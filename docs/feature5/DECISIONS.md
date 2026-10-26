# Feature #5 isolated decisions

- Primary research/adapter candidate: Tencent **HunyuanVideo 1.5**, local official CLI with optional future Diffusers backend; never dynamically fetch unreviewed weights.
- Do not activate Tencent under the community license without commercial/legal and territory review; hosted Indian SaaS does **not** automatically imply unrestricted worldwide access.
- Keep previously implemented Alibaba Wan on Part3 integration branch as an alternative provider behind the coordinator's contract. No second live paid provider.
- 480p, 5-second, 24-fps bounded output profile is a conservative **proposed** profile; not asserted verified by actual inference. Dimensions/probe acceptance require real pinned-model test.
- Premium disabled at three gates: worker flag, license approval, GPU budget approval. Existing approval + quota reservation required in DB before claim. No browser/provider key exposure, no public inference endpoint, no LangGraph or new DB schema.
- Feature4 alone handles reliable offer text, brand logo, music, transitions and final export. Feature5 preserves original assets and indicates human quality review required.

## 2026-10-26 safety/interop addendum
- Tencent official CLI uses `--image_path` *only* for I2V; text mode must omit the parameter. `--video_length 121` at 24 fps targets five seconds, but exact output requires real inference validation.
- Default BF16 runner requires `torch.cuda.is_bf16_supported()`, at least 14 GiB of GPU memory, and a pinned local install. Do not assume the Central India T4 is sufficient merely because it offers 16 GB nominal VRAM; no silent fall back to FP32 (substantially different cost/memory).
- Treat unknown/late private Storage upload acknowledgments and completion fencing as `UNKNOWN`, never as refundable FAILED or a reason to repeat GPU inference.
- Exact existing private object convention `{shop}/renders/{job}/{lease}.mp4` in `retailgrowth-media`; invalid bucket, path, lease or private flag are not success. Never create a duplicate public media bucket.
- No new Azure Functions ingestion path, payment ledger, or final renderer: Part3 and coordinating Feature4 own those integrations.

## 2026-10-26 continued decisions
- Part3 draft Wan reservation SQL is incompatible with the Hunyuan profile. Stop at an injected adapter; coordinator must reconcile ONE premium ledger and versioned provider/model/cost schema before hosted activation.
- A Feature4-ready clip must have a matching audited VisualReview object bound to the exact stored media hash and reviewer tenant write permissions. A `quality_status=APPROVED` string alone is insufficient.
- Generation idempotency version `feature5-lease-v2` includes approved prompt SHA-256 and model seed to prevent stale campaign output reuse or accidental duplicate GPU spend.
- Tencent Hunyuan Community License is conditional and territory-limited. Runner now fails closed when explicit operator licensing, regions, hosted notices, rights and MAU context is absent. This does not replace licensed jurisdiction/terms review or authorize use in EU/UK/Korea.
- Initial paid GPU pilot remains gated on real account access, quota, approved geography/consent and bounded spend. Never claim mock video is Hunyuan output.

## Runtime budget hardening decision
- An enabled GPU job requires a `MotionSpendGuard` and existing service-only DB credit reservation covering **worst case** allowed GPU wall time, active A100/vCPU/RAM rates plus ancillary allowance, not merely a nonzero reserved value. Runner timeout must not exceed quote. If no guard/rates or insufficient allowance, fail before leasing/launch.
- Measured subprocess wall-time is included in output metadata only as an **estimate of model-related compute**, not as an Azure invoice. Worker must reconcile Azure startup, image pulls, network, storage and full bill before settling charge.
- On out-of-budget runtime or unclear DB write, enter `UNKNOWN` (or raise reconciliation-only status when persistence fails). Never transform unrecorded uncertain paid work into a refundable `FAILED`.

## 2026-10-26 source pin + visual evidence decision
- Pin official Tencent HunyuanVideo-1.5 `generate.py` from upstream commit `60783e704160023913bee78f0b47036d393d4dfa` by Git-object SHA1 blob `ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d`. SHA1 is Git's blob identity and cannot substitute for SHA256 checks of model weights/dependency provenance; pin still needs actual tested runtime and licensed source evidence.
- A cheap real FFmpeg-encoded 5-second MP4 fixture is appropriate to verify Feature5 machine media validation without pretending a text/image-to-video model ran. Do not treat it as cinematographic acceptance.
- Human visual QA will examine private PNG samples and contact sheet tied to the exact MP4 SHA256. Only tenant-authorized reviewer state stored in the existing service backend can later authorize Feature4; generated review sheets alone confer no right to publish.

