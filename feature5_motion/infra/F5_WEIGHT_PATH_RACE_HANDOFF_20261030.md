# Feature5 F5-14 — mounted checkpoint pathname identity (GPU OFF)

Date: 2026-10-30. Proposed source-only hardening for original F5 task **F5-14**; **IN PROGRESS**, not DONE.

## Scope and evidence
- Parent Feature5 draft: #465, branch `feat/feature5-a100-safe-control-20261028`.
- Dedicated draft PR: #771, commit `e8dbdb0b149c7107cb96aaabc8db4f19c4100932`.
- Existing offline `wan22_local_weight_audit._actual_full_sha` now checks open file link count and compares inode, device, size, mtime, ctime, mode and link count both on the open descriptor and at the original pathname after full streaming.
- New tiny fake-weight negative tests simulate same-byte path replacement after the file was opened, and a new hardlink after the read began. They do not contain actual Wan model bytes.
- Local Git checkout / pytest **not executed**: runner DNS could not resolve github.com. GitHub PR exact-head four-job CI **pending verification**. No success claimed.
- Actual three checkpoint full-byte SHA/size on private read-only Azure Files, immutable licensed OCI/CUDA dependency audit and live ComfyUI remain **UNVERIFIED**; never infer approval from fixture tests.

## Task control / blocker
- `F5-14` — owner Feature5/Runtime, dependency `F5-WEIGHTS`; needs independent trusted source SHA/size manifest and **actual read-only mounted three original Wan checkpoint files**, plus full-byte operator audit receipt. Acceptance: exact full original bytes/size/SHA and current private read-only mount evidence. This PR does not satisfy acceptance.
- `F5-13` — owner Feature5/Runtime, dependency `F5-OCI`; immutable licensed CUDA OCI base, reviewed wheelhouse hashes, complete source and SBOM still missing.
- `F5-02` — owner Feature5; `F2-CREATIVE-SOURCE` requires coordinator-merged original Feature2 exporter, then genuine 15/30/60 stdout/tamper tests.
- Central `coordination/task_progress.json` remains coordinator-only; propose evidence after exact-head CI, and only coordinator may record reviewed integrated DONE after main merge and fresh 4/4.
- Do not start A100/GPU, paid model calls, cloud writes, PROD or WineShopPOS. No customer images, model inference or user-facing samples were created.
