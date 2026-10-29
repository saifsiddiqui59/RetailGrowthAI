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

## 2026-10-26 — A40 exact screening support
- A40 is included only as one BF16-capable, 48GB VRAM **provisional** candidate in SHA-locked price screening. Its $0.59/hr Runpod published Pod price is not guaranteed account capacity or a true provider-enforced ceiling. A 1-hour rental at $0.59/hr plus illustrative $0.02/hr storage and $0.05 reserve screens at $0.66, explicitly including provider termination, not just inference time.

## 2026-10-26 — Do not equate complete open-source engine with a deployed SaaS
- Reassess Feature5 with **official, runnable GitHub upstreams** rather than another paid video API: prioritize LTX-Video 13B v0.9.8 as **conditional** long-form/60s extension candidate, Part3 Wan2.2 as Apache-2.0 baseline, existing Hunyuan code preserved. ComfyUI offers an internal authoring/runtime engine but its GPL-3.0 and model licenses are separately reviewed. Azure-Samples ComfyUI H100 Terraform is a hardware-expensive example, not an approved deployment plan.
- No false claim that 60 seconds is generated in one cheap pass: recommended model operating windows are smaller, require continued model inference and continuity evaluation. Code and checkpoints have distinct licensing; LTX's 0.X weights have USD 10m revenue threshold and AI-disclosure/use restrictions.
- No change to final approved model/provider, paid GPU authorization, quota limit or cross-feature contracts without coordinator approval and verified CUDA quality/cost pilot.

## 2026-10-26 — Full upstream, not handwritten renderer
- Official whole-project GitHub path: Microsoft `Azure-Samples/comfyui-on-azure` launches full upstream ComfyUI plus models on a **single H100, 40-vCPU Azure VM**. Full A100 serverless alternative is a **new container deployment packaging** of upstream code, not a claim the unmodified H100 Terraform can run on ACA.
- Cost reference East US H100 $6.98/hr allocated versus A100 serverless GPU $0.000529/sec plus variable CPU/RAM ($2.4228/hr **illustrative** 4/16). Both account quota requests are blockers at the last verified Azure state; no cost-per-60s-video claim absent benchmarking.
- Preserve real upstream workflows/model quality; RetailGrowthAI code should be an auth, ledger, asset and review adapter, not a substitute video generator. Do not install/rent GPUs under undocumented billing or quota assumptions.

## 2026-10-28 — GPU provider procurement recommendation, not a paid activation
- For first original Wan2.2 proof under Indian domestic card billing, recommend **JarvisLabs India on-demand A100 80GB at published ₹140.94/hr**, rather than an unverified ₹32/hr community RTX 4090 listing or blocked Azure A100 quota 0. The A100 is not the cheapest hourly GPU, but verified 80GB capacity permits the full non-offload profile and avoids pre-approval Azure GPU capacity constraints.
- Official vendor: https://jarvislabs.ai/in (INR payment, Indian debit/credit via Stripe, GST; UPI support not confirmed). 100GB persistent storage adds published ₹1.30/hr even while paused; do not leave persistent instance indefinitely. A100 price and stock are estimates for planning until authenticated checkout.
- **This is a recommendation only**: No payment, VM, vendor access or GPU inferencing occurred. Use operator hard spend cap and no retries. Preserve original upstream generator, existing Feature5 Hunyuan branch, Part3 Wan owner and Azure/Supabase DEV PROD separation.

## 2026-10-28 — Capacity grant does not start paid GPU usage
- User-supplied Azure Portal environment Quota screenshot shows **A100 limit 2 used 0** in existing `rgai-f5-gpu-canary-eastus`. This supersedes previous capacity limit=0 noted in documentation, pending independent CLI readback. Quota is permission, not a paid reservation.
- Prefer actual original Wan2.2 model proof on **existing Azure serverless A100** now that capacity appears available, rather than buying external GPU access by default. Provision nothing billable until reviewed cost cap, private upstream image, model integrity/licensing, min replicas 0/max 1 and no-retry controls. No GPU charges at zero replicas; ancillary Azure services can bill separately.

