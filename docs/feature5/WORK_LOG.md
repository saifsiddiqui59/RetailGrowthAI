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

## 2026-10-26 — Owner requested minimum cost; offline continuation
- Re-read live coordinator AGENTS/PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG/ARCHITECTURE/INTERFACES/PARALLEL_WORK/CI docs. Verified Feature5 PR #323 remains open/draft, Part3 PR #125 and Feature4 PR #322 separate; starting Feature5 head `77f0b8223f` had successful dual four-job CI.
- Fixed a genuine potential double-charge defect in source-only `MotionWorker`: exceptions or media validation failures after the model runner starts no longer create refundable `FAILED` jobs; they fence as `UNKNOWN` or require explicit reconciliation. Pre-GPU staging still safely fails; added four negative tests.
- Added zero-premium default `cost_routing` policy and seven offline tests: rights-approved stock/FFmpeg preference, no fake walking model, hard budget rejection, no implicit paid activation, corrupted cost input blocking, independently priced eligibility only. This policy is not yet hosted or connected to Feature4.
- Independently checked official Microsoft serverless GPU regions: Central India A100 **No**, T4 **Yes**; Tencent minimum 14 GiB VRAM and BF16 CUDA profile does not imply T4 suitability. No cross-border data movement or GPUs provisioned.
- No WineShopPOS/PROD, schema, other-feature branches, Azure/Supabase writes or charged inference. Exact final PR-head Actions logs must be inspected before reporting success.

## 2026-10-26 — User requested real Hunyuan sample
- Inspected Github main, open Feature5 #323, Part3 #125 and Feature4 #322; reread root instructions and Feature5 docs. Rechecked current CPU tool runtime (`torch 2.10.0+cpu`, CUDA false, no NVIDIA driver/weights). A ChatGPT-generated still was previously presented by mistake; explicitly ruled out counting it as Hunyuan.
- Inspected official Tencent Hunyuan 1.5 weights/model docs and public HF `multimodalart/Hunyuan-Video-1-5` ZeroGPU I2V Space. Attempted one public browser demo; no sign-in/payment gate seen, but a local image is required and browser had no uploadable file. **No actual Hunyuan inference completed; no MP4 exists**.
- Added deterministic five-second festival fashion T2V demo spec with user-chosen theme and CPU tests. Hardened manual CUDA test to disallow accidental second T2V/I2V inference in same invocation and require a reviewed regional Azure retail rate snapshot and total USD cap before paid work. GPU provisioning, model weights, hosted DB and WineShopPOS unchanged.

## 2026-10-26 — Azure GPU request follow-up
- Acknowledged that no prior Azure GPU deployment was made. Inspected current project branch, separate draft PRs, root AGENTS and mandatory coordinator docs. Verified GitHub has DEV OIDC workflows and known RG-only credentials but this chat has no Azure control-plane action and local sandbox has no `az`/Docker/CUDA/weights.
- Started secure browser-profile Azure Portal authentication setup for user sign-in (user credential action still outstanding); did not see or request passwords, did not create any GPU resource.
- Reverified latest Microsoft region/quota and Tencent 1.5 CUDA/license docs. Implemented fail-closed read-only A100/DEV quota inventory helper + 8 negative tests; verified no deployment verbs are possible from inventory wrapper. Prepared one-shot GPU runbook/cost examples; no registry/model download/VM/GPU/storage bill incurred.
- Left shared root docs, coordinator-owned workflows, PROD, Supabase schema and WineShopPOS untouched. The main blocker is a signed-in Azure management session plus supported model weights/quota, not missing frontend imagery.

## 2026-10-26 — Azure connected and inspected in real portal
- Confirmed user's Microsoft portal profile signed in; first *actual* Azure Portal inventory verified Azure subscription 1 and tagged `rg-retailgrowth-dev` Central India, eight existing DEV resources, no A100 environment, no ACR, plus separate Sweden Central voice environment untouched. Second browser audit reached Subscriptions filter displaying 0/0 in its directory and could not inspect A100 quota. Quota/permissions remain **unconfirmed**, not proven denied. Logged exact evidence/recovery in `AZURE_SIGNEDIN_INVENTORY_20261026.md`.
- No Azure resources created, no quota request, no cloud GPU charges, no model weights, no real Hunyuan MP4; protected PROD, WineShopPOS, Supabase data and voice workloads. Need selected directory/usage quota visibility before safe one-shot GPU deployment.

## 2026-10-26 — User asked to verify A100 quota directly
- Executed two separate **authenticated read-only Azure Portal** checks from user's saved Microsoft profile. First followed existing dedicated `rg-retailgrowth-dev` to Azure subscription 1; direct subscription Usage + quotas redirected to Events without showing table or explicit access denial. Second used standalone Quotas service → Azure Container Apps → East US and searched NCA100/GPU names; UI returned **no data for filters**. A registration warning under Microsoft Fabric did not prove anything about Container Apps registration.
- **Result:** actual East US Container Apps A100 limit, usage and availability remain unverified; no invented numbers or assumption that quota is zero. Need subscription-scoped Azure Resource Manager/CLI read-only provider+quota inspection, possibly requiring coordinator-approved GitHub DEV OIDC workflow. No Azure writes or GPU spending, no WineShopPOS/PROD modifications.

