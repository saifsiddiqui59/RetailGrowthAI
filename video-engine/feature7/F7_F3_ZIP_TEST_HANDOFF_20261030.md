# Feature #7 — F7-02 original Feature3 artifact acceptance handoff (2026-10-30)

Task: **F7-02**, original pinned Feature3 technical artifact positive consumer test. Status: **IN PROGRESS / source improved, exact repository positive test still not observed**. This is test infrastructure, not production footage, rights clearance, ASR or final editing.

## Read-only original evidence in this ChatGPT run

- Downloaded existing GitHub Actions run **40831572603**, artifact **12879355229** (no model execution or cloud provisioning).
- Independently verified all **seven** ZIP entry SHA256 values against `feature3_artifact_preflight.py` pins, including original video SHA256 `16ceaa91a5dad57de023f45b21eee45772f361a18299801e9e27b6ae49ce9f22`.
- Ran local `ffprobe` on the extracted original bytes: **1080×1920 H.264 video, stereo AAC audio, 9 seconds**. Original manifest declares **no VTON inference** and **no publish approval**.
- This manual check does **not** claim the three repository positive tests were executed, and no real merchant rights or generated model-wearing-garment output was verified.

## Code change and remaining acceptance

- `tests/media/test_feature7_feature3_actual_demo.py` now accepts the **single pinned ZIP** via `FEATURE7_F3_ORIGINAL_ARTIFACT_ZIP`, verifies the entire original ZIP/license/manifest using `check_feature3_actual_artifact`, and passes the verified embedded MP4 bytes into the existing Feature7 private source consumer. The older separately staged MP4 + expected SHA mode remains supported. When both are present, the original standalone file must match the ZIP.
- This eliminates a second manual extraction and separately supplied hash from the positive consumer path, reducing accidental fake-asset acceptance. No new sample, model, service, renderer, GPU or shared contract was added.
- **Still required:** run with the actual artifact staged in the same repository checkout:
  `FEATURE7_F3_ORIGINAL_ARTIFACT_ZIP=/absolute/path/to/feature3-openvto-editor-input-mp4.zip python -m unittest tests.media.test_feature7_feature3_artifact_preflight tests.media.test_feature7_feature3_actual_demo tests.media.test_feature7_feature3_private_review_actual -v`.
  The original Feature3 video is silent technical geometry input. It is not approved retailer-owned content.
- Targeted source syntax and exact-head four-job CI are separate gates; no new integrated DONE or hosted release is claimed. Coordinator alone may merge and record canonical status.
