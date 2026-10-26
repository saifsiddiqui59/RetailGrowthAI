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