## 2026-10-28 — Safe GPU lifecycle design
- First source-only ComfyUI + Wan2.2 5B pilot will use Azure **A100** Consumption (not V100) if explicitly provisioned and paid approval is separately granted. Prefer single **Manual Container Apps Job** with no automatic triggers/retries, one replica, <=1800s timeout and no public ingress over always-on ComfyUI. Read-only start preflight default, explicit double-gated paid start and emergency stop verify execution status. This is not a hard cost cap; all ancillary storage/ACR/network and independent triggers require separate accounting.


## 2026-10-28 — Wan2.2 native Comfy video codec, offline build and safety lock
- Official pinned ComfyUI commit 79cf64c21a1dba50749945ba9fe2e3a692f45438 in comfy_extras/nodes_video.py implements SaveVideo with a structured dynamic video codec, not an arbitrary string "auto" supplied to the optional codec argument. The Feature5 native graph now requests format {"format":"mp4","codec":{"codec":"h264"}} and no standalone codec-string widget. Accept real runtime only after checking independently obtained private /object_info; an offline generated object_info fixture is not evidence of a running server.
- Reuse the existing native Wan TI2V-5B model/ComfyUI graph and one trusted Feature4 renderer. No separate editor, renderer, paid prompt expander or media store.
- A fully pinned and commercially reviewed CUDA base OCI digest, every transitive wheel+SHA hash, full ComfyUI GPL redistribution obligations, Wan/model rights and exact runtime source commit are mandatory. The gated, source-only Containerfile has no default CUDA base and no bundled wheelhouse; it intentionally cannot build/deploy yet. Never silently use floating image tags, pip latest, upstream runtime dependencies or unapproved GPU.
- Read-only safetensors header parsing and local model stat can detect malformed files cheaply but do not establish a fresh full 34GB weight SHA256. Model weights and Azure Files environment binding remain GPU-OFF. Only independently reviewed runtime, license, quota and budget can open real inference.


## 2026-10-28 — Reproducible runtime cannot rely on declared hashes alone
- Approved source/OCI/wheel SHA values in JSON may be correct-shaped or identical to a mock and still not represent real bytes. Require an independently reviewed per-wheel manifest, stream actual immutable wheelhouse SHA-256, verify wheel WHEEL/METADATA version/name and reject symlink, unapproved extra and duplicate package aliases.
- Generate the complete deterministic pip --require-hashes requirements file from exactly that approved manifest and verify on-disk lock equality (no extra pip flags, URLs or index sources). The existing Containerfile remains no-index/offline, with no baked default base image; only owner-approved runtime build can advance.
- These offline CPU checks are necessary but insufficient: real CUDA/PyTorch compatibility, model checkpoint/GPL/license obligations, operator-reviewed base OCI digest and paid inference test remain separately gated; no GPU activation or client-controlled approval.


## 2026-10-28 — Pinned source, private scratch and no duplicate paid Comfy submissions
- A source commit marker is not an attestation of actual checked-out bytes. Require independent complete per-file SHA256 manifest and reject extra, missing, linked or changed Comfy source. Real reviewed all-wheel hashes and exact offline pip lock are independent and required before image build.
- Future rootless Comfy container must restrict I/O/temp/user staging to private 0700 paths, listen on 127.0.0.1 only, and disable MP4 embedded prompt metadata. Production lease isolation/cleanup requires actual runtime proof later.
- Official ComfyUI /prompt accepts a caller-supplied UUID but does not promise de-duplication. A single unknown paid POST must be reconciled with the EXISTING Part3 ledger; never resend based only on the same prompt ID. A successful history result does not imply authenticated private media receipt or human editorial approval.
- Canonical workflow alone cannot tell whether a permitted basename is actually approved; require independent current signed/DB authorized Feature3 private filename/source hash at point of dispatch. All new adapters are default OFF with injected callbacks pending coordinator-owned implementation.


## 2026-10-28 — Durable single paid Comfy intent and scoped private result
- ComfyUI POST /prompt accepts a caller UUID, but that is not server-side deduplication: after preflight/rights/creative checks, require existing transactional Part3 worker atomically record a unique one-attempt SUBMISSION_INTENT before POST. A boolean checked earlier and same-UUID retry are both insufficient. Fail closed if callback missing, stale, duplicate, or non-True; mark in-process dispatcher consumed regardless of POST outcome. Coordinator owns actual DB CAS and reconciliation.
- Private Comfy SaveVideo outputs are untrusted until existing tenant+job+attempt lease and exact 0700 attempt root are verified. Locate exactly one official numbered MP4 under approved rgai/feature5 prefix, reject symlinks/extra files/foreign directories, ffprobe real H264/704x1280/121f/24fps and decode five frames. This can only yield a PENDING receipt, never a verified AI origin, license/likeness rights or human approval. Actual private upload/settlement remains coordinator-owned.
- Cheap synthetic moving FFmpeg testsrc2 is allowed for GPU-OFF source tests but must never be represented as authentic Wan-produced person-wearing-garment video or true GPU/retailer acceptance.


