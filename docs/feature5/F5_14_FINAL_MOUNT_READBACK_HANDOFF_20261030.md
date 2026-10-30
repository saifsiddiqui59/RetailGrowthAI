# Feature #5 F5-14 — final mounted-weight identity readback (GPU OFF)

**Task:** F5-14 (source in progress; NOT integrated DONE).  
**Branch:** `feat/feature5-f5-14-mount-recheck-20261030`, stacked on Feature5 PR #465.

## Change

The existing read-only offline Wan three-checkpoint auditor already streamed each file and compared the full expected SHA-256, size and open descriptor. However, because the three files are processed sequentially, a file whose hash was checked first could be atomically replaced while later files were being audited. The final result would otherwise attest a stale pathname.

The auditor now records no-follow filesystem identities for the model mount root, intermediate directories and all three named checkpoint paths. It checks them again after all three hashes. It also checks ctime on the open descriptor. A deterministic **synthetic tiny-byte** negative test swaps the first file with identical bytes and a new inode after its hash, before the other two files are read, and requires rejection. No actual checkpoint was read.

## Evidence and limits

- Code: `feature5_motion/infra/wan22_local_weight_audit.py`
- Regression: `tests/ai/test_feature5_wan22_weight_final_readback.py`
- Targeted local execution: **not performed** in this GitHub-only session. Verify the exact-head four-job PR CI and inspect the Python test result before coordinator acceptance.
- This final path recheck narrows a TOCTOU window; it is **not an atomic filesystem snapshot** or proof of mount read-only policy. The caller must still enforce immutable private storage, independent model hashes, rights, approved OCI/runtime, protected live node inventory and explicit GPU/budget approval.
- Dependency: `F5-WEIGHTS` (Feature5/Runtime). Required: original three Wan checkpoint bytes in the approved read-only private mount and independently reviewed SHA-256/size; acceptance: full live read-only byte audit and immutable provenance, followed by coordinator-reviewed integration and fresh 4/4 main CI.
- No paid calls, GPU, Azure writes, hosted SQL, PROD, demo media or WineShopPOS changes.

**Status:** IN PROGRESS — source change proposed for coordinator review; F5-14 and the central 22-task completion count remain unchanged.
