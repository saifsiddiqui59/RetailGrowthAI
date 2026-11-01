# Feature #3 F3-02 / F3-13 private worker final-read grant revision guard

## Source-only security issue
The existing `poster-engine/feature3_worker_input_handoff.py::_final_read` checks a current private media grant before reading original garment/model/try-on bytes, but compared `rights_revision` using Python's ordinary equality. A transient mocked or malformed authoritative callback with `rights_revision=True` or `1.0` could incorrectly equal an immutable revision `1`, so the final-byte read boundary would fail open on malformed rights metadata.

## Change
- Require `type(grant.get("rights_revision")) is int` before checking the exact approved revision. No other paths/authorization contracts are changed.
- Add a deterministic **full `resolve_private_worker_inputs` path** test with synthetic in-memory bytes: establish revision 1, inject malformed `True` or `1.0` only on the final garment-grant callback, and prove the packet is denied at that check. A later healthy grant must not excuse the transient invalid current grant.
- Original task IDs: **F3-02** private worker materialization and **F3-13** cross-tenant/rights negative regressions. Existing source components were previously integrated through Waves A/B; this is a distinct previously untested *intermediate* input-revision type gate.

## Acceptance and boundaries
- Run `python -m unittest discover -s tests/media -p 'test_feature3_worker_input_handoff.py'` and all mandatory exact-head Part 1 CI jobs. Independent private-media/rights review required before feature merge, then fresh postmerge main 4/4.
- No approved signed hosted developer accounts, independently licensed garments/models, real Feature4/5 worker lease, paid GPU, live upload, DB mutation or hosted test; F3-02/F3-13 remain source partial, not hosted DONE.
- No sample media, paid inference, PROD, Azure paid resources, automatic retries or WineShopPOS modifications.

## 2026-11-01 continuation — final worker read must recheck the private path
- The original intermediate rights-revision type fix is retained. A separate TOCTOU gap was found in the same F3-02/F3-13 final worker read: after the first full private-source proof, the final `_final_read` rechecked only shop, bucket, media ID, SHA and MIME. A transient substituted `object_path` or source kind could therefore be handed to `read_private_bytes` before the final manifest recheck rejected the packet.
- The final read now reuses the established `fashion_reference_v1._approved_asset` source authority **before** private bytes are requested, enforcing current rights revision type, original garment/model/try-on role, tenant-scoped Storage namespace, registered source and byte digest. For a first-frame input, the validated manifest source selects the existing garment or reviewed try-on path policy. The existing post-read lease/rights rechecks remain in place.
- Offline regression `test_transient_private_object_path_substitution_denied_before_worker_read` injects a foreign-shop path, traversal path, HTTPS path, model-library path, changed source and public bucket on the *second* garment row read. It verifies that only initial authorized source reads occurred; no transient substituted path was fetched. No paid inference, hosted Storage, signed customer media or new API/schema is introduced.
- This is an additive change in the existing **PR #862**, not a new duplicate task. Exact new head mandatory 4/4 CI, independent private-media review, current-main merge and fresh postmerge main 4/4 are still required. **F3-02/F3-13 remain source partial**; hosted acceptance remains 0/33. Separate `fashion_reference_v1.resolve_first_frame` final-frame path/rights review remains an adjacent cross-feature gate and is not claimed solved here.