## 2026-10-26 — Environment-first GPU quota blocker and real ARM attempt
- Verified latest Microsoft serverless GPU docs: East US A100 profile available in service catalog; must create workload-profiles env before environment Consumption NCA100 quota can be read/requested. Empty subscription quota rows were not meaningful.
- Used saved signed-in Azure Portal: standalone environment wizard unavailable; ephemeral no-storage Cloud Shell Bash did open but GUI couldn't focus xterm input, **no shell commands executed**. Next used direct Azure custom ARM template wizard, submitted exactly one proposed empty Consumption environment. Portal reported `CustomDeployment-20261026093554` succeeded, but DEV resource-list search did NOT find the environment. Follow-up audit reached RG resources but browser automation metered budget exhausted before ARM operations were opened. **Created-resource state remains UNKNOWN; no GPU or model generation started.**
- Implemented pinned Azure one-resource log-free/no-GPU ARM template, strict template + what-if validation, negative tests, and corrected source preflight to wait for owned East US empty environment before reading NCA100 quota. Isolated feature-owned paths only; coordinator to inspect ARM deployments via existing DEV OIDC, not retry until reconciled. Complete runbook at `ARM_CUSTOM_DEPLOYMENT_DISCREPANCY_20261026.md`.

## 2026-10-26 — User requested GitHub OIDC connection for direct Azure commands
- Verified `main` already contains read-only OIDC login/inventory workflows using `azure/login@v3`, GitHub environment `dev`, and short-lived id-token. Confirmed connected GitHub Actions API exposure here is read-only for workflow dispatch (no dispatch tool), so bare chat cannot execute arbitrary Azure commands even though GitHub runners can authenticate and run `az`.
- Added feature-owned **proposed** manually triggered, read-only GitHub OIDC ARM reconciliation/quota workflow `docs/feature5/proposed-workflows/azure-feature5-oidc-reconcile.yml` for coordinator review/install. Does NOT edit `.github/workflows/**`, merge main, deploy GPU or incur Azure costs. Replaces repeated TinyFish navigation for diagnosis after coordinator activation.

## 2026-10-26 — Real Azure OIDC environment rollout SUCCESS, GPU quota ZERO
- Coordinator PRs #367, #368, #369, #370 and #377 introduced the read-only OIDC reconciliation and one-time restricted ARM deployment with corrected logging omission and strict Azure what-if Ignore semantics. Actual main [run #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764) **SUCCEEDED**. Logs explicitly show `PASS: Azure what-if permits 1 Create and 8 known unchanged DEV resources`, then successful ARM creation/read-back for `rgai-f5-gpu-canary-eastus`, East US, default Consumption only, with no GPU workload profile/app/job, and quota `ManagedEnvironmentConsumptionNCA100Gpus limit=0 used=0`.
- Reviewed current Microsoft quota docs: now that the environment exists, request one managed-environment NCA100 GPU from its own Quota pane; Azure may process or route for review. Quota increase not submitted. No model weights installed, no Hunyuan inference, no MP4, no Azure GPU charges started. Preserve isolated RetailGrowthAI DEV and do not touch PROD/WineShopPOS/voice projects.

## 2026-10-26 — Checked alternate Azure GPU VM quota without TinyFish
- Coordinator PR #388 added and merged a main-only OIDC read-only regional VM quota/SKU inventory workflow, tested 4/4, and actual run #40355181214 passed with no Azure mutations. Central India and East US regional VM quota each 10 used 0; NVIDIA A10 SKUs listed without location restriction, A100 VM SKUs restricted. Checked Microsoft NVadsA10v5 official RAM/vCPU table and Tencent 1.5 >=14GB GPU memory requirement; viable full A10 24GB uses 36vCPU, beyond existing cap. Thus no suitable Azure VM quota path without additional approval. Existing East US Consumption env A100 quota 0 unchanged. No CUDA inference/real MP4 or GPU bill; next external dependency is a serverless A100 quota increase to 1, which has NOT been submitted.

- 2026-10-26: Read existing Feature5 PR #323 and coordinator merged Azure work through #388; confirmed full OIDC East US empty environment and NCA100 limit=0/used=0 from #40347841764, plus VM inventory limitations from #40355181214. Verified Microsoft 2026 managed-environment quota request path and lack of documented CLI/REST submission route, Tencent 1.5 14GB/offload + 50-step T2V, and official current Runpod/Vast advertised rental rates. Created `docs/feature5/QUOTA_AND_EXTERNAL_GPU_OPTIONS_20261026.md`, `feature5_motion/external_gpu_budget.py`, `tests/ai/test_feature5_external_gpu_budget.py` with fail-closed quote/price/lease screening; development-only, no cloud or GPU calls. CI evidence is to be checked independently after push. **No quota request, genuine Tencent MP4, model weights, external vendor reservation, Azure resource write, invoice or retailer/private media.** Shared root docs, workflows, Part3/Feature4, WineShopPOS, PROD unchanged.
