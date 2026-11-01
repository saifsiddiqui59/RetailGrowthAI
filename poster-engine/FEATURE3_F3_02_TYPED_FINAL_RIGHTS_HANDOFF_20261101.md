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
