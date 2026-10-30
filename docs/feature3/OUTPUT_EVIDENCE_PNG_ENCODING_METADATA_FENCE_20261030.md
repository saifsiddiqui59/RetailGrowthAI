# Feature #3 source handoff — immutable private output evidence PNG hardening (2026-10-30)

**Task IDs:** F3-06, F3-07, F3-13. **Status:** IN PROGRESS — source-only, awaiting coordinator integration and exact-head four-job CI. **Hosted DONE:** unchanged; no acceptance evidence added to the shared task manager.

## Actual code changes
- `azure-functions/campaign-api/feature3_verified_output_evidence.py`: reject nonidentity Content-Encoding, malformed Content-Type, and EXIF/XMP-bearing PNGs even when bytes match the private SQL SHA/length receipt. Preserve the two independent SQL reads and no-URL operator receipt.
- `tests/api/test_feature3_verified_output_evidence.py`: fixture-only negative tests for gzip/Brotli/malformed header, an XMP-bearing valid PNG with matching SQL SHA, and positive identity-encoding control. These are deterministic synthetic PNGs, not licensed/generated customer images.

## Evidence and acceptance boundary
- Tests are proposed in this PR; check the exact PR head and four independent CI jobs before coordinator review. Do not claim pass until Actions confirms.
- The existing service-only SQL RPC proposal is **not applied to hosted DEV**; this change does not mount a public route, perform GPU inference, register customer output, grant rights, settle invoices, or modify PROD.
- Coordinator alone can integrate into main and update `coordination/task_progress.json`, `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md`. F3-06/F3-07/F3-13 are not DONE merely because source tests pass.

## Explicit blockers
- **F3-LICENSED-MEDIA** — Feature3 rights owner; independently reviewed retailer original model/garment rights, human approval, and revocation evidence. Accept only signed current commercial rights, not fixtures.
- **#471 / #325** — Feature3/coordinator; approved mounted authenticated no-URL generated-output route and immutable current private output bytes; acceptance includes signed foreign/revoked/VIEWER denial in DEV.
- **#249** — Azure reliability lead; signed hosted DEV 503 fix with post-fix verified response.
- **F5-GPU-AUTHORIZATION / PART3-WAN22-CONTRACT** — coordinator; explicit bounded paid model authorization and immutable lease/spend interface before genuine output. GPU remains OFF.
- **DEV-AUTH-TEST-USERS** — Auth Admin/operator; two distinct nonprivileged DEV shop-owner accounts, signed RLS shop isolation and browser negative tests. Not provisioned/verified by this change.

No paid inference, Azure provisioning, hosted SQL, customer preview, or WineShopPOS changes.
