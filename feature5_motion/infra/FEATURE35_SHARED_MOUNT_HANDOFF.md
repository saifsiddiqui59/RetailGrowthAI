# Feature3 + Feature5 shared ComfyUI mount — GPU-OFF integration handoff
2026-10-28 | Feature5 draft PR #465 | SOURCE ONLY, not an Azure deployment

## Evidence and immutable constraints
- Existing storage: East US `rg-retailgrowth-dev/rgaimodelseastus26`, StorageV2 Standard_LRS, classic SMB Cool LRS `retailgrowth-models`, quota 64 GiB. Separate Central India storage untouched.
- Successful **real** main workflow 40666975458 (GitHub head ea73e357) verified six exact source SHA-256s and Azure file metadata/readback; total 34,277,265,757 bytes. Digests and lengths are in `shared_model_mount.py`. No GPU was started by this run.
- The **private** Azure `models-sha256-manifest.json` was written by the staging script but has NOT been independently opened/read by this branch. Its three distinct Hugging Face repository revisions remain unverified here. Do not substitute the example fixture or metadata for a fresh authenticated Azure readback.
- The existing A100 managed environment `rgai-f5-gpu-canary-eastus` is not a deployed or billed GPU execution. The specific job `rgai-f5-wan22-a100-canary` is NOT established as existing.
- PR #323 (Feature5 provider) and stacked PR #465 (A100 safe controls) are both OPEN/DRAFT at this checkpoint. Never claim the proposed controls are deployed or that ComfyUI has produced actual images/videos.

## One-share, read-only mounting plan — NOT EXECUTED
Microsoft docs: https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts
and https://learn.microsoft.com/en-us/rest/api/resource-manager/containerapps/jobs/get .

1. Do not create another storage account/share or copy weights. With a separately approved, reviewed operator change, create **one** environment storage definition named `rgai-models-readonly`, `storageType=AzureFile` (classic SMB), `accessMode=ReadOnly`, account `rgaimodelseastus26`, share `retailgrowth-models`. Authorize its secret/key through protected Azure infrastructure settings or use environment managed identity **only if supported for the actual environment and role is correctly provisioned**. Never commit storage keys, SAS, or credentials.
2. In the future **Manual** Azure Container Apps JOB template, define `properties.template.volumes: [{name: retailgrowth-models-volume, storageType: AzureFile, storageName: rgai-models-readonly}]`; container `volumeMounts: [{volumeName: retailgrowth-models-volume, mountPath: /mnt/retailgrowth-models}]`. Follow the specific JOB API schema, not a Container App revision YAML blindly. No extra GPU deployment here. The helper `job_volume_fragment()` is illustrative and intentionally not a full runnable ARM deployment.
3. ComfyUI can discover checkpoints without copying them by passing `--extra-model-paths-config feature5_motion/infra/extra_model_paths.feature35.yaml` in an *approved, pinned* image. It maps the same share's `feature3/diffusion_models,text_encoders,vae` and `feature5/diffusion_models,text_encoders,vae`. Do not mix the mismatched feature text encoders/VAEs.
4. Keep application outputs **outside** this read-only mount; use existing private tenant media pipeline. Do not make model share public or use it for tenant uploads. Network access, port 445, and actual mount capability need authenticated Azure preflight. Bind changes are coordinator-owned and may have incidental paid storage/network implications.

## GPU-off manifest and model preflight
Run from repository root on CPU, with no Azure credentials required:
```bash
python -m unittest discover -s tests/ai -p 'test_feature5_shared_model_mount.py' -v
python -m feature5_motion.shared_model_mount --format yaml
python -m feature5_motion.shared_model_mount --format plan
```
Only after a separately approved **read-only** retrieval of the private Azure manifest:
```bash
python -m feature5_motion.shared_model_mount --manifest /PRIVATE/LOCAL/models-sha256-manifest.json
```
Optional **stat-only** check on a mounted volume uses `--mounted-root /mnt/retailgrowth-models`. It checks names and exact byte sizes, not full SHA-256 over 34GB. The uploaded files' checksums were validated by staging run 40666975458; a new byte-level audit is a separate explicit action due to I/O/transaction cost.

