# Feature #5 — Next tasks / gates

1. **Coordinator interface gate (P0):** map `MotionSpec`/AssetGrant to existing signed Feature3 media/Part3 source rights, existing subscription reservation, persisted lease claims, outbox, private Storage importer, without an independent schema or queue. Design review before any shared file change.
2. **Model exactness gate (P0):** pin upstream Tencent generate.py commit + downloaded weight/checksum and allowed inference mode/version. Current runner supports 480p T2V/I2V via official CLI shape but has never executed GPU inference. Validate output dimension, FPS, 5s actual generation and expected VRAM on a real licensed GPU.
3. **GPU cost and legal gate (P0):** review Tencent territory exclusions (EU, UK, South Korea), hosted-service notices/disclosure, 100m MAU clause, third-party rights, India data residency; confirm Azure Central India T4 quota and $/GPU-second. Obtain explicit paid approval before provisioning/inference.
4. **Media integration (P0):** verify existing claim attempt-token DB generation and replay fencing, input byte-signature/pixel/decompression checking via existing Feature3 importer, exact private output media path, DB-fenced registration, and media quality approval. Do not treat machine codec check as garment QA.
5. **Operational gates (P1):** secure job image staging cleanup, GPU subprocess/child-group timeout, workload profile idle scale-zero, GPU OOM telemetry and retry policy, amount-spent reconciliation and non-billable fallback to Feature4 static animations.
6. **Cross-feature acceptance (P1):** Coordinator Feature4 assembles a branded fashion Reel; Feature6 ensures human approval before publishing.
7. **CI:** inspect exact PR-head GitHub Actions after push; no mock implies real GPU output.

## Updated 2026-10-26 progress
- **Completed offline:** official CLI T2V omission of `--image_path`; I2V source flag, bounded model args, preflight image decode, timeout and CUDA gate, immutable lease-scoped private output receipt, nonfinite quota rejection and post-upload unknown-state handling. Corresponding automated mocked tests added to the standard Python CI.
- **Still blocked:** verified licensed GPU/device and actual Hunyuan output, pinned weights+runtime digest, real 480p/frame aspect/FPS verification, actual garment quality, managed/private media adapters, transactional reservation and claim RPC wiring, Azure service and real preview.
- **Hardware:** Central India T4 has native BF16 compatibility risk (CUDA compute capability 7.5); default Hunyuan BF16 runner rejects unsuitable GPU. Coordinator should review whether a consented A100 region is permissible or keep dormant Wan vendor choice. No cross-region transfer without approval.

## Real GPU acceptance harness prepared, not executed
- Optional `tests/gpu/test_feature5_local_acceptance.py` provides real T2V and I2V paths only after three explicit environment approvals (real test, GPU spend, and reviewed license) plus pinned local checkout and weights. The separate I2V test requires a rights-approved source image.
- The standard GitHub CI does not discover or run `tests/gpu/`; local manual execution must never be described as a successful test until real GPU output, ffprobe, side-by-side garment review and captured measured costs exist.

## 2026-10-26 integration gates after owner approval
1. **Coordinator schema + service adapter:** Part3 PR #125 remains draft. Its `PROPOSED_20261023180000_premium_video_reservations.sql` explicitly restricts `model_id` to two Wan 2.7 names and resolution to 720P/1080P. Feature5 `hunyuanvideo-1.5-480p` cannot use that database safely until coordinator reviews a compatible, versioned extension to EXISTING premium jobs/quotas/leases/rights/ledger/outbox. Our `Part3MotionStoreAdapter` is injected interface code and is NOT connected to a real DB RPC. Do NOT create another ledger, apply schema or claim hosted integration.
2. **Feature4 handoff:** PR #322 `creative_reel_v1` expects genuine approved `source_feature=feature5` video in a backend-signed/staged tenant manifest. Feature5 now provides matching shape, strict rights metadata and a separate immutable human review gate. Coordinator mounts only after merging relevant PR and verifying real signed-in E2E; we did not touch Feature4 branch.
3. **Real inference:** No Azure/NVIDIA GPU and no licensed model weights in current tool environment. Real pilot needs an Azure connection with exact subscription/project, quota and region, reviewed model commit/weights, licensed approved test image and a cost-capped one-shot GPU job. Existing Central India T4 does not satisfy the default BF16 profile; A100 documented in East US but data-region transfer needs owner consent. Do not silently route Indian customer private media to US.
4. **Visual signoff:** Before promotion, reviewer compares REAL output side-by-side with original clothing; check face/body, garment color/pattern/sleeves, background continuity, camera, motion, temporal artifacts, honest product representation and mandatory disclosure; bind to exact SHA256 and published-asset version. Synthetic/mocked test checklists never count.
5. **License:** Review and document Tencent territory limitations (EU/UK/South Korea), hosted use disclosure of actual provider, Tencent no-endorsement, terms/AUP notice, 100m MAU release-date exception, rights. Operator-approved policy booleans are defense in depth, NOT legal clearance or verified geo-blocking.
6. **CI:** inspect final PR HEAD four required jobs and record SHA/result. Do not self-merge; main integration belongs to coordinator. Preserve WineShopPOS and production isolation.

## Follow-up: quote/actual billing and launch order
- Implemented SOURCE ONLY: `MotionSpendGuard` bound to approved full-job timeout, Azure GPU+vCPU+RAM price and ancillary allowance; tests run on mocked GPU. A paid runtime must have an existing DB reservation >= quoted worst-case cost, with one charge ledger reconciliation of observed subprocess time and actual cloud bill. No provider charge was incurred.
- Coordinator must first merge/reconcile Part3 schema and private claim/outbox, Feature4 canonical asset contract and reviewed VisualReview audit persistence. Feature5's code is **not yet connected to those live resources**. Owner consent does not supply cloud credentials, quota, consent for transferring retailer images to East US, licensed weights or a formal legal agreement.
- Real inference remains a separate acceptance gate: one actual A100 call in authorized region on licensed model/staged noncustomer media, record true elapsed and Azure charges, ffprobe, inspect sampled frames side by side, then attempt authorized clothing I2V. Only after that may Feature5 be described as operational.

## 2026-10-26 follow-up gates after pinned-source implementation
- **DONE in owned Feature5 source:** pin exact `generate.py` Git blob from audited Tencent upstream revision and reject tampering before GPU, CPU-real FFmpeg 5-second MP4 validator tests, bounded local human-review frame/contact-sheet exporter with clip+frame digests. CI must be inspected on final HEAD; test artifacts are synthetic, not AI-generated.
- **P0 real model authenticity remains:** obtain explicitly licensed *actual* `HunyuanVideo-1.5` weights and record their immutable release revision/complete shard SHA-256 checksums, runtime dependencies, and GPU execution environment; no model weights were downloaded or attested here.
- **P0 real human visual acceptance remains:** make a real 5s I2V clothing/retailer demonstration on an approved GPU and reviewed geography, generate review evidence, then require human approval of motion, faces, exact outfit colors/prints, temporal smoothness and disclosure before Feature4 assembly.
- **P0 coordinator remains:** Part3's current Wan-only reservations SQL/queue/ledger needs additive provider-aware versioning and real service-role adapters; Feature4's `creative_reel_v1` must be integrated by coordinator. Never merge or deploy behind another team.

## Actual hosted DEV evidence and coordinator acceptance (2026-10-26)
- DONE: read-only catalog verification of RetailGrowthAI DEV confirms **no** `premium_video_jobs`, no premium shop allowance/budget columns, and only `campaign|render` usage / `planning|render` outbox kinds. Feature5 is **not production/billing integrated**, regardless of green offline CI.
- Coordinator must first reconcile Part3's Wan-only draft and Feature5 480p/A100 total wall-time tariff in a **single existing ledger/outbox**; use `PART3_DEV_SCHEMA_RECONCILIATION_20261026.md` for additive contract and DB-negative acceptance plan. Do not apply migrations independently in Feature5 branch.

