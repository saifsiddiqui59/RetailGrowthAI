# Feature #5 — Premium AI Motion State (2026-10-26)

Status: **source-only first integration slice**. Provider and GPU adapter source, source-media validation, worker/injected interfaces and offline tests are on `feat/feature5-premium-ai-motion`. This is NOT a working hosted service, real Hunyuan inference, customer preview or paid GPU. No model weights downloaded. No Azure or Supabase changed.

Coordinator-owned `main` and draft Part3 integration PR #125 must be preserved. The existing Part3 Wan provider, credits reservation proposal, encrypted/private import and FFmpeg composition are not duplicated by Feature5. Feature5 adds a disabled Hunyuan candidate with its own private worker contract, pending integration to Part3's ledger and ownership gates.

Delivery and review boundary: Feature5 may add its provider/worker source and own tests; coordinator must approve all shared API/DB/frontend/queue changes and copy status into the main PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG at merge. Do not edit shared files from this feature branch.

## 2026-10-26 continuation (source-only)
- Exact pre-continuation Feature5 SHA `57f83743` succeeded in all four standard checks, twice (Actions #40289071677 and #40289078080). Later hardening commits require independent, exact-head CI verification.
- Fixed genuine upstream CLI mismatch: Tencent `generate.py` uses *presence* of `--image_path` to select I2V, so T2V now omits it completely. Added 121-frame/24-fps 5-second target, disabled rewrite and upscaling, and blocked external model downloads. Command tests use mocks, not real GPU output.
- Added decoded-image checks (including limits), timeout subprocess termination, CUDA BF16+minimum-VRAM preflight, fail-closed NaN/Infinity quota checks, exact private output path/lease receipt, post-upload UNKNOWN reconciliation, and private scratch cleanup.
- No real inferences, cloud billing, private media uploads, deployed database tables, or operator authorization occurred.
