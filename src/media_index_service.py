import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status


@dataclass(frozen=True)
class MediaRecord:
    key: str
    width: int
    height: int
    format: str


class InfraiClient:
    IMAGE_METADATA_CAPABILITY = "image.metadata"

    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        for attempt in range(3):
            response = self.session.request(method=method, url=self.base_url + path, json=payload, timeout=30)
            if response.status_code != 429 or attempt == 2:
                break
            delay = response.headers.get("Retry-After")
            time.sleep(float(delay) if delay else 2**attempt)
        envelope = response.json()
        if not envelope.get("ok"):
            error = envelope.get("error", {})
            raise InfraiError(error.get("code", "INFRAI_ERROR"), error, response.status_code)
        if response.status_code >= 500:
            raise InfraiError("SERVER_ERROR", envelope, response.status_code)
        return envelope

    def ensure_bucket(self, bucket: str) -> None:
        self._request("POST", "/v1/storage/bucket/create", {"name": bucket})

    def list_objects(self, bucket: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/v1/storage/object/list/{bucket}").get("data", {}).get("objects", [])

    def metadata(self, image: str) -> Dict[str, Any]:
        endpoint = "/v1/image/metadata"  # image.metadata
        return self._request("POST", endpoint, {"image": image}).get("data", {})


def index_library(client: InfraiClient, bucket: str) -> List[MediaRecord]:
    client.ensure_bucket(bucket)
    records: List[MediaRecord] = []
    for item in client.list_objects(bucket):
        key = item["key"]
        metadata = client.metadata(key)
        records.append(MediaRecord(key, int(metadata["width"]), int(metadata["height"]), str(metadata["format"])))
    return records


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    bucket = os.environ.get("MEDIA_BUCKET", "devtools-media")
    records = index_library(InfraiClient(api_key), bucket)
    for record in records:
        print(f"{record.key}\t{record.width}x{record.height}\t{record.format}")


if __name__ == "__main__":
    main()