## 2026-10-28 — GPU-OFF private output hardening and mock-to-media acceptance
- Pending native result receipts bind canonical job+attempt UUID, existing lineage, independently measured private MP4 SHA, and SHA256 of canonical pending metadata. This provides tamper evidence ONLY; no cryptographic signature or persistence, and never Feature4 auto-approval. Unknown/duplicate paid POST remains existing Part3 atomic submission-intent contract. Reject any foreign output directory including empty directories, and rehash result after FFmpeg screening; coordinator must verify accepted bytes again while persisting final immutable private object.


## 2026-10-28 — GPU-OFF source qualification and exact external gates

Source-readiness is NOT operational start approval. The attempt/job-bound pending receipt SHA256 is tamper-evident metadata only, not authenticated proof of user consent, durable DB state or one-use importer. Existing Part3 transaction must provide unique durable intent before any POST and verify current lease/bytes before signed immutable private import; unknown POST is NEVER automatically retried. Real remaining gates: independently license-review complete vendored ComfyUI/CUDA source, actual model/wheel SHA-256 and immutable OCI runtime plus approved build/registry charges; protected real /object_info and model mount/ABI; coordinator-owned existing Part3 unique intent, signed current F3 tenant rights and leased job claim, billing reconciliation and immutable hash-rechecked private importer with signed DEV negatives; owner-authorized one cost-capped A100 5-second Wan inference, observed stop and bill; human garment/likeness review; Feature4 final 1080x1920 assembly; coordinator PR integration/hosted acceptance. A100 and paid APIs remain OFF.


## 2026-10-28 — Coordinated eight-task security and public-media QA continuation

Safety requirement strengthened: a callback may commit a durable SUBMISSION_INTENT then lose acknowledgement; label UNKNOWN and never retry, rather than assuming no paid intent. Read-only cross-worker reconciliation is permitted only with independent current Part3 durable tenant/job/attempt authority, and is never a second submission path. Feature3 rights are rechecked after node preflight/before CAS, and output lease again after probe. Comfy MP4s must be 0600 with exactly one hard link and parent 0700, and Containerfile must enforce umask 077. Pexels stock page availability and general commercial media license do NOT prove individual model release, customer endorsement, product ownership, source lineage or clothing match. Hosted RLS metadata alone is not signed tenant negative acceptance. The exact latest source prior to this documentation commit is d747b6b9d622baba9198f80dcf81a9a2f14235f0; run final four GitHub CI jobs again on the documentation commit before claiming current-head success. Earlier independent 858e5e598d6348fb2849c7497550d109d7660a7f run #40747182176 was 4/4 SUCCESS. A100 and paid API use remain OFF; no actual Pexels bytes, Wan inference or WineShopPOS change.


## 2026-10-28 — Continued fail-closed source sprint after previous green CI

One Comfy dispatcher can start at most one attempt even under local concurrent invocations; Part3 transactional CAS is still mandatory across workers. Reused mutable reference approvals cannot be trusted across GET /object_info; compare against a snapshot. After durable submission intent, missing/revoked/changed Feature3 grant is UNKNOWN consumed, never safe for automatic POST replay. Comfy /prompt ack must have expected canonical UUID and a nonnegative integer queue number. Local /history requires the actual issued receipt object; other workers require independently authenticated read-only reconciliation. Parse F4 receipt UUIDs/tenant/rights/path before trusted settlement lookup.


## 2026-10-28 — Parallel/timeout negative proof

Parallel callers to the same local Comfy dispatcher must never start a second POST. If the post-intent F3 rights reader times out or errors, treat committed intent as UNKNOWN/consumed, never implicitly safe to repeat. Cross-worker uniqueness continues to require existing Part3 atomic CAS.


## 2026-10-28 — Stock media decoded-frame screening continuation