## Hosted DB reality check — 2026-10-26
- Read-only inspection of dedicated RetailGrowthAI DEV subscription/usage/outbox catalog confirms the provider-aware premium ledger is **not deployed**. Existing quotas and outbox cannot store premium jobs in their present CHECKs. Never claim Part3/Feature5 live subscription ledger integration until coordinator migration and E2E prove it. Source-only adapter design remains intentionally backward-compatible and default-disabled.

## 2026-10-26 — Weight code integrity and retained real inference evidence
- A pinned `generate.py` Git blob is insufficient to approve GPU spend. **Require a complete enumerated SHA256 manifest of materialized clean source files and licensed model weight shards**, with independently reviewed top-level SHA256 passed into the runner. Reject extra/missing/modified files and symlinks before CUDA. Keep lock generation local/offline and exclusive so no silently overwritten prior candidate.
- A manifest file in the same download folder is not an independent trust root. The reviewed `approved_manifest_sha256` must be protected in separate operator configuration, and origin/model-license/dependency checks still require human/operator diligence.
- A manual GPU test that deletes the generated video cannot provide real human visual sign-off. Require a separately protected `RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT` and preserve the original MP4, side-by-side source reference for I2V, review frames and clip SHA256 with **PENDING_HUMAN_REVIEW** status only. Actual quality must be approved by a reviewer, never inferred from video codec/duration checks.

## 2026-10-26 — Cost-minimizing policy
- Default to **zero premium spend**. Prefer already deployed CPU FFmpeg for retailer-approved stock/images when no photorealistic model motion is required; stills must never be misrepresented as bespoke walking-model footage. A separate reviewed `MotionSpendGuard` full wall-time quote and explicit paid operator flag are required even to mark a premium job GPU-budget-eligible. Feature5-only selector is a **planning boundary**; Part3/Feature4 coordinator owns actual execution.
- Start of `HunyuanLocalRunner.run` constitutes **possibly billable** attempt even if code/model initialization fails before producing valid MP4. Any subsequent exception, time-limit failure or rejected output must be `UNKNOWN` rather than refundable FAILED; safe pre-inference invalid source may be FAILED. Existing DB reconciler must prove amount/credit disposition; never blindly retry.
- Do not acquire a paid A100 GPU in East US or transfer Indian retailer private media simply because Central India has only T4 in official serverless GPU support. Geographic consent, hardware compatibility, actual quota, licensing and capped commercial inference remain gates.

## 2026-10-26 — Authenticity and one-shot-only cost gate
- Do not present assistant-generated stills as Hunyuan video output. The sole acceptable Feature5 sample is a **real MP4 from pinned Tencent code and weight shards on CUDA**, with provenance, cost and ffprobe/visual evidence. User can choose theme freely; selected free-to-design red festive kurti luxury-boutique T2V to avoid sharing any retailer photos.
- Manual GPU harness must select **exactly one of text/image** per invocation and require a verified Azure pricing snapshot and operator dollar cap covering all allowed billable GPU/vCPU/RAM/ancillary time before launch. No budget config or GPU means no sample launch. Actual billing is separately reconciled; manual harness is not a subscription integration.
- A free community Hugging Face Space can illustrate what original Tencent weights do, but is **not our connected Feature5 runner or customer tenant media flow**. Keep exact provenance labels and third-party retention/usage distinctions.

## 2026-10-26 — Azure demo must be real, capped and explicitly authenticated
- Owner intent authorizes pursuing an Azure GPU canary, but does not itself supply an Azure login, GPU quota, Tencent licensed weights, or an exact enforceable bill cap. Fail closed before creating a paid resource; no false deployment claims.
- Use a single manual East US A100 candidate **for synthetic T2V only**, subject to permission/territory/weights/price approval; Central India serverless T4 should not be assumed to support this BF16 Hunyuan runner. Existing verified dedicated Central India DEV RG must remain isolated and ownership-tagged; do not touch PROD or WineShopPOS.
- Separate read-only Azure subscription/profile/quota inspection from paid provisioning. No code in Feature5 may mutate Azure without a reviewed coordinator deployment path. Capture real mp4, exact sha, visual review evidence and charged USD before claiming task completion.

