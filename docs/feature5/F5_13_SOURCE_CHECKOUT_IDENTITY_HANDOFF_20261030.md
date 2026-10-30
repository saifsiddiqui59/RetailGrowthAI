# Feature #5 F5-13 — immutable ComfyUI source audit follow-up (2026-10-30)

Status: **SOURCE CHANGE PROPOSED; NOT INTEGRATED DONE**.

- Ownership: F5-13 immutable OCI/source/wheel licensing preflight. This is stacked on PR #698 (`feat/feature5-comfy-source-manifest-safety-20261029`), which remains under coordinator review; do not duplicate or bypass its standalone strict manifest parser.
- Issue found: a reviewed ComfyUI file could be replaced by an identical-size, different-inode file, changed in place, or swapped to a symlink after its original SHA-256 was read. The prior audit only rechecked file size after reading and did not recheck every named file at the end.
- Change: hash an open regular-file descriptor with no-follow/nonblocking flags where supported, reject linked or nonregular files, check device/inode/size/mtime/ctime before and after the stream, then recheck **all** named file and ancestor-directory identities after the full checkout inventory.
- Negative regression: synthetic same-byte inode replacement after hash, same-size in-place mutation, and symlink replacement between initial path check and open. All test bytes are fake ComfyUI source; no real model, rights, GPU, network, Azure, paid provider, PROD, or WineShopPOS.
- Verification: source/tests submitted to GitHub; exact-head CI and reviewer acceptance must be checked before claiming source-ready. A green offline test does not prove the actual vendored checkout, signed operator manifest, CUDA image digest, SBOM, redistribution licenses or runtime.
- Remaining acceptance: independently reviewed complete ComfyUI source/wheel hashes, actual immutable image build/digest, legal/SBOM/ABI review, coordinator-approved integration and fresh main four-job CI. No task_progress DONE event proposed.