Technical FFmpeg movement detection is only a low-cost diagnostic: two decoded frames with differences can show non-frozen footage but never authenticate human motion, retail garment consistency, likeness, right-to-publish or production-grade output. Hash/inode checks constrain tamper during local stock inspection, not grant a customer license.


## 2026-10-28 — Image-generation A100-free source qualification

Owner requested image generation without A100. Preserve GPU OFF. Official Black Forest Labs FLUX.2 Klein 4B is Apache-2.0, smaller consumer GPU capable (official model listing ~8.4GB model VRAM, support guide ~13GB working VRAM), **not A100-exclusive**. Feature3 owns actual model deployment, sourcing licensing and runway/cost. Feature5's PIL CPU review composite is a deterministic image processing artifact, MUST NOT be described as FLUX generative AI, virtual try-on, realistic garment/likeness fidelity or approved promotion. Need real model and independently authorized host before enabling AI image inference.


## 2026-10-28 — Part3 native private import GPU-OFF acceptance

Prioritize immutable at-most-once import: a trusted Part3 service-only SQL CAS must commit unique intent before any potentially successful private write. All post-intent uncertainty is `UnknownPart3PrivateImport` requiring independent object/ledger reconciliation; no refund, replay or manual false success. Existing media bucket `retailgrowth-media` and private path convention are mandatory. Source test fake session is not a signed Supabase JWT and synthetic human review is never legal/quality approval.


## 2026-10-28 — Import intent ambiguous ACK + private staging path guards

An import-intent CAS callback may commit then time out, so any raised exception is `UNKNOWN` (no new commit/upload/replay), never normal retryable preflight. Before CAS, private paths must be contained within dedicated 0700 worker root, with safe intermediate parents. Do not substitute browser signed URLs for trusted file paths.


## 2026-10-28 — Two-shop parallel offline acceptance and Pexels rights audit

Simulated test-user logins use an explicitly isolated per-test HMAC secret and never correspond to Supabase Auth JWT. Parallel test CAS lock proves adapter's expected interface only; production must use SQL unique + transaction fencing across processes. Pexels pages license free modifications but no implied endorsement; API AI training/evaluation dataset extraction is restricted, so test local media technical decoding rather than model training datasets.


## 2026-10-28 — Pinned official Wan2.2 weight source inventory

Official Wan2.2 upstream Apache-2.0 and ComfyUI 5B file-name/license inventory do not establish installed artifact byte provenance. Leave reviewed weight SHA, workflow SHA and OCI SHA `null` until independently attested; do not turn false gates true on the strength of CPU test mocks. Actual publisher/user consent remains independent.


## 2026-10-28 — Current Feature3 / Feature4 / Part3 real source contract audit

Cross-feature Feature3 consumer packet is metadata-only and `provider_call_permitted=false`. At the F5 boundary the current server-side packet must be re-fetched and matched, source ID/revisions/fingerprints and F2/F4 timeline checked. This qualification does not itself approve any GPU call or commercial media. Feature4 Hunyuan 1.5 480p and Part3 Wan2.7 720P/1080P cannot be silently changed to F5 Wan2.2 704×1280/121frame 24fps; reject wrong model and seek versioned coordinator schema reconciliation.


## 2026-10-28 — F3 verified consumer-to-private first-frame staging + hosted catalog reality

- 2026-10-28: Added real F3 consumer packet + private first-frame CPU staging connector and revocation-safe follow-up read. This uses F3's genuine contract shape, while tests use synthetic F3 current readers on old F5 branch. Connected Supabase read-only inventory: F3 model tables deployed with 0 records, Part3 premium jobs table not deployed. No writes, no hosted JWT, no GPU or paid provider.


## 2026-10-28 — Deterministic fake token corruption regression fix

Fake test HMAC token tampering MUST be demonstrably different from original. A randomized last-character replacement might reproduce the original value and cause nondeterministic false rejection of a valid token; switch deterministically to a different character before asserting denial. Keep the test enabled.


## 2026-10-28 — Current main real F3 producer source integration

Use real producer code from main through a fast-forward-safe, two-parent Git merge after compare verified no overlapping changed files. Never duplicate a Feature3 consumer module in Feature5. CPU test fixture can call genuine Feature3 code but mocked rights are NOT commercial consent/true original licensed garment. Real production authorization must be independently proven by signed tenant reader.


## 2026-10-28 — F3→CPU motion→Part3→F4 continuous offline acceptance

