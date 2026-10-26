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
