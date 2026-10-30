# Feature #5 — F5-14 original Wan checkpoint manifest reader hardening (2026-10-29)

Scope: existing GPU-OFF six-model Azure Files inventory and local three-Wan-file full-byte-check CLI. The original 64 KiB private manifest is now parsed through one bounded fail-closed helper that rejects symlinks, empty/oversized inputs, nonobject roots, nested duplicate-key JSON, nonfinite JSON and deep-recursion decoder failures. It preserves immutable checked source revision/size/SHA from source and does not read any 18 GiB model weights automatically.

Targeted CPU tests: `python -m unittest discover -s tests/ai -p 'test_feature5_shared_model_mount.py'` plus `test_feature5_wan22_local_weight_audit.py`. Four mandatory exact-head CI jobs must be reviewed. No GPU, Azure mutation, model downloads, customer media, prod, user sample, rights assertion or WineShopPOS change.

Original **F5-14 remains IN PROGRESS**: actual local Azure Files model byte hashing against independently reviewed original 3-file SHA and real mount/readback have not been executed. Parent draft Feature5 PR #465 and separate paths from F5-02/F5-13 sibling branches; coordinator integrates shared ledger after review and fresh postmerge main CI.
