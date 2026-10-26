# Feature #5 development log

## 2026-10-26 — Additive source implementation
- Read mandatory root docs; verified current main and Part3 integration branch/source/PR #125; noted Part3's Wan, private importer, staged SQL, queue code and mock CI.
- Verified Tencent HunyuanVideo-1.5 public official code/requirements and community license; Diffusers has documented pipeline; Azure lists Central India serverless T4 but not A100.
- Created isolated Feature5 branch from exact verified main SHA `140a9f86170132d7c482a183b843788aa09b3b5a`.
- Added contract, gated local CLI runner and separate injected worker; added offline tests and cost/rollout proposal.
- No real GPU test, paid API call, subscription adjustment, Azure resource, migration, production edit or WineShopPOS edit.
- PR #323 is OPEN/DRAFT for coordinator review. Exact post-fix head `57f83743b1c1fad158c5a3f22fc731c83b350862` passed the four mandatory jobs in [Actions run #40289071677](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40289071677): Python/uv (450 tests, 41 subtests at previous diagnostic pass; exact latest job success), FFmpeg codec/render, frontend build/Playwright, and disposable Supabase RLS/security. This proves offline regression only, **not GPU inference, hosted paid activation, or video visual QA**.
\n- Strengthened image-byte signature checks (PNG/JPEG/WEBP) and DB claim token canonicalization; ambiguous post-upload DB completion remains UNKNOWN for reconciliation, not a duplicate bill or automatic refund.\n
## 2026-10-26 continued work
- Inspected Actions #40289071677 and #40289078080: exact SHA `57f83743`, each **4/4 PASS** (Python, frontend, FFmpeg and Supabase isolation). Subsequent intermediate pushes were cancelled by GitHub CI concurrency; inspect the final PR-head run.
- Inspected real Tencent `generate.py` CLI docs; corrected `--image_path none` bug that would make T2V wrongly select I2V. Added isolated CLI tests with simulated subprocess, no actual generation.
- Strengthened source image size/decode, subprocess output/timeout, offline-only model flags, BF16 CUDA/VRAM preflight, prevention of NaN/Infinity budget bypass, private scratch cleanup, exact private blob lease receipt, and UNKNOWN on ambiguous uploads.
- Fixed a mock-fixture timing defect detected by CI (fixture created output before start). Did not disable tests or modify workflow.
- Code and docs remain isolated to Feature5-owned folders/tests. Production and paid GPUs are untouched.

- Added separate MANUAL-ONLY real local GPU acceptance harness gated on operator cost/license approval and existing on-disk official weights. No tests executed against GPU or billable APIs.

## 2026-10-26 follow-up — owner requested continuation
- Rechecked branch/main/PR #323 and verified prior exact-head 4/4 CI passes at `51201dbf9` (#40293931880, #40293926883); no changes to Part3/Feature4/PROD.
- Read updated mandatory canonical project docs and coordinator ownership rules.
- Verified Tencent official model CLI and November 2025 Community License terms; source confirms `--image_path none` is accepted/normalized to missing (so omitting optional flag is a stylistic contract hardening, not proof that earlier command would have failed). Kept 121-frame documented model profile.
- Implemented mandatory VisualReview-bound Feature4 clip handoff and negative tests (review absent, wrong asset/job hash/role, rejected garment).
- Versioned deterministic idempotency key to include source image, approved prompt digest and seed.
- Implemented reviewed territory/hosted-commercial license policy and negative tests for EU/UK/Korea, missing notices and >100m release-date MAU threshold. Real GPU test harness requires additional operator fields.
- No actual real GPU inference, azure deployment, licensed sample outputs or human garment acceptance was possible. Next coordinator integration and real GPU blockers documented without pretending all assigned tasks completed.

## 2026-10-26 follow-up — GPU budget ceiling and measured usage
- Added `MotionSpendGuard` in `feature5_motion/azure_pricing.py`, integrated into `MotionWorker` before durable claim, and required existing reservation >= total worst-case billable approved CPU/RAM/A100 time and ancillary allowance. Added offline negative tests for missing quote/underfunded reservation/runner timeout.
- Added monotonic subprocess elapsed-time and Azure-rate estimate to private output metadata for later existing ledger reconciliation. Enforced `UNKNOWN` on over-budget runtime; fixed an edge case where failure persisting UNKNOWN could be incorrectly downgraded to FAILED. No GPU was actually run.

## 2026-10-26 work continuation: runtime source integrity and offline QA
- Re-read latest canonical AGENTS and coordinator project docs, current main, PR #323, PR #125 Part3 and PR #322 Feature4; preserved their branches.
- Fetched official Tencent upstream `generate.py` at commit `60783e704160023913bee78f0b47036d393d4dfa`; added exact Git-blob integrity gate and fake/tampered/symlinked script tests. Did not download model weights or start CUDA.
- Added true FFmpeg/libx264 5s H264/24FPS media validation test with real 30FPS and 4s rejection fixtures, rather than relying only on `ffprobe` mocks. Added private six-frame review contact sheet and clip SHA256 manifest; real garment visual assessment remains unperformed.
- No Part3/Feature4/shared-main edits, Azure/Supabase/PROD changes, GPU spend or WineShopPOS modification.

## 2026-10-26 live DEV metadata verification
- Queried read-only PostgreSQL information_schema/pg_constraint of dedicated RetailGrowthAI DEV (existing shop/user data not read or modified): `shop_subscriptions` has no premium budget, `shop_usage_reservations` accepts campaign/render only with no units, `job_outbox` accepts planning/render only, `premium_video_jobs` does not exist. Recorded exact coordinator-owned single-ledger reconciliation proposal and negative test plan in `PART3_DEV_SCHEMA_RECONCILIATION_20261026.md`; no schema changes, no live calls to a GPU.

## 2026-10-26 — Remaining model authenticity and quality evidence work
- Verified GitHub feature branch/PR #323 and separate Part3 #125/Feature4 #322 still open; read latest AGENTS and canonical project docs; stayed within Feature5-owned paths. Previous PR head `45fc91ed1` had two complete 4/4 CI runs (#40307095552, #40307083961).
- Implemented deterministic full code+weight SHA256 manifest preflight, operator-only candidate generator, trusted digest passed separately to `HunyuanLocalRunner`, and negative CPU-only tests against synthetic code/shard fixtures. No real weights downloaded or licensed; official source commit still independently pinned by existing code.
- Reworked manual GPU harness to preserve verified actual MP4/reference imagery + contact-sheet frame hashes in a private operator-owned evidence location instead of destroying temporary test media. Added CPU-real FFmpeg acceptance-export fixture tests; no actual Hunyuan generation or real garment visual acceptance was performed.
- Kept feature flags OFF, no real model/GPU/queue/cloud/Supabase writes, no new ledger, no PROD or WineShopPOS changes. Final exact-head CI status must be inspected after docs commit.
