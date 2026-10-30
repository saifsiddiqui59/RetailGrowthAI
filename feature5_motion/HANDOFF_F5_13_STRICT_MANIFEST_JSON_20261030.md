# Feature #5 / F5-13 — Offline reviewed-manifest parser hardening

- Owner: Feature #5. Task: `F5-13` / OCI source and immutable offline build attestation.
- Source-only patch on a dedicated branch based on Feature5 draft PR #465 head `af4cc21b69382f6b1b45fbd916861569740f7677`.
- Changes: reject duplicate object keys at any nesting depth and non-finite JSON values in separately supplied source and wheel SHA manifests, including the direct ComfyUI source-audit CLI. Previously Python JSON silently accepted the last duplicate key and NaN/Infinity.
- Tests: `tests/ai/test_feature5_wan22_source_audit.py` and `tests/ai/test_feature5_wan22_build_context_gate.py` add deterministic synthetic negative cases; CI results must be checked on the exact final head before asserting a pass.
- **Status: IN PROGRESS.** This is a safe F5-13 subtask, not F5-13 acceptance. Immutable reviewed CUDA base, wheelhouse, GPL/CUDA legal review, SBOM, actual OCI digest and build/ABI verification remain missing. No Docker build, network download, GPU, inference, cloud deployment, PROD or WineShopPOS edits.
- Coordinator handoff: review this stacked PR before F5 #465 integration; only coordinator may update `coordination/task_progress.json` and shared canonical documents after acceptance and fresh main 4/4 CI. Do not mark F5-13 or the 22-task release ledger DONE on source-only evidence.

## CI repair evidence

- Initial exact-head push CI [#41033706123](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41033706123): Python job **FAILED** (4 new subtests) because the test asserted raw parser diagnostic text while the existing outer build gate deliberately returns the generic fail-closed `Unreadable reviewed manifest` error. Other 1179 Python tests passed, 9 skipped. The strict parser was rejecting the inputs as intended; no security gate was weakened.
- First safe fix `960901c7`: assert the existing redacted `WanCompatibilityError` in build-gate tests; exact low-level duplicate/non-finite reasons remain covered in source-audit tests. New final-head CI required; no DONE claimed.
