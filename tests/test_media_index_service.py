from media_index_service import InfraiClient, index_library


class FakeClient(InfraiClient):
    def __init__(self):
        self.created = []

    def ensure_bucket(self, bucket):
        self.created.append(bucket)

    def list_objects(self, bucket):
        return [{"key": "hero.png"}, {"key": "icon.webp"}]

    def metadata(self, image):
        return {"hero.png": {"width": 1600, "height": 900, "format": "png"}, "icon.webp": {"width": 64, "height": 64, "format": "webp"}}[image]


def test_index_uses_metadata_for_dimensions_and_format():
    client = FakeClient()
    result = index_library(client, "devtools-media")
    assert client.created == ["devtools-media"]
    assert result[0].width == 1600
    assert result[1].format == "webp"