## 2026-10-26 — Next activation prerequisites after artifact-lock implementation
1. **Model release**: Obtain complete legitimate model weights from their licensed source, verify upstream model revision, manufacturer/third-party notices, legal region/commercial eligibility and immutable per-shard SHA256. Stage a **clean, non-symlinked** runtime/weight snapshot without `.git` or transient download cache. Create candidate lock with `python -m feature5_motion.seal_artifacts`, independently review manifest and configure *its* SHA256 in operator-side deployment settings. A self-declared manifest is NOT approval.
2. **GPU preflight**: On approved BF16-capable GPU and permitted region, run **one cost-capped manual GPU** T2V first, then I2V with approved noncustomer clothing reference, using expected lock SHA, explicit Tencent context, one licensed CUDA environment and isolated private evidence output. Do not deploy an always-on GPU or post media automatically.
3. **Visual acceptance**: Inspect persisted `clip.mp4`, comparison `reference.png` (I2V), `review/contact-sheet.png`, six frames and hashes; obtain actual tenant/rights/QA reviewer signoff with exact media hash before passing to Feature4. Runtime source tests/CPU mp4 fixtures cannot certify garment fidelity or a model's provenance.
4. **Hosted billing/composition**: Coordinator must implement and test single Part3 ledger/outbox schema for Hunyuan 480p and Wan, and reconcile Feature4 creative_reel_v1; read-only DEV inventory confirms premium tables/units not applied. No Feature5-owned production/DEV schema change permitted.

## 2026-10-26 — Next tasks after $0-first route and paid-failure fencing
1. **Coordinator integration gate (unchanged P0):** Part3 must implement existing ledger/reservation/outbox support for Hunyuan 5s/480p with service-owned worst-case bill cap and UNKNOWN-safe reconciliation. This source-only worker's state transitions require an atomic persisted SQL adapter before any live test.
2. **No-cost delivery (now designed):** coordinator may wire `plan_lowest_cost_delivery` to existing approved-media FFmpeg route; route is source-only and does not itself render/publish. If actual creative intent requires model motion, **defer** until an approved GPU provider is affordable instead of falsifying a real walking video.
3. **Actual GPU acceptance:** only with independently verified licensed weights, full artifact SHA lock, reviewed Tencent license/territories, budget approval, region/data consent, cloud quota, one-shot capped A100 GPU and human visual review. Do not use T4 merely because it appears as available Central India.
4. **Cost reconciliation:** if any GPU run times out/fails/produces invalid MP4, worker marks UNKNOWN, requiring existing ledger+Azure bill reconciliation before deciding retry/refund. Actual cloud invoices/FFmpeg v. model quality remain unverified.

## 2026-10-26 — User demands actual model video (NOT another ChatGPT image)
- **P0 blocked by model execution access:** obtain supported BF16 NVIDIA GPU and licensed pinned Tencent 1.5 weights (complete SHA256 manifest); choose an authorized India-residency solution or separately approve a non-India DEV synthetic-only GPU region. Current chat runtime has **no CUDA**, and the separate public HF ZeroGPU demo cannot be treated as proof of our runner.
- **One exact chosen creative:** `feature5_motion/demo_fashion.py`: adult fashion model, red/gold kurti, walking in boutique, 5s/480p/24fps/9:16. Launch `RETAIL_FEATURE5_ACCEPTANCE_MODE=text` only after cost snapshot/approved cap, Tencent license, official runtime pinned+weights, zero public personal imagery and recording path in 0700 directory. Do NOT schedule image mode in the same paid pilot.
- **Proof, not promise:** after real GPU execution, save actual `clip.mp4`, `acceptance-pending.json`, six PNG frames and contact sheet, check ffprobe, clip SHA256 and true Azure billed seconds. Show the real MP4 to user labeled *actual Hunyuan*, never show previous ChatGPT still/FFmpeg animation as generated model motion.
- **External free model eval:** if user wishes to test Tencent weights independently before connecting GPU, visit `https://huggingface.co/spaces/multimodalart/Hunyuan-Video-1-5` and manually upload an authorized local still + describe motion. This is external, optional, with its own terms/privacy; not a RetailGrowthAI SaaS hosted sample.

## 2026-10-26 — Actual GPU deployment next action (blocked on sign-in)
1. **User action:** save authenticated Azure Portal browser session from this conversation's secure setup link. No passwords in chat. Or provision a reviewed coordinator-owned Azure management/CI workflow capable of the same read-only checks. Existing GitHub OIDC identity in `dev` can authenticate but is not an executable Azure management tool here.
2. **Read-only inspection:** verify exact DEV subscription, tags/role in `rg-retailgrowth-dev`, `eastus` A100 workload profile/available quota. `python -m feature5_motion.azure_gpu_readonly_cli` is now implemented. Current cloud GPU quota and image/weights are **unknown**, do not assume green.
3. **Verified manual deployment prerequisites:** licensed pinned real Tencent weight shards and container image, supported GPU quota, allowed East US synthetic-only deployment, exact agreed max USD, model CPU+RAM sizing and disposable storage. An Azure Cost Management budget alert is not a hard stop; require single manual execution, one replica, no automatic retries, bounded timeout and teardown.
4. **One real Hunyuan MP4 and audit**: genuine fashion T2V, verify model revision, H264 5-sec 480p/24fps, review frame sheet/sha256 and actual Azure charges; show video to user; later Part3/Feature4 integration remains separate. See `AZURE_GPU_CANARY_DEPLOYMENT_20261026.md`.

## 2026-10-26 — Actual Azure sign-in now available; quota screen currently blocked
1. **READ-ONLY portal fix:** user selects correct directory/subscription in Portal Settings → Directories + subscriptions, where existing `rg-retailgrowth-dev` is visible. In Azure subscription 1 → Usage + quotas (or Quotas) inspect **Container Apps East US Managed Environment Consumption NCA100 GPUs**. First portal inventory showed the subscription, second generic Subscriptions blade 0/0 after clearing filters, so actual quota is **UNKNOWN**. This is the immediate blocker, not lack of login.
2. **Do not infer quota from lack of managed environment**: no A100 environment exists yet, but its creation eligibility/limit was not checked. Do not request quota changes, create paid GPU or use voice-project environment as a workaround.
3. Once quota is verified, operator reviews actual approved region, Tencent license+official pinned weights, supported A100 Container Apps Job profile, image size/pull/CPU/RAM cost and **specific full USD maximum** for one fictional text-only sample. Only then create one ephemeral zero-retry job and capture a genuine MP4. See `AZURE_SIGNEDIN_INVENTORY_20261026.md`.

## 2026-10-26 — Quota blocker after full Azure browser inspection
- **DONE** signed-in portal resource-group/subscription inventory. **DONE** both Subscription → Usage + quotas and separate Azure Quotas → Container Apps → East US attempt. Both failed to display **Managed Environment Consumption NCA100 GPUs** limit/usage; do not ask owner to redo those same steps without a different diagnostic path.
- **NEXT diagnostic, read-only:** use dedicated GitHub DEV OIDC identity in a coordinator-reviewed manually dispatched read-only workflow or authenticated local Azure CLI to query **Microsoft.App resource provider registration** and the Container Apps managed-environment A100 GPU quota API/CLI for exact subscription/region. Record returned status codes + precise quota values; don't treat zero results as denial. Feature5-owned `feature5_motion/azure_gpu_readonly_cli.py` offers a no-write inventory helper but does not create an A100 environment and cannot show environment quota when no environment exists.
- **REMAINING blocking inputs** before actual Hunyuan test: real licensed model shards/checksum trust, supported CUDA GPU/capacity, one-job concrete maximum dollar approval and synthetic-only regional processing, and verified container image profile. No live GPU/MP4 exists.