## Workflow and licensing
- ComfyUI upstream review pin in #465: `79cf64c21a1dba50749945ba9fe2e3a692f45438`. Official Wan 5B workflow source review pin: `e7cd011d4ded3411c2f481200544f0be6fdc962e`. These are documented **source pins**, not a built image digest or a tested requirements lock.
- Feature3: FLUX.2 [klein] 4B distilled model with Qwen3-4B encoder and `flux2-vae`. The original BFL 4B is Apache-2.0 commercially usable; verify all bundled model/encoder/ComfyUI dependency notices for actual distribution. https://help.bfl.ai/articles/7108141705-can-i-run-or-fine-tune-flux-2-klein-locally and https://docs.comfy.org/tutorials/flux/flux-2-klein .
- Feature5: Wan2.2 TI2V-5B fp16, UMT5 XXL FP8, Wan2.2 VAE. Official hybrid 5B supports T2V and I2V. Original Wan2.2 TI2V 5B model card uses Apache-2.0; downstream components and input/outputs still need actual commercial/consent and content review. https://docs.comfy.org/tutorials/video/wan/wan2_2 .
- Official ComfyUI workflow templates MUST be downloaded and pinned as reviewed **CPU-only source** under coordinator scope before an image is built. The `retailer_t2v_i2v_preflight.example.json` is an illustrative requirements fixture, **not a ComfyUI API workflow or generated video**. Scripts must not silently install community custom nodes, latest Python/Torch/CUDA or fetch weights at runtime.
- A minimal canary will generate one genuine 5-second / 24 fps source clip, then human-check hands/face/garment and hand to Feature4 for **accurate text/logo/approved soundtrack overlays**. Feature2 owns script; Feature3 owns approved reference PNG; Feature4 final render; Feature5 generates temporal motion.


## Explicit protected read-only audit, prepared but NOT EXECUTED
`feature5_motion/audit_shared_model_share_readonly.py` uses the Azure Files SDK to
read at most 64 KiB for the **one** private completion JSON and GET file
**properties only** for the six checkpoints. It compares complete/size/SHA-256
metadata and each stored Hugging Face revision against the original manifest.
It never opens/downstreams weight bytes, changes Azure settings, creates files,
starts a job, or spends GPU time. Ordinary unit tests run with all Azure calls
mocked. Azure Files metadata transactions are not necessarily free.

```bash
# Default is safely offline: no account access needed.
python -m feature5_motion.audit_shared_model_share_readonly

# Documentation only; run from authenticated approved DEV operator context
# with a transient masked key, NEVER with a key committed to GitHub.
# python -m feature5_motion.audit_shared_model_share_readonly --audit-existing-share
```

**The live private manifest and revisions have NOT been independently read yet.**
Running source tests only establishes audit logic, not current Azure reality.

## Additional PAID-START fail-closed cost gate, prepared not activated
Even after manually acknowledging paid run and the existing model-license/approval flags,
`gpu_job_control.py` now refuses to start without a referenced, independently
reviewed USD quote: `RETAIL_F5_COST_QUOTE_CURRENCY=USD`,
`RETAIL_F5_COST_QUOTE_REFERENCE`,
`RETAIL_F5_QUOTED_ALL_IN_USD_PER_GPU_SECOND`,
`RETAIL_F5_QUOTED_FIXED_OVERHEAD_USD`,
`RETAIL_F5_OWNER_APPROVED_PER_TEST_MAX_USD`.
It checks `replicaTimeout * quoted_rate + fixed_overhead <= approved_max` with
finite Decimal inputs. These fields are **unset and not approved** at this time;
test fixtures use fictional numbers and are NOT an Azure retail quote. This check
is operator admission control, NOT a hard Azure financial cap. It cannot prevent
separate starts or unexpected bills, so lease/one-execution/status/stop and
actual invoice checks still apply. NEVER set fabricated quote environment values
to force a run.

## Additional verified upstream native workflow inspection
Read-only source inspection at pinned official Comfy-Org/workflow_templates commit `e7cd011d4ded3411c2f481200544f0be6fdc962e`:
- Wan UI workflow `templates/video_wan2_2_5B_ti2v.json` has 13 nodes with `UNETLoader`, `CLIPLoader`, `VAELoader`, `Wan22ImageToVideoLatent`, `KSampler`, `VAEDecode`, `CreateVideo`, and `SaveVideo`. Loader filenames **exactly** match the three stored Wan files. It defaults to 1280x704 and 121 frames at 24fps (~5s) with an image input; T2V requires correct optional start-image handling and a reviewed ComfyUI API-format graph, not merely removing a file from JSON by guess.
- FLUX 4B edit UI workflow `templates/image_flux2_klein_image_edit_4b_distilled.json` references **`flux-2-klein-4b-fp8.safetensors`**, not the staged `flux-2-klein-4b.safetensors`. The official example uses saved subgraph node IDs and is NOT ready to submit to the headless ComfyUI API as-is. Preserve the existing 7.75 GB checkpoint and review loader/precision widget overrides and upstream subgraph compatibility *offline* rather than downloading replacement weights or pretending it works.
- FLUX text-to-image `templates/image_flux2_klein_text_to_image.json` uses embedded native subgraph nodes instead of a simple top-level UNETLoader; its actual inner model references need inspection/normalization before using the staged checkpoint.
- These are verified **source template observations**, not CUDA inference or a license attestation. All three workflows remain unexecuted, and image/build dependencies remain unpinned.

