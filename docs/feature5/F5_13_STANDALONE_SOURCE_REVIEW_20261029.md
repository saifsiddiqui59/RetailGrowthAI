# Feature #5 F5-13 — Standalone ComfyUI vendored source manifest (2026-10-29)

The original reviewed ComfyUI Containerfile calls `python source_audit.py --source ... --manifest ...` directly. Independent composite OCI pre-build reader hardening in Feature5 PR #688 does **not** protect this separate build-stage CLI. This source-only CPU security batch gives the direct Containerfile entrypoint its own strict bounded parser, rejecting ambiguous nested duplicate keys, nonfinite literals, JSON array/null roots and deep-recursion parse errors, plus symlinks or oversized review files.

Source-only negative tests exercise both the standalone helper and the actual CLI denial path. Verify targeted `python -m unittest discover -s tests/ai -p 'test_feature5_wan22_source_audit.py'` and mandatory exact-head CI 4/4. Review manifest matching remains a trust declaration, not independent source license approval or a signed SBOM; F5-13 remains IN PROGRESS until actual CUDA image/wheels/ABI/license/digest and production attestation.

Standalone draft PR stacked onto Feature5 #465 with owned nonoverlapping paths; coordinator handles source integration into main and main CI. No paid GPU, online model checkout, customer media, hosted SQL, PROD or WineShopPOS.
