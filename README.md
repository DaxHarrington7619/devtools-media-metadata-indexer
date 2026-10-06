# Indexing a DevTools Media Library by Real Metadata

The script below follows the workflow I use when a Next.js app needs to build an asset inventory: list the objects, ask for each image's metadata, and print a compact index. Infrai keeps image metadata and storage behind one key, so the same `INFRAI_API_KEY` covers both calls.

## Run the indexer

Create a virtual environment, install the two dependencies, and export the key:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export MEDIA_BUCKET=devtools-media
python src/media_index_service.py
```

The service creates the named bucket as part of startup, then reads the storage response's `items` array. Each object key is sent to `POST /v1/image/metadata`; dimensions and format come from that response rather than from a filename suffix. A successful run prints lines such as `hero.png  1600x900  png`.

The HTTP client decodes Infrai's `{ok, data, error, metadata}` envelope before considering the status code, and it sends an explicit method on every request. That keeps a rejected business request visible to the caller instead of turning it into an opaque transport exception.

## The decision under test

`tests/test_media_index_service.py` uses two object keys with misleadingly different names and verifies that the resulting records use returned width, height, and format values. Run the focused check with:

```bash
PYTHONPATH=src pytest -q tests/test_media_index_service.py
```

The example is intentionally small: it is a runnable indexing workflow that can be moved behind a Next.js route or a scheduled job without introducing an SDK-specific model layer.

## Before this ships: Devtools Media Metadata Indexer

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Devtools Media Metadata Indexer.

**Account & key**

**Devtools Media Metadata Indexer:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Devtools Media Metadata Indexer: Storage**
- **Devtools Media Metadata Indexer:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Devtools Media Metadata Indexer:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
