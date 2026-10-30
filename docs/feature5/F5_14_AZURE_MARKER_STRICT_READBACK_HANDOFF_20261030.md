# Feature #5 F5-14 — Azure Files completion marker fail-closed readback (2026-10-30)

Status: **IN PROGRESS, SOURCE-ONLY**. Task ID `F5-14`; parent draft PR #465. This change is deliberately path-disjoint from existing F5-14 drafts #691/#724 and F5-13/F5-02 drafts. Coordinator alone accepts shared task-status events and merges to main.

## Implemented CPU-only source
- The existing read-only Azure Files six-checkpoint metadata audit now bounds marker GET to the HEAD-verified maximum 64 KiB, re-reads marker size and optional ETag after the GET, and rejects changed marker identity.
- Rejects duplicate root/nested JSON keys, nonfinite numbers, recursive malformed JSON, nonobject documents, invalid metadata types and size drift instead of accepting ambiguous marker declarations or leaking unexpected parser exceptions.
- Deterministic fake Azure SDK negative tests; no Azure network, model byte download, GPU, inference, billing, PROD, WineShopPOS or user-facing sample.

## Evidence / acceptance
- Targeted suite: `python -m unittest discover -s tests/ai -p test_feature5_model_share_readonly_audit.py`.
- Four exact-head CI jobs must be verified for this PR head before coordinator review. Source-only metadata comparison **does not** establish 34,277,265,757 bytes of genuine mounted weight SHA proof.
- Dependency **F5-WEIGHTS**; owner **Feature5/Runtime + authorized operator**; required output: actual existing read-only mounted Wan2.2 three-file full-byte SHA/size and independently reviewed source revisions, without unapproved remote I/O. Acceptance: secure no-follow, stable full-stream hashes and original manifests, with actual operator evidence; no inference or legal approval implied.
- Other independent gates: F5-OCI immutable reviewed legal runtime/SBOM; F5-GPU-AUTHORIZATION separate human approval; PART3-WAN22-CONTRACT coordinator ratification; F3-LICENSED-MEDIA genuine signed retailer rights. Never mark F5-14 integrated DONE from these tests.

Proposed coordinator status receipt: `F5-14` stays `IN_PROGRESS`, PR head + CI evidence to be filled after verification. `coordination/task_progress.json` and canonical shared docs remain coordinator-owned.
