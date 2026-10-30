# Feature #5 / F5-14 — Private mounted-weight manifest strict parsing

- Owner: Feature #5. Existing numbered task: F5-14 (actual read-only Wan checkpoint byte verification).
- This independent source-only subtask reuses the F5-13 strict JSON parser from stacked PR #793, refusing duplicate object keys and NaN/Infinity before any private weight-byte access.
- Deterministic tests in `tests/ai/test_feature5_wan22_local_weight_audit.py` ensure malformed manifests cannot invoke the model-byte reader; synthetic fixtures only.
- **IN PROGRESS, not DONE.** No actual mounted 18.1 GB Wan files were available to this ChatGPT run; no genuine full SHA256 readback, runtime launch, OCI verification, license signoff, or GPU inference occurred.
- Exact-head four-job CI is required after this branch push; only coordinator can merge accepted changes and update canonical task-progress/main docs.
- Blocking dependency: `F5-WEIGHTS` owned by Feature5 Runtime/Operator. Required: private read-only mounted Wan original three files with independently pinned size/hash and full streaming verification. Acceptance: all three real installed original bytes pass SHA/size/inode checks, with no symlink/hardlink or mutation and independently reviewed provenance.
