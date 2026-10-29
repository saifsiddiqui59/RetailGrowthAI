# Feature #5 F5-13 — Offline wheel archive install-boundary hardening (2026-10-29)

This independent, GPU-OFF Feature5 source PR is stacked onto existing draft Feature5 #465; it does not touch any other feature branches. It complements distinct F5-13 OCI reviewer-manifest PR #688 without overlapping files.

Offline `audit_offline_wheelhouse` already verifies byte-for-byte independently reviewed SHA256 and embedded distribution identity. Before installing a reviewed wheel via offline `pip --require-hashes`, the updated audit now rejects duplicate ZIP member entries, case-fold name collisions, symlinks/device entries, absolute/traversing/empty/dot paths, control bytes and expanded archive size above 24GiB. Source-only CPU tests intentionally recompute fixture-approved hashes after creating malicious wheel ZIPs to prove that a matching SHA alone cannot authorize a dangerous archive.

Targeted: `python -m unittest discover -s tests/ai -p test_feature5_wan22_wheelhouse_audit.py`. Mandatory exact-head four-job CI after push. Not actual legal, ABI, CUDA, real wheel download/OCI digest, SBOM or GPU approval. F5-13 remains IN PROGRESS; no deployments, paid inference, hosted writes, PROD, previews or WineShopPOS.