## 2026-10-26 — Azure sign-in does not imply GPU quota
- Actual signed-in browser profile makes the dedicated DEV subscription and resource group visible, but East US A100 managed-environment quota has not been surfaced; a different portal blade showed no subscription rows in its current directory/filter context. Do not mislabel this as an Azure denial or user failure. Keep paid GPU creation disabled until exact quota, supplier model weights, accepted licensing and maximum bill are verified. Do not reuse the separate voice-project Container Apps environment.

## 2026-10-26 — Azure ARM notification is not a verified GPU deployment
- `CustomDeployment-20261026093554` showed **Deployment succeeded** in Azure Portal, but exact managed environment was not visible and operation/template details were not retrievable. Therefore mark **UNVERIFIED**, never retry automatically; use coordinator OIDC read-only ARM show/operations before creating anything.
- Azure **environment-level** Consumption NCA100 GPU quota is only observable after a supported v2 managed environment exists; subscription Quotas empty pre-environment is NOT a proof of zero quota. Allow a single empty Consumption/logging-none DEV environment via strict one-resource what-if, but not an actual GPU profile or job until confirmed availability and real capped spend.
- Azure Cloud Shell ephemeral browser input failed, and the portal browser tool exhausted its metered budget. Prefer existing repository DEV OIDC to execute coordinator-controlled audited ARM path instead of repeating unreliable GUI steps. User's desire for minimum cost remains controlling; no GPU execution or paid deployment was verified.

## 2026-10-26 — OIDC is a runner credential, not direct chat cloud access
Keep Azure authentication within reviewed GitHub Actions using existing `dev` federation, without access keys or TinyFish browser wallet usage. The current GitHub app supports source commits and Actions logs but **does not expose arbitrary `workflow_dispatch`**; do not claim direct session Azure control. Only the coordinator installs .github workflows and approves any actual ARM create. Feature5 can publish a read-only proposed YAML under its own docs and pass reviewed handoff. Owner does not need to re-enter Azure login credentials for normal OIDC workflows.

## 2026-10-26 — Actual Azure per-environment quota zero; no GPU spend before one-GPU allocation
- Azure's actual list-usages output on the newly provisioned tagged East US v2 managed environment is `ManagedEnvironmentConsumptionNCA100Gpus limit=0 used=0`. Earlier blank portal quota pages were due to the missing environment and are superseded by this live result. We will **not** misinterpret an empty Consumption environment as a deployed/operational A100 GPU, nor claim a genuine Hunyuan MP4.
- Use the **managed environment Quota** request path for **1** serverless NCA100 GPU (not a subscription NCA 100 dedicated quota). The official Microsoft documented path may auto approve or require Azure Support review; do not file a separate case without owner approval. Paying for a GPU remains explicitly gated by quota, real licensed weights, approved geography/data handling and exact cost ceiling. Existing empty environment must stay isolated; no WineShopPOS/voice/PROD changes.

## 2026-10-26 — Do not use fractional A10 below model minimum or over-vCPU quota
- For authentic HunyuanVideo 1.5, follow Tencent official >=14GB VRAM with offloading. Azure NVadsA10 v5 SKU sizes offer 4/8/12GB fractional GPU at 6/12/18 vCPU and first 24GB full GPU at 36vCPU. DEV subscription regional cap is 10 vCPUs in both Central India/East US (live OIDC), so neither the insufficient-memory low-tier options nor first memory-sufficient 36vCPU SKU should be deployed. A100 VM SKUs restricted. No speculative paid VM, no auto quota request; favor one serverless A100 managed-environment quota request to the already existing DEV environment. Retain zero-active-compute settings until approved.

## 2026-10-26 — Managed-environment quota submission and outside-GPU fallback
- Microsoft now documents environment-level serverless A100 quota increases through **existing Container Apps environment → Settings → Quota**; neither public GPU SKU listing nor the unrelated subscription dedicated GPU quota satisfies it. The exact environment already exists (OIDC #40347841764) and limit=0; no request was submitted or approved. No undocumented REST/write mutation through OIDC.
- A lower-priced third-party on-demand GPU is **evaluation-only** until account-specific provider geography, isolation, model licensing, upload policies, host RAM, real cost/termination and source/weight provenance are approved. Use synthetic T2V before any retailer media. Model 480p T2V requires the official 50-step configuration by default; its faster distilled I2V mode is not a substitute.
- External price quotes are separately SHA256-pinned and checked with a strict, read-only CPU module; the result deliberately says QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION. Python wall-time cannot terminate a rental provider instance or hard-cap the invoice. Never activate external GPU spending on quote-only output.