## Still blocked / must not run
1. Independently read Azure manifest and actual account/share/secure environment storage configuration; upstream revision commit IDs and model readback via Azure OIDC. Current branch has **no cloud Azure CLI session**.
2. Source-pin official FLUX T2I + image-editing and Wan TI2V T2V/I2V API workflows; review pinned Python/CUDA/Torch/ComfyUI and OCI image digest, license/attribution, file-format and CPU JSON validation. No GPU-inference proof exists.
3. Coordinator review of environment storage read-only binding, networking, safe Manual JOB manifest, durable shop media/ledger lease, exact approved A100 runtime rate, single-test **all-in** spending cap and termination. A100 quota alone is not price or deployed instance.
4. Real model image/video acceptance is **separately user-paid-approved**. No unconditional paid start or Azure creation; no automatic retry, no public ingress, one concurrent execution, pinned image and bounded timeout.
5. Do not merge this stacked Feature5 draft PR without its underlying #323 branch and coordinator contract/CI review; coordinator alone updates `docs/PROJECT_STATE.md`, `NEXT_TASK.md`, `WORK_LOG.md`, `DECISIONS.md` and `.github/workflows/**` after final integration. Do not touch WineShopPOS.

## 2026-10-28 verified deployment update after independent DEV OIDC
- Private Azure Files manifest: [main-run #40676023863](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40676023863) **SUCCESS**, all six exact bytes/SHA metadata/complete fields and three source revisions independently read using protected OIDC. The original uploaded weights were not rehashed again.
- Single existing model share ReadOnly environment binding **actually registered and read back** under `rgai-f5-gpu-canary-eastus`: [protected #40677739766](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40677739766) SUCCESS; fix #506 merged. The binding is not yet a successfully mounted volume in a running container.
- Named manual A100 GPU job was **absent** in the preceding signed audit; the entire group returned no jobs then. The binding run did not create a job or start GPU. No subsequent full-resource GPU billing inventory is claimed here.
- Published verified East US A100 serverless GPU rate `USD 0.000529/sec`, active CPU `USD 0.000024/vCPU-sec`, active RAM `USD 0.000003/GiB-sec`; this is not the user's account invoice or approved all-in price. Runtime & money approval remains unset.
- Additional launch safety: even a correctly formatted immutable job image is **not** sufficient; execution now requires `RETAIL_F5_REVIEWED_RUNTIME_IMAGE` to EXACTLY equal the reviewed `registry/image@sha256:<64 hex>` of the actual deployed job. Missing/other hash and tags such as `latest` fail closed independently of manual paid approval, runtime/tenant eligibility and spend quote. This is a source-only gate; NO actual pinned image was built or supplied by us.
- Model licensing: the FLUX.2 Klein 4B/Qwen3/Wan 5B model licenses require their exact dependency/source notices; ComfyUI itself is GPL-3.0. Commercial SaaS is not necessarily forbidden, but distribution/source obligations must be professionally reviewed before release. Do not mark rights approved or generate with unapproved customer photographs.
- The still-open source PRs #323 (Feature5 runtime) and stacked draft #465 remain integration/QA-gated; preserve part owner scope and coordinator files. No WineShopPOS/PROD changes.

## 2026-10-30 — Feature5 F5-14 full original-byte readback source (GPU OFF)

- Added an **explicit operator-only** `verify_mounted_sha256(root)` to `feature5_motion/shared_model_mount.py`. It opens each pinned file through no-follow directory descriptors, refuses symlinked parent components and nonregular/wrong-sized files, streams at most 4 MiB per read, checks stable file identity/size/timestamps and compares the full SHA-256 against the six pinned staging digests. No cloud APIs, model downloads, inference or write operations are in this function.
- A full share scan reads **34,277,265,757 bytes** and can incur remote Azure Files I/O/transaction costs. It is **never automatic**; the CLI requires all of `--mounted-root /mnt/retailgrowth-models --verify-sha256 --confirm-full-scan`. Do not invoke against Azure without separate operator cost/permission approval. Existing default `--mounted-root` remains a cheap metadata-only check.
- Added CPU-only tiny-local-file tests for successful digest readback, same-size tampering, symlinked ancestor denial and the two required explicit CLI flags. These tests use no genuine model weights and are **not** evidence of actual mounted checkpoint integrity.
- **F5-14 stays IN PROGRESS:** no full 34GB readback was performed, no protected running container mount was accessed, and there is no runtime ABI/licensing approval. F5-13 OCI digest/SBOM, F5-15 protected ComfyUI node inventory, F5-16 paid authorization and F5-17 genuine Wan inference remain independently gated. This branch is a source-only review proposal; the coordinator alone integrates and updates canonical shared status.