## 2026-10-26 — Next action after ARM success notification, missing resource
1. **P0 read-only reconciliation by GitHub DEV OIDC coordinator:** inspect `az deployment group show` and `az deployment operation group list` for `CustomDeployment-20261026093554`; enumerate `Microsoft.App/managedEnvironments` in exact `rg-retailgrowth-dev`; query `Microsoft.App` provider registration. The browser cannot reliably inspect deployment details and must not be retried blindly.
2. If deployment successfully created target but RG list was stale: verify exact DEV tags, East US, Consumption only and no paid profiles; run `az containerapp env list-usages` for environment and read **Managed Environment Consumption NCA100 GPUs** limit/currentValue. Missing row = UNKNOWN/absent, not zero.
3. If succeeded deployment is **empty**, coordinator may perform reviewed `what-if` with `feature5_motion/infra/empty_gpu_env.json`, require precisely one Create and no other changes, and explicitly deploy **only the empty environment**; no GPU/app/job/registry/logging.
4. Still blocked for genuine video: official licensed Tencent weight shards, compatible A100 quota, synthetic-only geography/terms, realistic 24vCPU/220GiB + GPU worst-case capped USD, private output receipt, one no-retry CUDA job and human garment-motion QA. Detailed reconciliation instructions in `ARM_CUSTOM_DEPLOYMENT_DISCREPANCY_20261026.md`.

## 2026-10-26 — Exact next step with existing federated Azure identity
- Coordinator copies/reviews `docs/feature5/proposed-workflows/azure-feature5-oidc-reconcile.yml` into `.github/workflows/` on a coordinator-owned change and merges after security/CI review. It uses existing `dev` environment secrets, `azure/login@v3`, manual `workflow_dispatch`, and **read-only** Azure CLI; it is intentionally ineligible on feature branches. The current GitHub plugin does not expose a dispatch method, so the initial run must be started via GitHub Actions **Run workflow → main** (or a coordinator-native workflow trigger), not TinyFish.
- Read logs and record the actual ARM result/managed environment quota. **Do not automatically create** the same environment again after Azure's earlier success notice without knowing whether ARM `CustomDeployment-20261026093554` had an empty template. No actual CUDA/Hunyuan job until licensed weights, A100 available quota and strictly approved full price cap.