An end-to-end local 121-frame 704×1280 CPU camera zoom/pan on one Feature3 still can validate transfer integrity, not Wan2.2 generative motion, correct garment try-on or person walking. A test-only positive Feature4 reviewer is a contract shape assertion and MUST NOT be used in production. The original private reference must be cleaned after use; only a test storage object remains. Continue zero spend.

## 2026-10-28 — Validate media bytes across external Part3 callback boundaries

An existing server-side rights/claim callback is not a filesystem lock. Feature5 must recheck absolute private path containment, file permissions/link identity, metadata and SHA **after** that callback, before durable unique import intent, and once again **after** committing the intent but before Storage upload. Pre-intent drift is denied without new storage/billing action; post-intent drift is an ambiguous consumed intent and is NEVER automatically reprocessed or refunded. Existing Part3 transactional reservation and authoritative signed tenant checks remain mandatory; local mock callbacks cannot attest them. GPU/A100 stays OFF.

## 2026-10-29 — Do not settle a premium video job from the private upload ACK alone

A no-overwrite Storage upload acknowledgement is untrusted evidence of *actual* retained bytes. Feature5 therefore requires a **second, service-only** streamed read of the exact tenant-scoped job/attempt private object, bounded to the validated FFmpeg native media length and exact SHA256, before accepting the trusted Part3 fenced transaction settlement callback. Readback is mandatory, not optional; missing or mismatched bytes after durable import intent are UNKNOWN/CONSUMED with no automatic retry/refund. Readback callback MUST be bound by coordinator to active DB lease, tenant, rights and private Storage; Feature5 test callbacks are not signed Supabase claims. No new queue/wallet/schema or model substitute, no A100.

## 2026-10-29 — Accept F3 private worker API without copying ownership

Consume Feature3's actual source-owned `materialize_feature5_input` via dependency-injected trusted callback *only after* coordinator source integration. Feature5's local adapter must reject extra/unexpected fields or a changed `shop_id`, `first_frame_asset_id`, `reference_fingerprint`, binary SHA/MIME/dimensions or non-FALSE paid/GPU/publishing flags; never treat a public OpenVTO demo input or F3's source bytes as approval for generation, marketing, source likeness or a valid Part3 paid claim. Preserve existing aspect-ratio letterbox, second packet freshness check and private ephemeral cleanup. Existing F3 `resolve_first_frame` integration is retained for backwards compatibility. No migrations/shared contracts or real GPU calls.

## 2026-10-29 — Real Feature3 source merge, silent native motion and strict external gating

Bring upstream Feature3 worker-input code via a verified zero-path-overlap merge from coordinator `main` (two actual Git parents), never copy source modules or fork shared media/ledger functions. Run the exact merged F3 `materialize_feature5_input` function in F5 CPU-only acceptance and bind to current approved same-shop reference IDs/revisions/fingerprint and actual private byte hashes. The returned `provider_call_permitted=False`, `gpu_authorized=False` and `publish_approved=False` are authoritative **denial** states and cannot be promoted by F5 or an external stock asset. Native five-second Wan validation requires one silent H.264 video stream; any extra audio, subtitle, data or multiple video stream must fail before storing/reviewing it. Feature4 owns licensed voice/music separately. This is offline implementation, not permission for actual paid inference, rights approval, or source-completed service.

## 2026-10-29 — Bind all private fashion originals and distrust caller-supplied MP4 probe evidence

Feature5 may consume the newly main-merged Feature3 `resolve_private_worker_inputs` only as a trusted dependency-injected server function under current authoritative job claim/readers, never copy its implementation or expose binary bytes/URLs to browser. Independently compare all three image originals against expected immutable garment/model/reviewed first-frame identity+SHA and deny client-shaped extra fields, revoked source and any GPU/publish entitlement. Preserve existing ephemeral 0700/0600 preparation and repeated packet freshness check.

The Part3 importer must independently **FFprobe the real exact native private file** after current claim/rights, before single-use import CAS; a `NativeClipInspection` dataclass can be fabricated, even if its SHA matches arbitrary bytes. Deny forged dimensions/FPS/frame count/duration/codec and all additional media streams; post-CAS failures remain consumed UNKNOWN without retry/refund. This does not authenticate model origin or human rights. No new shared DB/queue/API/migration, paid GPU/cloud, and no changes to WineShopPOS.

