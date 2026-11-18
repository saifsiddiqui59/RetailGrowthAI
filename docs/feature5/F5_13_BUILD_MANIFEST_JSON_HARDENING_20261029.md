# Feature #5 — F5-13 offline build-review manifest hardening (2026-10-29)

This is a source-only CPU security batch to the existing draft Feature5 #465 stack (parent head `af4cc21b69382f6b1b45fbd916861569740f7677`), with its own branch and PR. The 4 MiB private JSON reader for independently supplied OCI/source/wheel review manifests rejects nested duplicate JSON keys, nonfinite numbers, nonobject roots, and excessive nesting instead of crashing or accepting ambiguous attestations.

Targeted test: `python -m unittest discover -s tests/ai -p 'test_feature5_wan22_build_context_gate.py'`. Exact-head four mandatory CI jobs are required for source evidence. This neither builds the image nor verifies NVIDIA/CUDA terms, OCI digest, SBOM, legal license, actual 18 GiB model bytes, local private ComfyUI runtime, commercial rights, hosted RLS nor WAN inference.

Feature #5 original task **13 remains IN PROGRESS**, dependent on independently reviewed immutable OCI build and legal/ABI/SBOM proof. Do not activate GPU; no billable service, hosted SQL, PROD, samples or WineShopPOS change. Only the coordinator merges parent #465 and records postmerge CI.
