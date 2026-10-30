# F5-14 — Private Wan model manifest inode fence (2026-10-30)

**Scope:** GPU-OFF, CPU-only source hardening on top of consolidated Feature5 PR #781. F5-14 remains **IN PROGRESS**, not integrated DONE.

## Problem and fix

The previous bounded manifest reader checked `is_symlink()` and `is_file()` before calling `Path.open()`. A local attacker with write access to the manifest directory could replace the path between those calls and the actual open, causing an unintended symlink target to be read. The new reader opens with `O_NOFOLLOW`, verifies regular file and single-link inode identity before/after reading, enforces 64 KiB bound and uses `O_NONBLOCK` to avoid blocking on a substituted FIFO. Unsupported no-follow platforms fail closed.

The regression test rejects hardlinks and named pipes, and confirms a normal synthetic private manifest still validates. Existing duplicate-key, nonfinite, oversized, symlink, SHA/revision and mount negative tests remain intact.

## Evidence / next gate

- Changed: `feature5_motion/shared_model_mount.py`, `tests/ai/test_feature5_shared_model_mount.py`.
- Targeted test: `python -m unittest discover -s tests/ai -p 'test_feature5_shared_model_mount.py'`.
- **Test execution and exact-head four-job CI pending independent verification**; no passing test claim.
- Coordinator should review this stacked PR, integrate it once into the F5-14 consolidated batch, run full exact-head CI and fresh main 4/4 before any integrated DONE receipt.
- Original Wan model weights were **not read**. Actual private Azure Files mount, all three checkpoint hashes, license/SBOM/OCI review and GPU runtime remain unverified.
- No GPU, paid model, Azure/SQL/PROD mutation, external media, customer output, or WineShopPOS change.