## 2026-10-29 — Full local weight hash before live runtime, immutable reviewer fields

Keep native Wan2.2 TI2V-5B source pinned to actual verified official Wan-Video commit `1ea34ff48f87168174e12956e200b1d908b1c5ff`, ComfyUI commit `79cf64c21a1dba50749945ba9fe2e3a692f45438`, and immutable Comfy-repackaged weight identities. Original official Wan CLI checkpoint layout is NOT interchangeable with Comfy repackaged three-file layout. A passed file header/metadata/Azure Files uploader receipt does not prove installed bytes; require an explicit full SHA of all three mounted originals under an operator-supplied independently reviewed six-file provenance manifest. A matched SHA alone does not assert CUDA runtime integrity, rights, model quality, copyright acceptance, verified ReadOnly mount semantics or GPU start. Never run a new paid instance solely for a read-only audit without separately approved budget. ComfyUI GPLv3, Wan2.2/model Apache-2.0, NVIDIA CUDA and all wheel/native dependencies require independent redistribution/use review.

Reviewer `VisualReview` is frozen **including** its boolean checklist: copy into MappingProxyType so post-creation input dict mutation, changing APPROVED→REJECTED criteria or accidental dataclasses.replace reconstruction cannot silently mutate a signed decision. Preserve strict 11-field bool coverage, matching shop/clip SHA, human role, explicit disclosure and separate real human approval before F4. No simulated reviewer, FFmpeg media or MIT demonstration is real garment fidelity or marketing consent. No DB/shared interfaces/PROD/WineShopPOS changes.

## 2026-10-29 — Use existing verified Feature3 demo photography NOW, never call it a try-on

When the owner directs Feature5 to consume Feature3's garment/model images, reuse **the already pinned actual source** instead of demanding new source fixtures or using image placeholders. Pin Git original OpenVTO MIT SHA1 identities `72a86a60280976ce5c73db9525d9648b54d1126a` for fictional model pose, `878fde8857f58862723f85d7f8bd723c65a8e498` for separate apparel and include exact MIT notice. For stable no-network CI use F5-only original-byte offline fixture and invoke authentic Feature3 image/manifest validators, not duplicate its rights engine. Convert the *model pose only* to 704x1280 test PNG without altering garment fit; keep garment as a separate immutable source ref, verify both and never claim the model is wearing that SKU. Constructing a native Wan graph is a zero-GPU technical acceptance only, not permission for inference, customer publishing, tenant-specific claims or commercial output. All paid/approved Feature5 paths still require real authoritative Feature3 same-shop private worker grant, leased Part3 job, checked actual try-on and independent reviewer approvals.

## 2026-10-29 — Distinguish actual test photo pixels, technical FFmpeg motion and true Wan/video authorization

Reuse real pinned Feature3 OpenVTO MIT originals for independent CPU media acceptance rather than placeholders: actual model-pose JPEG *and separate* shirt JPEG, each verified by authoritative upstream Git SHA and Feature3's own image gate. `feature3_mit_demo_input.py` remains offline-only; new full-path test may use real FFmpeg zoom/pan and in-process Part3 fake Storage/lease only to validate codec, immutable SHA, imported private object and denial behavior. This must NEVER be presented as genuine Wan animation, virtual try-on, a clothing model wearing the SKU, actual customer license/consent or a production entitlement. Authoritative trusted Feature3 private-worker lease/rights grant and independently approved wearer frame remain mandatory before paid inference. F3 #630's future demo-only byte packet is not a way to lift these flags. Do not merge or duplicate Feature2/3/4/Part3 ownership or pretend current drafts already provide live JWT/grants.


## 2026-10-29 — Editorial draft integrity is not spend authority

The Feature2 `retailgrowth.feature2-f4-f5-offline-fixture.v1` is consumed by a new F5-only *read-only* 15/30/60s continuity gate, versioned as `retailgrowth.feature5-f2-offline-qualified.v1`. Preserve verbatim original F2 direction and independent matching F4 timeline prompt hash; never rewrite source text in Feature5. Whole-packet SHA-256 and original prompt SHA-256 detect local drift but are NOT signatures, merchant grants, current rights checks or credit reservations. The return contract explicitly forbids provider submission, release and Feature4 publishing. No parallel billing/database schema, unmerged Feature2 source copy, new paid runtime or shared interface edit.
