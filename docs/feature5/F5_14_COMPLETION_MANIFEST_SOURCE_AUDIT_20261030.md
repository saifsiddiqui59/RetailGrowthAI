# F5-14 — Azure completion marker + private manifest source verification (2026-10-30)

This is a **GPU-OFF source-only batch** on existing draft PR #781. The original feature #5 item **F5-14** stays IN PROGRESS until the operator independently verifies the real mounted **three Wan checkpoint files** with full byte SHA256 and correct revision/rights. No Azure API or model bytes were accessed during this source change.

## Owned code changes

- `feature5_motion/audit_shared_model_share_readonly.py`: keep manifest read metadata-only, but enforce an SDK read **bounded by the declared <=64KiB marker size**, ensure byte count matches, verify marker size and available ETag/last-modified did not drift during the read, reject recursively duplicate JSON keys, NaN/Infinity and nested/deep/invalid UTF-8/object shapes using the shared strict manifest parser. Only after all checks may existing read-only six model file metadata checks proceed.
- `tests/ai/test_feature5_model_share_readonly_audit.py`: synthetic Azure SDK mocks prove duplicate nested field, original `gpu_started` duplicate, nonfinite, overdepth, null/trailing JSON and changed ETag are denied **before any model file HEAD**. Reject SDK returning more bytes than it was asked to read.
- `feature5_motion/shared_model_mount.py`: read the **local** private completion manifest using `O_NOFOLLOW`/bounded `O_NONBLOCK` single-link regular file descriptor, checking its identity, size and mtime before and after bytes and the final path, preserving the existing duplicate/nonfinite JSON and 6-file SHA/revision checks.
- `tests/ai/test_feature5_shared_model_mount.py`: synthetic single-link positive, hardlinked local manifest refusal and descriptor mtime replacement denial.

## Test and integration rules

Targeted: `python -m unittest discover -s tests/ai -p 'test_feature5_model_share_readonly_audit.py'` and `python -m unittest discover -s tests/ai -p 'test_feature5_shared_model_mount.py'`. Current exact PR #781 head requires **all four green CI jobs**; previous run #41054823580 (4/4) was on an older SHA and cannot certify this change. Coordinator may integrate only after reviewing the new head; postmerge 4/4 main CI required for accepted development completion. The module's optional Azure `--audit-existing-share` still requires manual opt-in and existing protected credential; no authorization requested or granted here.

The Azure marker and HEAD metadata **do not verify the original model bytes**, reveal consumer rights, grant GPU/cost budget, or validate real provider inference. Never treat injected fake SDK objects as a live source. Preserve GPU OFF, no paid inference, no PROD/hosted SQL, no WineShopPOS, no generated user-facing samples or artificial DONE.

Original task counts remain **0 DONE / 3 IN PROGRESS / 19 BLOCKED / 22**; F2 #551, Part3 #125, F4 #322 still need their actual owners' integrations.
