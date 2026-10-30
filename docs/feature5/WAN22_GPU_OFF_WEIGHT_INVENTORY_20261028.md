# Feature #5 — Wan2.2 weights and immutable CUDA image: GPU-OFF source inventory

**As of 2026-10-28: original upstream source names/LICENSE VERIFIED from authoritative published pages; downloaded weights, their actual SHA256, installed CUDA image and a running GPU are NOT verified. GPU OFF.**

## Independently identified model artifacts

Reference: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/tree/main and Apache-2.0 license at https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B (upstream official repository is ~34.2 GB with three diffusion shards plus original VAE/T5 dependencies).

Feature5's *chosen ComfyUI repackaged version* is a **different artifact layout**; no mixture with upstream raw checkpoints or substitutions is allowed without a reviewed loader profile. Exact official ComfyUI example: https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_wan2_2_5B_ti2v.json and ComfyUI docs https://docs.comfy.org/tutorials/video/wan/wan2_2.

| Required Comfy native 5B file | Expected install directory | Source-page approximate size | Actual private bytes verified |
|---|---|---:|---|
| `wan2.2_ti2v_5B_fp16.safetensors` | `models/diffusion_models/` | 9.31 GB | **NO** |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `models/text_encoders/` | 6.27 GB | **NO** |
| `wan2.2_vae.safetensors` | `models/vae/` | 1.31 GB | **NO** |

ComfyUI workflow also requires pinned source commit `79cf64c21a1dba50749945ba9fe2e3a692f45438`, official workflow commit `e7cd011d4ded3411c2f481200544f0be6fdc962e` and independent exact workflow SHA256. Existing native source adapter pins Wan upstream commit `1ea34ff48f87168174e12956e200b1d908b1c5ff`. **Git SHA and upstream web information are not SHA256 attestations of downloaded model files.**

## Already implemented GPU-OFF checks

- `feature5_motion/infra/wan22_build_context_gate.py`: **real local bytes only** source checkout + independent approved manifest, hashed offline wheelhouse, immutable OCI SHA, offline requirements lock (rejects missing inputs).
- `feature5_motion/infra/wan22_native_preflight.py`: pinned node input shape and fixed model workflow checks. A live `/object_info` response is needed *from the actual private installed runtime*, not a test double.
- `feature5_motion/infra/Containerfile.wan22.REVIEW_REQUIRED`: intentionally non-buildable without approved private vendored source, hashed wheelhouse, immutable CUDA base. It does not download GPU/model files in build steps.
- `feature5_motion/infra/comfyui_wan22_deployment_manifest.example.json`: deliberately `null` workflow/model/image SHA and false license/cost/start fields. **Do not populate with invented hashes.**
- `feature5_motion/gpu_job_control.py` + `start_a100.sh`: dry-run/disabled gates; no Azure environment or job resource created.
- `feature5_motion/part3_private_import_bridge.py`: output can be privately imported only after trusted claim, rights, UNIQUE DB intent, upload SHA, live lease/source recheck, exact authoritative reservation settlement, and separate human review for Feature4. None of these mean a model ran in synthetic tests.

## Required proof before saying CUDA/model runtime is verified

Obtain an exact operator-reviewed **independent SHA256** for each of the three downloaded model files plus all installed Python wheels/dependencies; audited copyright and redistributable commercial SaaS model/Comfy terms; audited pinned CUDA container base `@sha256` and transitive lock; approved location and tenant data region; live private `/object_info` response matching native graph; one bounded cost-controlled genuine inference + private media hash/ffprobe/human fidelity evidence.

With no these byte-verified prerequisites and no A100 activation, status remains **GPU-OFF SOURCE PREPARED, RUNTIME NOT ATTESTED**. This is not a reason to block low-cost source changes or use fake model-origin labels.