## 2026-10-26 — Live deployment succeeded, next gate is quota 0→1
- **DONE, independently verified in Azure:** East US empty `rgai-f5-gpu-canary-eastus` in isolated `rg-retailgrowth-dev`, default Consumption only; [OIDC #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764) green. **ManagedEnvironmentConsumptionNCA100Gpus: limit=0, used=0**. Do NOT create another managed environment or redeploy the confirmed resource; no GPU/app/job has been launched.
- **P0 owner/service quota approval:** select that exact environment in Azure Portal → **Settings → Quota**, request **new limit = 1** for **Managed Environment Consumption NCA100 GPUs**, and verify Azure's approval/status. This is an *environment* quota; do not request the unrelated subscription dedicated A100 meter. Microsoft may automatically approve or route to review. Do not create support cases if owner does not authorize them. No quota request submitted so far.
- **P0 genuine user-requested video after quota:** licensed verified Tencent 1.5 weights + pinned SHA256 lock, working BF16 A100 CUDA image, synthetic no-customer photo processing in East US subject to territory/license review, explicit full-cost one-job hard stop, exact one run/zero retries. Record a real 5-second portrait kurti-boutique MP4, ffprobe, hash, frame sheet and human quality review; only then claim Hunyuan sample produced. Part3/Feature4 hosted integrations separately pending.

## 2026-10-26 — Azure GPU alternate path eliminated under current quota
- Live read-only GitHub OIDC run #40355181214 confirmed Central India and East US **regional VM vCPU quota 10** and no user-subscription A100 VM eligibility. Azure A10 appears in SKU catalog without restriction, but only a **full 24GB A10** with 36vCPU satisfies Tencent >=14GB with offloading; current region quota is insufficient. Do **not** deploy a 6-vCPU, 4GB fractional A10 expecting model inference, and do not increase other quotas without reviewing costs. No Azure GPU is yet suitable within quota.
- Cheapest approved short-run path remains an **owner-submitted request for ONE per-environment `Managed Environment Consumption NCA100 GPU`** on existing `rgai-f5-gpu-canary-eastus` (limit 0); Microsoft may automatically approve or route for manual review. Request alone has no GPU compute usage fee. No request has been made. Only after quota 1, source/weight license checksum, territory/privacy, full budget + bounded GPU job, and actual MP4 QA can Feature5 claim genuine generation. Keep job scheduling disabled.

## 2026-10-26 — Prioritized action after verified quota=0 and provider comparison
1. **External Microsoft prerequisite (UNSUBMITTED):** on existing `rgai-f5-gpu-canary-eastus` → Settings → Quota request `Managed Environment Consumption NCA100 GPUs` new limit **1**; log actual request response/status. OIDC usage read confirms zero, but no supported CLI/REST submission path was verified for this *environment* quota.
2. **Development source follow-up:** Review/merge the feature-owned `external_gpu_budget.py` quote screening only after CPU test and PR CI; it does not enable new runtime or spend. Existing 5s red-kurti `demo_fashion.py`, pinned Tencent runtime and manual GPU harness remain the ONLY acceptable genuine-video flow.
3. **Fallback only if provider controls approved:** independently verify current Runpod A40 48GB or RTX 4090 quote, host RAM, location/terms, signed-in account capacity, all-in provider cap and automatic termination/disk delete. Do not treat offline quote screening as an actual provider reservation or hard billing cap; avoid retailer/customer media.
4. **Paid one-shot still BLOCKED:** verified GPU quota or approved bounded external rental, independently licensed official model/weights digest, BF16 CUDA image, proper region rights/consent, full-dollar cost allowance, one attempt/no retry, private original `clip.mp4` + ffprobe/hash/contact sheet + human QA and invoice/teardown. None has been executed.

## 2026-10-26 — A40 source bug fixed; external action still outstanding
- DONE: A40 48GB BF16 quote screening and CPU tests under Feature5-owned PR #323; NVIDIA/Runpod public specs support the *hardware candidate*, not a real Hunyuan model benchmark. Provider-side teardown bound in cost screen remains mandatory.
- NOT DONE: Azure **managed-environment** NCA100 quota new limit=1 request (submit under existing environment Settings→Quota), account-specific cloud GPU capacity/rates, prepaid hard cap, approved Tencent weights, real CUDA, true five-second H264 MP4.

## 2026-10-26 — Next after evaluated full GitHub solutions
- **Coordinator decision required:** evaluate retaining Hunyuan 1.5 vs adding separate Feature5 **LTX-Video v0.9.8 13B distilled** long-shot candidate, and use Part3-owned Wan2.2 as permissive short-format baseline; no duplicated Part3 implementation.
- **Before paid deployment:** independently review LTX 0.X checkpoint commercial license and AI disclosure/hosted SaaS constraints, pin exact code/weights/ComfyUI legacy workflow version plus checksums, ensure DEV Azure `ManagedEnvironmentConsumptionNCA100Gpus` limit >= 1, then operator cost ceiling.
- **Acceptance:** genuine private synthetic 5s pilot and controlled 60s model-extension clip at target portrait FPS, original SHA/FFprobe, garment/face visual reviewer and actual measured Azure GPU billing; until then neither performance nor cost is proven.
- Source/architecture comparison: `docs/feature5/OPEN_SOURCE_VIDEO_ENGINE_REVIEW_20261026.md`. No H100 Terraform apply, no new worker deployment and no PR merge independently.

## 2026-10-26 — Full upstream deployment priority
- User wants **real complete upstream project**, not replacement Feature5 generator code. When Azure quota supports it, use pinned, full ComfyUI plus official LTX-Video engine/models and their genuine long-shot workflow in private serverless A100; H100 Microsoft sample only if the owner accepts its ~3x active cost and separate 40-vCPU VM quota.
- Gate all paid deployment on operator-approved total budget, exact committed source/weight manifest, license acceptance, secured ComfyUI API, private Azure networking, one-run/no-retry and real visual quality benchmark. Stop/deallocate H100 VM when inactive; serverless A100 scale-to-zero.
- Detailed Azure USD/INR comparisons and blockers in `docs/feature5/OPEN_SOURCE_VIDEO_ENGINE_REVIEW_20261026.md`. No switch to paid hosted APIs or mock output as proof.

## 2026-10-28 — External GPU proof first, no automatic purchase
1. Operator may purchase prepaid credits on https://jarvislabs.ai/in and select **1× A100 80 GB on-demand** in an available India region (published **₹140.94/h**, separate storage + 18% GST; **no spot**). Minimum top-up/availability must be checked in checkout, not inferred.
2. Before booting/renting, approve a hard spending ceiling, plan minimum 100GB scratch/model disk, verify secure SSH/private endpoint, project checkpoint weight size/terms and output transfer path. Do not expose ComfyUI or customer media; use synthetic image/garment brief.
3. Install/clone **complete official Wan-Video/Wan2.2** pinned release+TI2V-5B model weights; execute its official 5s portrait inference CLI; preserve original MP4/ffprobe/frames/SHA and real billed minutes. No imitation generator and no unfounded 60s estimate.
4. Pause immediately when GPU work finishes and **delete disk/instance after downloading private evidence** to avoid continued storage charges. Then compare genuine visual results before any 15s/60s proposal. All code and ledger integration remains Part3/coordinator-owned; Feature5 supplies quality/cost evidence only.

## 2026-10-28 — Azure A100 quota now visible as 2 (operator screenshot)
- **Previously pending blocker changed:** Azure Portal environment GPU quota **0 used of 2 limit** for A100; owner may use existing East US environment instead of renting third-party GPU. Retain image/screenshot evidence in issue #400; independently confirm with `az containerapp env list-usages --resource-group rg-retailgrowth-dev --name rgai-f5-gpu-canary-eastus` before making any GPU deployment.
- NEXT: choose original Wan2.2 TI2V-5B upstream for one genuine portrait 5s GPU benchmark, after source+weights integrity and license review. Submit a coordinator-approved one-shot, cap-controlled private GPU worker (1 GPU max, min replicas 0, no automatic retries, private output only) using existing Azure OIDC. **No paid GPU provisioning until the cost ceiling and resource configuration are reviewed.**
- Cost model: quota alone ₹0 in GPU compute, running Azure serverless GPU replicas billed by GPU/CPU/RAM seconds, scaled-to-zero no replica resource charge. Storage/logging/network may have independent charges. No measured per-video estimate yet.

## 2026-10-28 — GPU-OFF readiness follow-up
- Before ANY paid test: review immutable upstream ComfyUI/Wan2.2 model/checkpoint and native workflow SHA256, commercial license, private region-safe checkpoint staging, pinned CUDA image and all ancillary costs. Coordinator-owned provision of Manual Azure Container Apps A100 job remains NOT DONE.
- Run mocked tests and shell syntax only; do not deploy/provision a GPU or switch on ComfyUI during preparation. After separate explicit paid authorization, inspect correct job quota/profile, run single sample with start/stop controls and verify actual Azure bill. See A100_SAFE_PREP_20261028.md.


## 2026-10-28 — Wan P0/P1 remaining blockers after CPU-only preflight
1. **P0 pinned ComfyUI production image:** owner/legal review of GPL+model/encoder/NVIDIA obligations; independently select a real SHA256-pinned CUDA/Python base, produce complete transitive --require-hashes CPU/GPU wheelhouse and licence bill of materials, verify vendored source commit, build one immutable OCI image after separately authorized build/registry charges; do NOT turn on GPU from Containerfile alone.
2. **P0 real backend evidence:** independently obtain native /object_info from the private built runtime and run the new wan22_native_preflight.validate_native_graph_against_object_info check. Validate the source 704x1280/24fps/121-frame graph, SaveVideo structured MP4/H264 codec, actual checkpoint choices, Azure model ReadOnly mount and real GPU memory. Fake offline schema/checkpoint headers are insufficient.
3. **P0 claim/rights/inference:** coordinator wires feature5 native adapter into existing shop-JWT, current Feature3 private-image grant, subscription reservation, leased Part3 job/fencing and one private upload with exact output SHA; ensure runtime quota and explicit approved per-test maximum USD. Remain disabled until explicit approval. No automatic retries on UNKNOWN paid outcome.
4. **P1 genuine I2V/T2V acceptance:** run precisely one capped authorized 5-second fashion I2V, inspect all frames against original live approved garment/model source; independent anatomy/embroidery/face temporal reviewer plus disclosure; Feature4 outputs final 1080x1920 Reel only after valid approved private clip. Native 1080p claim is forbidden. Current Feature2 v1 is I2V-only; T2V orchestration needs a separately approved creative contract.
5. **P1 coordinator:** reconcile draft #323/#465 with latest main and independent feature #2/#4 schema, as branch is stacked on old base; do not independently merge shared routes/SQL or modify WineShopPOS. Repeat four-job exact-head CI and post-merge main CI.


## 2026-10-28 — Updated Wan release priorities after wheelhouse audit
- DONE SOURCE: pinned Wan graph profiles, Feature2/F4 synthetic direction adaptation, F3 private reference and F4 pending-only clip handoffs, ffprobe/static-motion CPU tests, pinned ComfyUI SaveVideo structured MP4/H264 fix and native node drift checks.
- DONE SOURCE: audited wheelhouse byte SHA + metadata and deterministic --require-hashes lock generation/verification, negative tests for altered/missing/extra/linked wheels. This is tested with synthetic wheels ONLY.
- P0: independent operator must now acquire/review actual licensed immutable CUDA base digest, all resolved transitive PyTorch/ComfyUI/GPU wheel files and hashes, and matching source-commit proof; audit REAL offline wheelhouse, verify exact build-context lock, then build ONE reviewed immutable OCI image with no model download, only with separately authorized build/registry costs.
- P0: real protected runtime /object_info, mounted six private model checks (metadata alone does not prove full checkpoint byte hashes), GPU VRAM/response verification; correct any native schema mismatch with real evidence. No known running A100 job.
- P0: coordinator connect to existing authoritative Feature3 source approvals, Feature2 creative hash, Feature4 renderer, shop subscription reserve/Part3 lease claim/fencing/one-try retry reconciliation and private output writer. Never add a second wallet/queue.
- P1: owner-approved capped paid 5-second genuine Wan I2V test using current licensed active retailer source and approved cross-region transfer; human reviewer assesses anatomy/fabric/pattern/embroidery/continuity and authorizes private clip for Feature4's final Full-HD Reel. No real paid run, human visual approval or production clip so far.
- P1: coordinator reviews stacked draft PR #323/#465 against main and coordinates interface/merge; preserve independent 4/4 checks and postmerge main CI, WineShopPOS untouched.


## 2026-10-28 — Next unfinished after GPU-OFF execution/source sprint
- DONE CPU SOURCE: complete canonical Wan node topology, independently authorized F3 image-basename binding, entire vendored ComfyUI file SHA audit, transitive wheelhouse+pip-hashlock+immutable OCI base review gate, private non-root no-metadata Containerfile scaffold and default-disabled official local /prompt + /history single-attempt adapter with negative tests.
- P0 EXTERNAL ARTIFACT: independently obtain/legal-review complete pinned ComfyUI checkout and all-file SHA manifest, actual reviewed CUDA/PyTorch wheelhouse and hashes, immutable CUDA base OCI digest. Check the real bundle with offline gate before any separately approved build/registry costs. Current source template cannot build as-is.
- P0 COORDINATOR WIRING: bind injected lease/paid claim + approved original F3 bytes/source grants to existing transactional Part3 subscription reservation/fence/outbox, stage one lease-local Comfy input, accept only one output after bounded local probe/actual private sha+DB receipt/settlement. Do NOT add duplicate queue, wallet, HTTP route or migration.
- P0 RUNTIME: real protected ComfyUI /object_info, installed checkpoint choices, actual Azure model-readonly mount/torch ABI/true CUDA compatibility; no real inference.
- P1 OWNER-APPROVED A100 LATER: exactly one cost-capped licensed sample I2V, actual motion/garment/facial quality and private final 1080x1920 Feature4 composition, human review and measured costs. Remain OFF until explicit separate permission.
- P1 COORDINATOR: reconcile draft stacked #323/#465 and Feature2/3/4 main contracts, merge under coordinator ownership, verify postmerge four-job CI and hosted negative rights/tenant tests. Feature5 PR remains DRAFT.


## 2026-10-28 — Next after source-only one-attempt and private output intake
- SOURCE DONE: new existing-ledger atomic unique Comfy submission-intent callback required; denial of second start in same dispatcher and across two mocked workers. No additional wallet, outbox or cloud queue. Exact paid/unknown persistence must be bound by coordinator to the existing Part3 claim ledger and separately verified in hosted signed DEV.
- SOURCE DONE: new exact private per-attempt result discovery, tenant/job/token permission check before byte access, real 121-frame 704x1280 H264 MP4 ffprobe + objective moving-frame test; pending receipt remains review-required. CI includes synthetic moving FFmpeg media and path/traversal/missing/second-result/revoked-claim negatives.
- P0 STILL ENGINEERING: coordinator binds real transactional prepaid active claim + SHA-approved Feature2 direction + current Feature3 private original and try-on rights + unique durable submission-intent CAS + tenant/job/token scoped private output access + measured billing, storage upload and final fenced DB receipt. Source mock callbacks are not a live implementation.
- P0 STILL EXTERNAL: independently reviewed real ComfyUI whole source/notice, CUDA base OCI and transitive wheel SHA bundle, build/registry expense approval, actual private /object_info and real model read-only mount/runtime. GPU OFF.
- P1 REAL ACCEPTANCE: separately capped and approved A100 single test, actual human/garment/anatomy motion, review/publishing/license, Feature4 final Full-HD composition, coordinator PR #323/#465 integration and signed hosted tenant-negative E2E. Track detailed matrix in SOURCE_READINESS_AND_PENDING_20261028.md.


## 2026-10-28 — GPU-OFF private output hardening and mock-to-media acceptance
- First verify four new exact-head Actions jobs. Coordinator must verify pending receipt canonical SHA256, current job/attempt fences, and accepted private MP4 bytes inside existing atomic Part3 DB/Storage writer; returned metadata dict is not a stored immutable receipt. External remaining: full vetted CUDA/Comfy source and hashed wheels/OCI image, license/build approval, real private /object_info, signed Feature3 rights and transactional Part3 lease/settlement integration, one separately authorized A100 test, human visual/fashion review, Feature4 assembly, signed tenant negatives, coordinator merge.


## 2026-10-28 — GPU-OFF source qualification and exact external gates

No additional Feature5-owned CPU-source defects identified after #40733254877. First independently confirm four new exact-head CI jobs after final documentation update. Then coordinator must wire existing Part3/JWT/subscription/outbox/lease and private Storage import, verify exact input source grant and mutable receipt hash; never implement a second billing/storage/publishing system. Real remaining gates: independently license-review complete vendored ComfyUI/CUDA source, actual model/wheel SHA-256 and immutable OCI runtime plus approved build/registry charges; protected real /object_info and model mount/ABI; coordinator-owned existing Part3 unique intent, signed current F3 tenant rights and leased job claim, billing reconciliation and immutable hash-rechecked private importer with signed DEV negatives; owner-authorized one cost-capped A100 5-second Wan inference, observed stop and bill; human garment/likeness review; Feature4 final 1080x1920 assembly; coordinator PR integration/hosted acceptance. A100 and paid APIs remain OFF. Source readiness never authorizes automatic paid runs.


## 2026-10-28 — Public stock and hosted acceptance handoff
See docs/feature5/STOCK_MEDIA_QA_AND_HOSTED_HANDOFF_20261028.md. Real Pexels bytes not downloaded in restricted runtime; local sample adapter and tests only. Read-only hosted Supabase policy/schema audit completed; signed hosted JWT cross-shop & Part3 transactional import acceptance still coordinator-owned. No real licensed media product match, no model inference, no paid GPU.


## 2026-10-28 — Coordinated eight-task security and public-media QA continuation

Feature5-owned code validation: verify latest 4/4 source/doc CI; repair any failures without weakening tests. Coordinator: bind actual signed shop JWT, existing Part3 subscription/reservation/lease and one-time unique durable submission-intent CAS; separate cross-worker existing-intent READ-only reconciliation; active F3 original byte/try-on rights and second pre-submit approval check; current output lease recheck; ONE hash-verified tenant-private immutable DB/Storage media receipt/settlement; F4 independently trusted human approval. Host Dev JWT-negative OWNER/VIEWER, expired, foreign-shop and revoked tests are not completed. Public stock Pexels candidates require manual bytes/download and individual likeness/brand endorsement consent; cannot substitute for real tenant-owned garment. External immutable Comfy source/CUDA/vendored wheels/OCI legal audit, actual protected /object_info, separately capped paid one-shot A100, real fashion/anatomy/fidelity and F4 Full-HD remain blocked. The exact latest source prior to this documentation commit is d747b6b9d622baba9198f80dcf81a9a2f14235f0; run final four GitHub CI jobs again on the documentation commit before claiming current-head success. Earlier independent 858e5e598d6348fb2849c7497550d109d7660a7f run #40747182176 was 4/4 SUCCESS. A100 and paid API use remain OFF; no actual Pexels bytes, Wan inference or WineShopPOS change.


## 2026-10-28 — Continued fail-closed source sprint after previous green CI

NEXT: Verify final documentation-head CI four jobs and remediate genuine failures. Feature5 source-only tests now include mutable grant alias, post-intent F3 revocation/no POST, malformed acknowledgement, forged local history and foreign F4 receipt/no DB lookup. Remaining coordinator-owned REAL signed Part3 job+lease+unique DB CAS+immutable private storage+usage settlement, current F3 licensed source and independent F4 review, hosted tenant signed negatives. No real Pexels byte evidence or genuine Wan inference. Immutable CUDA runtime/license review and explicitly capped paid A100 acceptance await separate approval.


## 2026-10-28 — Parallel/timeout negative proof

After latest tests, verify all four jobs at the FINAL documentation SHA. Remaining real gates unchanged: coordinator Part3 signed tenant/lease/CAS and private importer, Feature3 real rights, Feature4 human review, separately approved licensed Comfy image and capped GPU. No source-owned paid work remains when CI passes.


## 2026-10-28 — Stock media decoded-frame screening continuation

Remaining free work: rerun four-job CI on final SHA after the new local stock fixture screen; independently obtain lawful original Pexels assets and run inspector to record actual original media hashes, model image/video suitability, and human review; never present different garments as a matched video try-on. Coordinated Part3/F3/F4 signed hosted acceptance and paid GPU remain separately gated.


## 2026-10-28 — Image-generation A100-free source qualification

Continue GPU-OFF: verify latest CI four jobs and fix any failing tests; independently supply licensed Pexels original photo/video bytes or authorized tenant media to execute the existing offline inspector on real files. Feature3 owns FLUX.2 Klein image generation and actual licensed try-on; Feature5 only composes a clearly labeled non-AI private reference review board. Full FLUX/real video generation, signed Part3 claim/unique intent/immutable importer, hosted real JWT two-tenant tests, independent F3 reviewer/Feature4 editorial signoff still require coordinator integration and separately approved compute. Do not start A100.


## 2026-10-28 — CPU first-frame cross-feature integration regression

Verify exact latest SHA 4/4 CI after cross-feature image test. No real licensed stock original bytes or photorealistic image-model inference until separately authorized F3 owned compute/source. A100 stays OFF; coordinator responsible for actual signed tenant lease, importer and Feature4 approval.


## 2026-10-28 — Part3 native private import GPU-OFF acceptance

Source-only test accounts now cover two simulated user sessions/shops, successful isolated private media import/download, deny foreign users and swapped lease/hash, unique intent/replay prevention, ambiguous Storage ACK, revoked rights post-upload, forged receipt and synthetic Feature4 metadata. The `test_feature5_part3_gpu_off_acceptance.py` suite exercises **real FFmpeg encoded 121-frame 704×1280 testsrc2**; labels synthetic output NO WAN. Next: run exact-head four CI jobs; coordinator must wire authoritative Part3 DB transaction + Storage upload, source-owner actual F3 rights and F4 real human review before any hosted claim. Actual Pexels raw bytes and signed hosted JWT credentials remain unavailable; never mark simulated sessions as real login.


## 2026-10-28 — Import intent ambiguous ACK + private staging path guards

Added negative tests for foreign attempt directory, linked attempt root, post-upload source mutation and lost unique intent commit acknowledgement. Run exact-head 4/4. Human, real JWT, licensed Pexels original bytes and hosted Storage are still explicitly unverified. Paid A100/Wan disabled.


## 2026-10-28 — Two-shop parallel offline acceptance and Pexels rights audit

Latest GPU-OFF source suite adds two-shop fake login/cross-private-download deny, 12-way concurrent single-intent upload, and new pinned Pexels page/license audit. Actual Pexels raw bytes still need a rights-approved original download and manual human review, hosted signed Supabase JWT + Part3 DB/Storage still pending; no A100. Verify final 4/4 CI.


## 2026-10-28 — Pinned official Wan2.2 weight source inventory

GPU-OFF source/Pexels test suite must finish exact-head four CI jobs. Runtime weights and pinned CUDA are unverified; acquiring >16GB verified files, SHA, legal permissions, region and budget requires separate delivery mechanisms. Meanwhile F5 native private import/tenant mocks and F3/F4 metadata tests continue without A100.


## 2026-10-28 — Current Feature3 / Feature4 / Part3 real source contract audit

Next after exact-head CI: coordinator must reconcile incompatible F4 Hunyuan/Part3 Wan2.7 with F5 Wan2.2 native 704x1280 121-frame profile and deployment/credit schema, merge actual F3 server-side current reference resolver, and integrate F5 fenced claim/outbox/private import. Test-only F3 packets do not grant real rights. Separate real source byte/consent, hosted signed tenancy and paid inference remain external gates; do not mark production complete.


## 2026-10-28 — F3 verified consumer-to-private first-frame staging + hosted catalog reality

Feature5 never treats feature3 packet freshness as a provider permission. `stage_fresh_feature3_consumer_input` calls both current F3 packet reader and the independently server-authorized raw first-frame resolver, and does a *second* packet refresh after the private PNG staging; output is deleted upon denied/revoked second refresh. The 0-row hosted Feature3 catalog and absent Part3 premium jobs table cannot be replaced by test logins or app mock receipts; record success only for CPU synthetic tests.


## 2026-10-28 — Deterministic fake token corruption regression fix

Verify final four-job GitHub Actions after token negative-test fix; no actual deployment until coordinator versioned premium schema, real tenant-owned first frame, private Storage and F4 live approval. Existing FFmpeg negative auth failure was test-flakiness and has been corrected, not silently skipped.


## 2026-10-28 — Current main real F3 producer source integration

Check new exact-head CI, then coordinator can reconcile Part3 premium schema/provider against Wan2.2 native worker; since F3 consumer is now main, no cross-branch dependency for its offline contract. Real F3 model catalog and true approved retailer image, signed hosted tenant read, model runtime and F4 final Reel still not proven; no paid GPU.


## 2026-10-28 — F3→CPU motion→Part3→F4 continuous offline acceptance

Run exact-head four-job CI after new single-path F3→CPU FFmpeg→Part3→F4 integration test. Source-level rehearsal is now a full sequential path, but the native model-origin is explicitly synthetic and different from Wan; keep production blocked until coordinator resolves Part3 Wan2.7 vs F5 Wan2.2 schema/worker, genuine license/tenant-authenticated media, genuine private render and human QA. Real Pexels raw files still not downloaded.

## 2026-10-28 — After immutable import handoff guard

1. Verify latest exact-head GitHub CI (all four required jobs); fix any genuine failures without bypassing tests.
2. Coordinator must reconcile existing Part3 Wan2.7 provider/credit schema with **separate versioned** Wan2.2 native model, attach real signed tenant/lease/CAS/private Storage callbacks, and run authenticated DEV two-tenant negative acceptance. Feature5 source-only callbacks and mock sessions are not hosted integration.
3. Obtain lawful actually verified retailer model/garment/try-on originals from Feature3, with human likeness and marketing rights, immutable source SHA; validate with private reads and revocation.
4. Build externally reviewed immutable ComfyUI/CUDA + wheel SHA image, verify live native node schemas and private staged model hashes without paid A100 launch. Paid capped inference and real garment/Feature4 visual acceptance remain blocked pending explicit separate authorization.
5. Generate any technical CPU synthetic samples with explicit NOT WAN/NOT CUSTOMER label. Do not mark sample media as real AI or Pexels original.

## 2026-10-29 — Next independent GPU-OFF and external gates

- Verify exact-head 4/4 CI for mandatory uploaded-object byte readback; fix real failures. Reader contract: trusted service-only `read_back_private_chunks(shop,job,attempt,"retailgrowth-media",key)` yields bounded bytes of the **actual stored object** under existing reserved/leased attempt; never trust browser/storage ACK metadata or a public URL.
- Coordinator: wire this reader to existing Part3 private bucket/DB/tenant JWT fences; reconcile Wan2.7 premium provider versus separate Wan2.2 704x1280/121-frame native reservation contract, one UNIQUE durable intent CAS, private output media registration and credit/settlement under existing shared schema. Hosted premium table remains absent in last read-only DEV inventory.
- Obtain actual tenant-owned Feature3 image+garment with independent person/likeness/commercial approval and current server-side rights; perform signed DEV two-shop OWNER/EDITOR/VIEWER foreign/revoked checks and trusted private signed downloads. Offline synthetic fixtures are not hosted identity tests.
- Independently attest ComfyUI/CUDA wheel/weights exact SHA and licensing, protected live /object_info and image; separately authorize capped paid A100 5s inference and real garment/face human QA before Feature4 Reel release. GPU remains OFF.

## 2026-10-29 — Feature3 #604 GPU-OFF handoff adoption

- Verify exact-head Python/media/frontend/disposable-DB CI on the Feature5 private-worker adapter branch; do not call test-only callback actual #604 source execution.
- Coordinator: independently merge Feature3 #604 after its own CI and rights checks, then invoke `resolve_feature3_materialized_first_frame(...,materialize_feature5_input=feature3_worker_inputs_v1.materialize_feature5_input)` in the existing active Part3 worker **with authoritative JWT/RLS readers and current leased job**. The returned private frame is still NOT an authorized paid submission.
- Feature3: provide independently approved licensed exact garment-wearing-model first frame and persisted person/likeness/commercial rights (OpenVTO demo's separate shirt+model photo does not qualify). Stable `materialize_feature5_input` identity/F3 revision/fingerprint/image_bytes must remain current and private. Test revoked, foreign, changed bytes and wrong lease.
- Remaining Part3 coordinator: versioned Wan2.2 versus Wan2.7 worker/credit contract, atomic submission intent, private Storage readback, signed customer two-shop hosted E2E; separate GPU runtime/inference/human/F4 review remains blocked until permitted.

## 2026-10-29 — Completed independent source batch and remaining authority gates

**DONE source (same Feature5 branch):** clean conflict-free two-parent sync from newer main including merged F3 #604; real `feature3_worker_inputs_v1.materialize_feature5_input` → strict Feature5 byte/identity adapter → real reference packet/private first-frame staging → FFmpeg 704×1280/121f CPU demo → mocked Part3 fenced private readback/settlement → F4 human-review-pending consumer, with end-to-end source tests. Native output FFprobe now rejects any stream other than one H.264 video; mock corruption/audio/data/extra video tests plus real FFmpeg AAC remux regression added. No GPU necessary.

**NEXT acceptance (not independently closable without real approvals/resources):**
1. **Coordinator Part3:** version and merge separate Wan2.2 TI2V 5B 704x1280/121-frame profile alongside Part3 Wan2.7, with active tenant JWT/RLS, DB transactionally reserved cost, single-use submission intent/lease, no retry of UNKNOWN, private Storage immutable clip readback (actual byte SHA), and atomic ledger/media settlement. No independent schema or wallet in F5.
2. **Feature3 and customer/reviewer:** real source-approved model **wearing** the actual approved retailer garment, persistent person/model publicity rights, private original bytes with exact SHA, signed OWNER/EDITOR/curator reviews, current/revoked same-shop access and commercial publishing rights. Public OpenVTO separate model/shirt images remain demo-only. Hosted DEV migrations/true sessions are still independently gated.
3. **Runtime/legal/paid:** reviewed original model shards + hashes, complete ComfyUI/CUDA container and wheelhouse/licensing approvals and live private `/object_info`, bounded geographically permitted paid 5s inference, actual invoice/teardown, independent human garment/color/face temporal approval, and approved professional F4 Reel. A100 OFF until explicit paid go.
4. Verify final GitHub Actions **four jobs at exact doc-head SHA** and keep PR #465 DRAFT awaiting coordinator integration. Do not merge cross-team schema or touch PROD/WineShopPOS. All prior test-only receipts remain explicitly non-production.

## 2026-10-29 — Independent work after new F3 three-image source handoff

**IMPLEMENTED source-only:** conflict-free main sync with Feature3 late private garment/model/first-frame worker; F5 strict role-by-role current-rights SHA adapter and full F3→CPU H264→fake Part3→F4 review-pending e2e; forged metadata denial by real native ffprobe re-probe after current claim and BEFORE consumption of unique irreversible upload intent. CPU source tests cover foreign/revoked/lease/changed bits, role swaps, unapproved provider and invalid video technical evidence.

**DEV read-only update:** 31 migrations now applied through 20261028232000, 0 model registration, 0 actual Feature3 GPU jobs, premium-video job schema absent. Six RLS-disabled `retail_private` tables reported by Supabase advisor; pg_catalog confirms no direct `anon`/`authenticated` SELECT/INSERT grants. Coordinator must review exposure and grants, not blindly mutate service-owned schemas.

**Remain genuinely blocked on independent external outcomes:** (1) register real licensed/same-shop retailer model wearing exact approved garment and signed OWNER/EDITOR+curator rights, instead of unrelated OpenVTO demo pair; (2) coordinator merge/version Part3 authoritative Wan2.2 provider/reservation/lease/unique intent/Storage byte readback/signed private download and hosted two-tenant roles against 31-migration DEV; (3) obtain reviewed native CUDA/weights/licensing/immutable runtime, capped explicitly approved GPU 5-second inference and measured credits; (4) signed human quality/Feature4 final high-quality Reel and voice/music permissions. No GPU/OIDC cloud changes in this branch. Verify 4/4 exact last documentation-head CI and keep PR #465 DRAFT until separate coordinator integration.

## 2026-10-29 — Seven selected tasks, actionable last gates after completed offline work

**[runtime] PARTIALLY COMPLETE / blocked externally:** official pinned source tree and GPLv3 vs Apache-2.0 verified; existing reviewed source + requirements + model mount validators and intentionally gated Containerfile audited. Missing independently approved OCI CUDA/Python base digest, complete transitive byte-rehashed wheelhouse, GPL/NVIDIA legal signoff, immutable built image registry digest and execution environment.

**[weights] TOOLING COMPLETE / actual installed bytes UNVERIFIED:** new manual `python -m feature5_motion.infra.wan22_local_weight_audit --mounted-share /mnt/retailgrowth-models --private-manifest /secure/models-sha256-manifest.json` rehashes three authentic mounted files from trusted six-source manifest in an authorized service process. Run via coordinator protected READ-ONLY mount; verify report and expected original upstream HF file SHA, record real bytes/sha and read-only config. CI tiny fakes are not actual model proof.

**[negative] SOURCE COMPLETE / hosted unverified:** private F3/Part3 fail-closed gates from prior PR + new full byte hash and immutable review/post-review replace tests. After final exact-head four-job CI, no other source-negative tests currently identified; real signed JWT/tenant DB role+CAS+Storage tests are separate Part3 operator integration.

**[supabase] READ-ONLY audit DONE / remediation needs coordinator:** 31 applied versions, zero Feature3 model/GPU job rows, no premium/video table; six private RLS-off tables have no direct `anon` or `authenticated` SELECT/INSERT/UPDATE grants. Audit 22 SECURITY DEFINER exposed RPC warnings, 15 no-policy INFO and password protection WARN, safely reconcile RLS and schema exposure before DEV release. Do not enable RLS blindly or bypass current security.

**[livecomfy] BLOCKED externally:** no approved built immutable OCI runtime, protected live ComfyUI, read-only attached full hashed checkpoint mount, native authenticated `/object_info` with independent server proof or actual 5s inference; perform them only within protected coordinator-owned approved budget and region, never by browser/public server or synthetic `object_info` test.

**[visual] BLOCKED on true media/person rights:** obtain Feature3 reviewed exact garment-wearing model source, actual native AI clip, signed independent rights/curator consent, compare all eleven human visual criteria against original, preserve exact private clip SHA and human reviewer signature. New immutable checklist tests pass offline; 9s MIT separate-scenes technical footage cannot be accepted.

**[merge] SOURCE SYNC DONE / final integration blocked:** main sync is conflict-free and does not override Feature3 or testing-chat code. Keep draft PR #465; coordinator still owns PR #125 Part3 Wan2.2-vs-Wan2.7 versioned job/credits/lease/Storage/reconciliation + true hosted E2E, after which coordinator merges verified parts and runs independent main CI. No unattended cross-owner merge. See [release audit](WAN22_GPU_OFF_RELEASE_AUDIT_20261029.md).

## 2026-10-29 — Feature3 real upstream model+garment input REUSED; updated live gates

**CLOSED for independent CPU/source development:** Feature3 original pinned fictional-model JPEG **and** product-garment JPEG have been transferred unchanged into F5 offline fixtures with matching actual Git blob IDs, attribution and unchanged MIT license. F5 source code now actually opens both original JPEG bytes via Feature3's own hash/image verifiers, stages a 704×1280 private model first-frame and constructs native 121-frame ComfyUI request graph without GPU or a provider POST. Tampering and forged rights are denied by tests. See [FEATURE3_REAL_GARMENT_MODEL_INPUT_20261029.md](FEATURE3_REAL_GARMENT_MODEL_INPUT_20261029.md).

**Still P0 for genuine fashion output:** Feature3's *current* published source proof is a model still + separate garment still, NOT a model wearing that exact product. Acquire a newly generated, authorized try-on/wearing-SKU frame, independent human garment/color/pattern/face validation, signed same-shop approval and actual registered private source; reuse existing `stage_fresh_feature3_consumer_input` under the real Part3 job lease for paid inference. No buyer/retailer title or server permissions may be inferred from MIT demo rights.

**Still P0 backend/runtime:** Part3 draft #125 real ledger job/claim/lease, paid budget reservation, native Wan2.2 profile, private Storage/callback/byte-readback and hosted two-tenant source rights. F5 independent approved OCI/ComfyUI/weight rehash/protected real `/object_info`, explicit capped GPU/API authorization and one measured real model-generated result, human quality signoff and F4 Full-HD Reel. Feature2 offline 15/30/60 source handoff is **already supplied** in PR #551 and native F5 `compile_motion_direction` exists; coordinator still must ratify and integrate its draft source, do not ask F2 to resend. Keep GPU OFF and PR #465 draft.

## 2026-10-29 — After F3 actual-original-image media chain

**CLOSED GPU-FREE F5-owned source**: original OpenVTO fictional model+separate garment **actual immutable bytes** now run all the way from Feature3 original verifier to native 704×1280/121-frame non-submitted graph, real CPU-encoded H264 zoom-pan MP4, FFprobe/motion screening, in-process protected Part3 simulation with unique intent/private object byte readback and wrong-user/replay denial, F4 denied pending commercial visual review. [Exact details](CROSS_FEATURE_HANDOFF_AND_REAL_IMAGE_CPU_VIDEO_20261029.md). No need to request F3 demo image input again.

**COORDINATOR NEXT**: review F3 #630 demo-only byte packet and F2 #551 creative source (both open), then merge in owner-approved order and retest actual authoritative imports. Source F5 can ingest existing real approved worker-media bytes independently, but live F2 writer/VM path not deployed and live F3 customer garment try-on absent. Do not treat separate demo garment/photo as SKU-worn first frame.

**STILL REQUIRED (not solvable from source mocks)**: Part3 #125 hosted durable premium job/claim/lease/credits/one-time intent/actual private output readback+storage; F5 approved immutable CUDA/Comfy runtime and full mounted checkpoint hash, protected native `/object_info`; explicit capped model GPU/API execution cost and real generated 5s video; independent actual garment/face/motion QA + F4 licensed final Reel; signed 2-shop DEV canary after coordinator release. #249 gateway unresolved; PR #465 stays draft.


## 2026-10-29 — New F2->F5 15/30/60s offline source gate follow-up

- Validate the *actual* Node `exportFixture(15|30|60)` output through `qualify_feature2_offline_storyboard` after coordinator integrates F2 #551 or provides an approved trusted artifact. The current new tests use contract-shaped source, not direct unmerged exporter execution. Preserve all original prompt/scene/garment SHA and deny customer/GPU permissions.
- Do not relax this gate to obtain green CI: inspect final exact-head Python, FFmpeg, frontend/Playwright and disposable Supabase jobs, fix F5-owned failures.
- No synthetic packet is a real garment-wearing approved F3 first frame or a Part3 JWT/lease/credit entitlement. Coordinator still owns actual Part3 contract and private Storage reader; F3 #630 demo-byte consumer remains pending its own merge. No paid native generation authorized.


## 2026-10-29 — Feature4 review-candidate adoption

- Coordinator/Feature4 should review F5's new `pending_private_wan_receipt_for_feature4` schema as **untrusted review metadata only**. Receiving editor must independently verify signed tenant/lease and current source+garment rights, actual private object bytes, active credit reservation/atomic settlement, real provider execution and human review before converting to the existing approved Feature4 render input.
- Existing `reviewed_wan_clip_for_feature4` approval gate must not be relaxed. Ask Part3 to expose a versioned service-only settlement + private object readback and ask Feature4 to preserve exact scene/prompt/source identity and a rejected/revoked state. No model-origin proof from source hashes.
- Verify four exact-head GitHub Actions jobs and attach result URLs after final docs; F2 contract tests are fixture-shaped until F2 #551 actually merges.

## 2026-10-29 — After merged Feature3 #630 byte handoff (current continuation)

**Completed source implementation:** actual merged Feature3 consumer-byte producer is present on the Feature5 branch after non-force main sync; new Feature5 adapter revalidates 3 distinct pinned roles/original SHA and stages only a private GPU-off native test graph. New source+negative tests submitted to GitHub CI, not a live hosted verification. Feature2 source-only 15/30/60-second storyboard gate and rich Feature4 pending-review media receipt already exist; do not rebuild them.

**Immediate work:** inspect exact-head four-job Actions on latest source/documentation SHA; repair genuine failures without disabling tests. Re-run independent source cross-feature tests after any upstream Feature2 revision lands. If main advances, perform a safe non-force reconcile without overwriting other owners.

**External gates remain:** Part3 #125 must provide live signed JWT/RLS OWNER/EDITOR and VIEWER-denial, existing credits/reservation and lease, unique provider submission/reconciliation, and one immutable private Storage byte-readback/settlement path with a separate Wan2.2 704x1280/24FPS/121f profile beside Wan2.7. Feature3 must provide a current commercially cleared *model actually wearing the actual retailer garment*, fresh rights/revocation, and verified private source. Approved immutable ComfyUI/CUDA OCI/dependency/18GB mounted weight check, authenticated real /object_info, explicit bounded GPU/API spend and a real 5s Wan inference are absent. Feature4 final 1080x1920 Reel, licensed voice/music and independent human fashion QA still require their owners. Keep PR #465 draft and do not charge GPU or touch PROD/WineShopPOS.


## 2026-10-29 — After F5 shot continuity / stream verifier

**New source tasks completed, CI pending:** 15/30/60s F2 chain continuity and fixed garment/source identity checks; fail-closed `python -m feature5_motion.verify_feature2_export --duration 15|30|60` for a real Node JSON stdout stream (2MiB bound, duplicate JSON key denial) and CLI tests. Check all four jobs on the final docs HEAD, fix genuine failures without disabling tests. Previous exact head `ce52576` [#40865478409](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40865478409) passed 4/4, before these changes.

**Cross-feature integration next:** After Feature2 #551 coordinator merge or a separately trusted source artifact, pipe its **actual** `node ai-agents/creative-director/export-feature4-feature5-fixture.js 15|30|60` into the Feature5 validator and run all three durations, with changed asset/review/shot negative tests. Do not copy F2 source into F5 or call fixture-shaped source actual executable integration. Inform F2 on #551 and coordinate Part3 #125 separate Wan2.2 profile+tenant JWT/RLS/leased credit/unique intent/UNKNOWN and server-side Storage byte readback; Feature4 #322 owns final human-reviewed 1080×1920 media.

**Blocked on external proof/approval:** verified retailer exact SKU worn by the model, signed likeness/commercial rights/current private original & revocation; coordinator Part3 hosted premium schema/job/settlement; reviewed immutable ComfyUI CUDA OCI/wheel hashes/actual 18GB mounted-file readback and native protected `/object_info`; separately approved capped paid 5s genuine Wan2.2 execution and human fashion fidelity; Feature4 real approved post-production. Preserve GPU OFF and PR #465 DRAFT.


- Latest F5 branch includes non-force upstream merge `d2bc8741` (latest coordinator main `214a27ff`, 21 disjoint changes); inspect post-merge **new exact branch HEAD** four GitHub Actions jobs, not cancelled predecessor runs. Keep PR #465 DRAFT; new upstream F3 GPU-off producer/history is source-only and does not supply garment-worn model or Part3 paid authority.
