# Feature #5 — Professional Wan2.2 TI2V-5B motion adapter (GPU OFF)

Status: source-only integration on draft PR #465, stacked on #323. No GPU job, inference, production output or paid permission.

## Official implementation reuse and licensing

Read the actual Wan-Video/Wan2.2 source at pinned commit 1ea34ff48f87168174e12956e200b1d908b1c5ff (Apache-2.0, copyright Alibaba Wan Team):

- wan/configs/__init__.py: official TI2V-5B supports 704x1280 or 1280x704, not native 1080x1920.
- wan/configs/wan_ti2v_5B.py: 24 FPS, 121 frames, one model for image-to-video and text-to-video.
- generate.py: the same ti2v-5B task accepts an optional source image. The original CLI expects a different checkpoint layout from the already-staged Comfy-Org .safetensors, so do not pass those files to original Wan CLI unchanged.
- wan/utils/prompt_extend.py and system_prompt.py: reuse model-specific task/technical motion framing, NOT unrelated source policy rewriting, cloud DashScope/Qwen calls or automatic creative prompt edits.
- The actual native nodes already implemented in feature5_motion/infra/feature35_comfy_api_graphs.py reuse pinned official ComfyUI commit 79cf64c21a1dba50749945ba9fe2e3a692f45438 and official workflow templates e7cd011d4ded3411c2f481200544f0be6fdc962e. No second pipeline or renderer.

Existing private six-model Azure Files manifest independently verified in protected Action #40676023863. Existing environment model share registered and verified ReadOnly in protected Action #40677739766, no GPU job provisioned by this work.

## Versioned Feature2 -> Feature4 -> Feature5 contract

- Feature2 draft PR #514 owns approved motion_direction_v1 and its 15/30/60s parent creative_direction_v1. Feature4 PR #322 coordinates and owns final creative_reel_v1 composition; Feature5 never rewrites scripts, offers, dialogue or editor effects.
- feature5_motion/wan22_motion_adapter.py validates complete 5-second Feature2 motion brief via Feature4's explicitly reviewed dispatch, shot/order/continuity, approved product and human likeness, exact garment color, embroidery, neckline, hem, time-sequenced body/fabric motion, camera, lighting, source media ID, source checksum and immutable review lineage. The upstream prompt mode switch uses the existing Wan hybrid model and the staged native ComfyUI graph.
- Feature2's 1080x1920 is an EDITORIAL FINAL REEL TARGET. Feature4/coordinator must approve a separate real Wan 704x1280/24FPS/121-frame production profile. No silent downscaling or claim of native Full-HD. Mismatched profile, unverified installed revisions, wrong GPU capacity, missing approval/media, bad image aspect, unsupported timeline or prompt overflow fail closed. Real garment fidelity cannot be proven by text.
- Model-specific focused technical prompt notes append the exact Feature2 approved prompt without replacing it. Its separate negative constraints are included in the immutable prompt hash. No third-party prompt extension fee.
- Current Feature2 motion_direction_v1 requires a first-frame reference, so its integrated path is IMAGE-TO-VIDEO ONLY. The same native Wan TI2V graph supports T2V without a start_image, but Feature2 must approve a new optional-reference schema before separate text-only dispatch is activated.
- feature5_motion/wan22_clip_validation.py reads only local private MP4 via ffprobe, verifies H264/704x1280/24fps/121 decoded frames/duration, hashes file and produces an immutable PENDING receipt. It never marks a generated clip approved without actual stored bytes, private upload, verified ledger claim/fencing/settlement and a competent authorized human evaluating hands, faces, garment embroidery, motion, camera and style. Feature4 remains final compositor and upscaler.
- Current legacy Hunyuan MotionSpec/runner/Part3MotionStoreAdapter remain intact. No second wallet, retry system, pipeline or editor was added; coordinator must wire the new versioned request into its existing durable claim and private media store.

## Release safety and costs

The Wan upstream minimum 24GiB GPU for offloaded TI2V-5B is not a measured ComfyUI VRAM or runtime guarantee. Public East US Azure NC A100 meter USD 0.000529/sec, plus CPU, RAM, storage and other charges, is NOT an account invoice or owner-approved all-in test budget. GPU remains OFF; no actual CUDA container built, verified OCI image hash, live ComfyUI node server or licensed retailer first frame is available from this source branch.

Wan source/model cards advertise Apache-2.0; actual checkpoint dependency licensing and notices need legal review. ComfyUI itself GPL-3.0, with corresponding distribution/source compliance questions for a packaged SaaS worker. Torch/NVIDIA runtime and other dependencies remain incompletely locked. The creative/media rights, human likeness approval, source image SHA and cross-region transfer consent must be verified independently before any paid test. Keep manual single-shot retries disabled, all per-test spending approvals unset and no WineShopPOS modifications.

## CPU verification and coordination

Source tests: tests/ai/test_feature5_wan22_motion_adapter.py, tests/ai/test_feature5_wan22_clip_validation.py, tests/ai/test_feature35_comfy_api_graphs.py. Require exact-head four-job CI, then independent coordinator review of #514, #322, #323/#465. Coordinator updates canonical PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG after integration. No hosted media or GPU inference is claimed.
