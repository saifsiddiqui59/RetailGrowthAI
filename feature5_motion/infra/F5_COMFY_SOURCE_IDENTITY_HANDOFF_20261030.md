# Feature5 F5-13 — reviewed ComfyUI source identity (GPU OFF)

2026-10-30. Proposed source-only F5-13 hardening, **IN PROGRESS**, not accepted integrated DONE.

- Parent: draft PR #465. Source commit: `d6fd83c30d5b90b32f57f452ca57b1e1bd152191`.
- Existing offline vendored-source SHA256 auditor now checks a source file's link count, opened inode and pathname identity across full streaming, including size, mtime, ctime and mode. It denies a multiply linked source or a replaced pathname even when the originally opened file has approved bytes.
- New deterministic fake-ComfyUI tests cover an external hardlink and same-byte path replacement after open. **No real ComfyUI source tree, CUDA image, wheels, GPU or model inference** was run.
- Local repo checkout / pytest could not run because github.com DNS was unavailable. Exact-head GitHub PR four-job CI must be inspected before review; **no test pass is claimed**.
- Task `F5-13` / dependency `F5-OCI` / owner Feature5/Runtime: needs independently reviewed immutable CUDA OCI base digest, full licensed source and real wheelhouse SHA256 lock, actual image build/SBOM, runtime ABI and legal signoff. Source-audit regression alone does not meet acceptance.
- Central `coordination/task_progress.json` and canonical docs are coordinator-owned. Coordinator must review PR, integrate and confirm fresh main 4/4 before DONE. No paid GPU, model, Azure/SQL/PROD or WineShopPOS change.
