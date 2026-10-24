# Part 1 — fenced poster queue and Pillow worker (source only)

- Queue: **retail-poster-render**; worker-only UUID messages. Dedicated `poster_outbox` dispatch/ack CAS and `poster_jobs` token + attempt lease fencing. No Part 2/3 queue reused.
- Default-off `RETAIL_ENABLE_POSTER_RENDERING`; no Azure resources created or hosted settings changed. Deploy only after RetailGrowthAI-specific DEV migration approval and queue provisioning.
- `PosterAdmin` reads backend-only poster/job/campaign/member/media records and invokes claim/complete/fail/reconcile RPC. `poster_worker.process_poster` rechecks current AUTHOR/EDITOR membership, campaign and day ownership, frozen title and CTA, revision, storyboard-listed image, exact mime, same-shop storage, commercial licensing and evidence.
- Source/logo bytes are fetched only from the existing private Supabase bucket and staged in a disposable directory. The existing Pillow engine renders the real PNG. Output passes the existing [private PNG validator](PRIVATE_PNG_OUTPUT.md) and is uploaded with `x-upsert: false` to a lease-specific private path. SQL completion must recheck lease/rights and atomically register `media_assets`, mark job SUCCEEDED and poster draft READY. Stale worker output never becomes a user asset.
- Fail/retry records only opaque `POSTER_RENDER_FAILED`, with no token or image paths in logs.
- `tests/api/test_poster_worker.py` covers successful owned product render, revoked membership, rights revocation, stale campaign text, busy job, duplicate terminal status and failure dispatch handling.

**Still required:** signed-poster-download HTTP facade and frontend persisted save/render/download, explicit attachment of reviewed asset to the day, new migration rollout, actual hosted end-to-end test. Dedicated queue needs approved configuration before runtime enablement. Do not touch WineShopPOS, SMTP/Part 2/Part 3.
