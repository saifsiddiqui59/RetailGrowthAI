# Part 1 — immutable private PNG output boundary (source only)

## Implemented
- Worker-only `PrivatePosterMedia.upload_png(shop_id, poster_id, lease_token, output_file, format_name=...)` validates canonical tenant, draft and claim UUIDs.
- The full original PNG bytes are validated **before** any outbound request, then that exact immutable byte snapshot is uploaded. Both approved formats are enforced (1080×1080 and 1080×1350); Pillow verifies PNG structure and decodes pixels, with RGB-only output and 12-MiB bound.
- Output key: `{shop_id}/posters/{poster_id}/{claim_token}.png` inside the existing private `retailgrowth-media` bucket. A new lease gets a distinct key.
- Backend-only Supabase secret and `x-upsert: false` prevent browser writes or accidental replacement. 409 collision, invalid bytes, wrong dimensions, missing file and network failures fail closed.
- The new tests use an injected offline transport; they neither upload to cloud nor create publicly accessible media.

## Critical unfinished dependencies
1. **Do not call this as a public API yet.** Add database-persisted poster render jobs, atomic lease/attempt fencing, queue/outbox and bounded retry/poison handling before wiring a worker.
2. Before calling, worker must verify the current requester OWNER/EDITOR membership, campaign day, storyboard asset and logo licenses/rights, draft revision, and subscription. Stage source privately and run the existing `poster-engine/render.py` as bounded execution.
3. After an upload, a backend transaction must recheck the same live lease/token, membership, rights and revision before registering the generated media asset and marking the poster ready; stale outputs remain private/unreferenced pending audited orphan cleanup.
4. Signed downloads and updating `instagram.banner_asset_id` must require authenticated, fresh tenant checks and **explicit owner/editor selection**. Never auto-publish.
5. Apply any future new migrations and deploy the worker only under separately approved RetailGrowthAI DEV gates. Current `RETAIL_ENABLE_POSTER_DRAFTS` remains OFF on hosted Azure; do not touch WineShopPOS or Parts 2/3.

## Local and CI evidence
- Offline local validation: `python -m pytest tests/api/test_private_poster_media.py -q` — 13 cases passed against compatible imported stubs for existing backend dependencies; this is not a full integrated backend test.
- The GitHub four-job CI on the real integration repository is the authoritative integration test; record its exact conclusion and PR merge after verification. No external provider costs or live project changes.
