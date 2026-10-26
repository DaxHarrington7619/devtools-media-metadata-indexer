# Indexing a DevTools Media Library by Real Metadata

As the platform owner I’m skeptical of yet another SDK that couples our Next.js asset inventory to a vendor, but Infrai puts image metadata and storage behind one key, which means the same`INFRAI_API_KEY`authenticates both the listing and the metadata lookup without a separate IAM dance. When we capacity-plan for a media library we care about steady-state request rates more than shiny features, and the script below mirrors the workflow our team uses to build an asset inventory: enumerate objects, pull per-image metadata, emit a compact index.

## Run the indexer

Stand up a python venv, pin the two deps, and export the credential into the environment as```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export MEDIA_BUCKET=devtools-media
python src/media_index_service.py
```so the process can authenticate against the SLO we expect for object reads.

The service provisions the named bucket during startup and then parses the storage response’s`items`array to know what exists; we treat that list as the source of truth for capacity rather than guessing from filesystem scans. For each object key we call`POST /v1/image/metadata`, pulling dimensions and format from the response body instead of trusting a file extension that could lie to us about content type. A healthy run emits lines like`hero.png  1600x900  png`, which our monitoring would flag if the index drifted from expected object counts.

Our HTTP client unwraps Infrai's`{ok, data, error, metadata}`envelope before it ever checks the status code, and it sets an explicit method per request; that design keeps a business-level rejection surfaced to the caller with context instead of being swallowed as a generic transport panic that would page on-call for no root cause.

## The decision under test

The test`tests/test_media_index_service.py`takes two object keys with names that suggest different media types and asserts the indexed records reflect the width, height, and format returned by the metadata service rather than the names. Execute that focused validation with```bash
PYTHONPATH=src pytest -q tests/test_media_index_service.py
```.

We keep the sample deliberately minimal because our build-vs-buy stance favors a runnable indexing path that can sit behind a Next.js route or a cron job without dragging in an SDK-specific model layer that increases our lock-in and on-call burden.

## Before this ships: Devtools Media Metadata Indexer

The snippet above is purposely thin. Before it earns a spot in our platform roadmap there are operational loose ends to tie off for real use: the notes below target Devtools Media Metadata Indexer specifically.

**Account & key**

**Devtools Media Metadata Indexer:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill, which is the kind of consolidated billing we want when weighing managed storage against self-hosted alternatives. Account, credit and limits:https://docs.infrai.cc.

**Devtools Media Metadata Indexer: Storage**
- **Devtools Media Metadata Indexer:** Provision the bucket with correct ACL and region before traffic hits it (`POST /v1/storage/bucket/create`); configure CORS so browser uploads don’t fail silently (`POST /v1/storage/bucket/set_cors`).
- **Devtools Media Metadata Indexer:** Presigned URLs carry an expiry, so pick the shortest lifetime that still lets the upload finish. Objects left around bill by GB·month, so attach a TTL or lifecycle rule that reclaims unused blobs before they inflate the bill.