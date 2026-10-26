# Feature #5 — Premium AI Motion State (2026-10-26)

Status: **source-only first integration slice**. Provider and GPU adapter source, source-media validation, worker/injected interfaces and offline tests are on `feat/feature5-premium-ai-motion`. This is NOT a working hosted service, real Hunyuan inference, customer preview or paid GPU. No model weights downloaded. No Azure or Supabase changed.

Coordinator-owned `main` and draft Part3 integration PR #125 must be preserved. The existing Part3 Wan provider, credits reservation proposal, encrypted/private import and FFmpeg composition are not duplicated by Feature5. Feature5 adds a disabled Hunyuan candidate with its own private worker contract, pending integration to Part3's ledger and ownership gates.

Delivery and review boundary: Feature5 may add its provider/worker source and own tests; coordinator must approve all shared API/DB/frontend/queue changes and copy status into the main PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG at merge. Do not edit shared files from this feature branch.

## 2026-10-26 continuation (source-only)
- Exact pre-continuation Feature5 SHA `57f83743` succeeded in all four standard checks, twice (Actions #40289071677 and #40289078080). Later hardening commits require independent, exact-head CI verification.
- Fixed genuine upstream CLI mismatch: Tencent `generate.py` uses *presence* of `--image_path` to select I2V, so T2V now omits it completely. Added 121-frame/24-fps 5-second target, disabled rewrite and upscaling, and blocked external model downloads. Command tests use mocks, not real GPU output.
- Added decoded-image checks (including limits), timeout subprocess termination, CUDA BF16+minimum-VRAM preflight, fail-closed NaN/Infinity quota checks, exact private output path/lease receipt, post-upload UNKNOWN reconciliation, and private scratch cleanup.
- No real inferences, cloud billing, private media uploads, deployed database tables, or operator authorization occurred.

## 2026-10-26 continuation checkpoint — after PR #323 integration review
- Verified exact branch `51201dbf93d7e94d2b2889310228f129ab6dcb3c` had two independent **4/4 PASS** GitHub Actions runs: #40293931880 / #40293926883. Main subsequently advanced independently; branch remains unmerged draft.
- After that checkpoint strengthened cross-feature clip handoff to require an independently loaded `VisualReview` with same shop, job, clip asset, exact bytes SHA-256, all anatomy/garment/temporal/branding checklist passes, actual reviewer write role and AI-disclosure approval. Tests use synthetic review records; this does NOT establish real quality.
- Billable logical request key now includes approved prompt SHA-256 and seed, not just day/source. Changing creative content cannot accidentally return the previous reserved motion clip. This is a proposed Feature5-only internal contract change, coordinator must version/accept it.
- Added Tencent Community License territory/notice/AUP/MAU policy, which blocks runner launch by default if reviewed activation context is missing. Test policy is simulated; it does NOT constitute Tencent consent or attorney approval.
- Real-gpu harness additionally requires actual operator reviewed deployment/publication regions and provider legal name. No GPU, weights or Azure credentials attached to this session; real Hunyuan outputs and fashion QA remain UNVERIFIED.

## 2026-10-26 additional gated cost and usage implementation
- Added `MotionSpendGuard` with verified Azure A100+CPU+RAM per-second rates, bounded maximum billable wall time and explicit ancillary allowance. Worker refuses all real or mocked enabled invocation without the injected guard, a bounded runner timeout and a sufficient existing reservation. Independent mocked tests cover underfunded credits, missing guard and timeout overrun.
- Measured per-attempt *model subprocess* elapsed time and Azure-rate *estimate* are added to the private media receipt, subject to the existing coordinator's authoritative usage ledger reconciliation. They are **NOT Azure invoice measurements**, and do not include all container warm-up/cold-load time unless measured separately. Exceeded runtime or ambiguous recording requires `UNKNOWN`; never silently retry/refund.
- No cloud account, model weights, or licensed real GPU currently accessible; no actual Hunyuan inference or visual garment QA was performed.
