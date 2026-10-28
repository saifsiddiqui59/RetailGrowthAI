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

## Still blocked / must not run
1. Independently read Azure manifest and actual account/share/secure environment storage configuration; upstream revision commit IDs and model readback via Azure OIDC. Current branch has **no cloud Azure CLI session**.
2. Source-pin official FLUX T2I + image-editing and Wan TI2V T2V/I2V API workflows; review pinned Python/CUDA/Torch/ComfyUI and OCI image digest, license/attribution, file-format and CPU JSON validation. No GPU-inference proof exists.
3. Coordinator review of environment storage read-only binding, networking, safe Manual JOB manifest, durable shop media/ledger lease, exact approved A100 runtime rate, single-test **all-in** spending cap and termination. A100 quota alone is not price or deployed instance.
4. Real model image/video acceptance is **separately user-paid-approved**. No unconditional paid start or Azure creation; no automatic retry, no public ingress, one concurrent execution, pinned image and bounded timeout.
5. Do not merge this stacked Feature5 draft PR without its underlying #323 branch and coordinator contract/CI review; coordinator alone updates `docs/PROJECT_STATE.md`, `NEXT_TASK.md`, `WORK_LOG.md`, `DECISIONS.md` and `.github/workflows/**` after final integration. Do not touch WineShopPOS.
