# Feature #5 — Public stock photo/video technical QA (GPU OFF; 2026-10-28)

## Approved *research candidates* (not automatically licensed ads)
- Video: https://www.pexels.com/video/fashionable-woman-walking-in-urban-summer-setting-30706004/ (Gaidar Iskakov; page advertises 9 s, 1080x1920, 30 fps, 2025-02-13, free stock).
- Photo: https://www.pexels.com/photo/photo-of-a-woman-wearing-a-traditional-red-kurti-20702674/ (Muneeb Malhotra; page advertises red kurti portrait, 4000x6000, free stock).
- Terms: https://www.pexels.com/license/ and https://help.pexels.com/hc/en-us/articles/360042295214-Can-I-use-the-photos-and-videos-for-a-commercial-project
- Confirm individual page/license/creator again at time of download. Photograph and video feature **different people and different clothes**. Their pairing is deliberately a **negative garment-fidelity case** and must never be presented as a single tenant-owned model/source or legitimate I2V model result.
- Pexels permits many commercial uses but does NOT give permission to imply an identifiable individual endorses a merchant, brand or unrelated item. Independent model/likeness consent, garment ownership and retailer commercial rights are NOT established by these stock pages. Never publish as a customer endorsement or claim a Pexels model is the retailer's model.
- None of these stock files are committed, hosted, or automatically fetched by CI. Container internet restrictions prevent downloading/inspecting their actual bytes in this session. Thus **real public-media byte/probe evidence is NOT achieved here**.

## Reproducible no-cloud technical check after manual legitimate download

Obtain the individually downloaded licensed video MP4 and photo JPEG through the origin's normal permitted download method into a private local temporary directory (avoid automated scraping or hosted tenant storage). Use:

python -c "from feature5_motion.stock_media_review import inspect_downloaded_stock_pair; import json; print(json.dumps(inspect_downloaded_stock_pair(local_video='PATH_TO_VIDEO.mp4',local_photo='PATH_TO_PHOTO.jpg'),indent=2))"

This uses local ffprobe/Pillow only. It validates basic media bytes, portrait profile and content hashes, and creates PENDING review metadata; it does not certify motion quality, human identity, rights, garment match or Wan model origin. Actual motion/garment comparison requires independent frame-by-frame human review of a tenant-approved matched source and **real** model inference, impossible from mismatched free stock.

## Hosted tenant security (read-only verified / negative cases blocked)

Connected DEV Supabase project jeearzffnjbvghwjjjrf was inspected read-only. Relevant public render_jobs, media_assets, shop_usage_reservations, usage_events, shop_memberships, job_outbox and Feature3 tables have RLS on; policies restrict render_jobs/media_assets reads to members, usage/reservations to OWNER; job_outbox has no user policy. Current hosted render_jobs and shop_usage_reservations contained 0 rows at check time. These observations neither prove JWT signatures nor a Feature5 paid lease/real two-tenant denial. NO hosted tenant-specific test accounts, JWTs or real coordinator Part3 claim were injected/created.

Coordinator MUST use authorized signed DEV JWTs from two explicit test shops and an OWNER/VIEWER plus expired/revoked cases; verify forbidden cross-shop private uploads/reads, denied stale lease and duplicate submission CAS, settled usage idempotency, exact SHA output and receipt/reviewer persistence, and no billed request on failed authorization. Do not make new schema/migrations, arbitrary hosted data, or static API claims in this branch. Repo shared docs, migrations and workflow files remain coordinator owned.

## Exact existing Part3/F3/F4 handoff

- Existing DEV render_jobs has shop_id, render_claim_token, render_lease_until, attempts, status and output_asset_id; shop_usage_reservations has shop_id, operation, job_id; job_outbox has job_id, lease_token, lease_until, state; media_assets has shop_id/storage_bucket/object_path/license columns; these have NO Feature5-specific durable intent or signed receipt columns. The coordinator must reconcile Part3's *own* draft provider schema/lease transactions before adding a unique paid SUBMISSION_INTENT CAS and immutable tenant-private receipt. Do not invent a live schema or separate wallet.
- Feature3 current rights must revalidate original bytes/current media approval and returned prepared reference for every worker attempt. Feature4 owns editorial / 1080x1920 compositor and independent human-review release gate. Feature5 is source-only until coordinator applies and tests these connections.
- A100 remains OFF. No production, WineShopPOS, paid provider, Pexels file copy or private retail media mutation.


## 2026-10-28 — Coordinated eight-task security and public-media QA continuation

Supplementary 2026-10-28 read-only DEV Supabase security advisors: 9 INFO enabled-RLS-no-policy findings (including internal outbox and private objects; may be intentional deny-by-default) and 16 WARN authenticated-executable SECURITY DEFINER functions (not necessarily exploitable). Coordinator must inspect function bodies/EXECUTE grants and effective caller scope before altering anything; no blanket privilege revocation from Feature5. Hosted signed test accounts, cross-shop JWT requests, claim CAS, actual paid job and immutable receipt remain untested. Local media analyzer accepts downloaded original Pexels clip/photo only when bytes are manually supplied, reports metadata/hash and always forbids customer-release. Licensing and model endorsement consent must be independently recorded. The exact latest source prior to this documentation commit is d747b6b9d622baba9198f80dcf81a9a2f14235f0; run final four GitHub CI jobs again on the documentation commit before claiming current-head success. Earlier independent 858e5e598d6348fb2849c7497550d109d7660a7f run #40747182176 was 4/4 SUCCESS. A100 and paid API use remain OFF; no actual Pexels bytes, Wan inference or WineShopPOS change.


## 2026-10-28 — Actual hosted RLS negative read-only session
Executed in connected DEV Supabase with BEGIN READ ONLY / ROLLBACK, SET LOCAL ROLE authenticated, and a *synthetic nonexistent UUID* in request.jwt.claims; actual counts returned **0** for shops, media_assets, render_jobs, shop_usage_reservations, usage_events and shop_memberships. Separate anonymous SET LOCAL ROLE anon query was denied with PostgreSQL 42501 permission denied for table shops (no broad anon SELECT GRANT). This is real hosted **role/policy denial evidence** but is **NOT a signed real-user JWT, real two-shop test, private Storage URL test, or Part3 paid fencing/settlement test**. No rows were created/modified, no signed JWT or secrets viewed. Coordinator still must execute supported signed DEV two-tenant workflow and review definer-function warnings before live activation.


## 2026-10-28 — Stock media decoded-frame screening continuation

Local offline stock check now decodes actual FFmpeg frames and reports movement/anti-freeze evidence only. Probe is source-only, not commercial-rights endorsement. Manual Pexels download and original rights documentation still outstanding. Run latest CI before source completion claim.


## 2026-10-28 — Image-generation A100-free source qualification

Additional GPU-OFF source image handoff: **actual test-only local PNG** is generated by CPU Pillow after an approved F3 grant and active job-fence checks, with explicit branding NO FLUX/WAN, NOT FOR AD. It cannot be returned as commercially reviewed or truly generated clothing. Real licensed source media still needs bytes + separate human review, and feature3 FLUX model needs appropriately configured GPU/API for genuine photorealistic image generation; A100 is not required for 4B in general.
