# Feature #3 original F3-07 / F3-13 — immutable private media commit receipt attempt fence

**Source-only, GPU OFF.** This code does not call FLUX, Wan, Azure, Supabase, any paid service or a deployed database.

## Exact original task coverage
- **F3-07**: Private generated PNG registration and SQL CAS evidence. The service-only `PrivateOutputRegistrar` formerly accepted a forged commit acknowledgement with `attempt=True` or `attempt=1.0`, because Python compares either as equal to integer `1`.
- **F3-13**: Negative authorization/unknown ACK regressions. Add untrusted receipt cases `True`, `1.0`, `"1"`, `0`, `2`, `None`, `False`, together with metadata attempt negative cases. The success case keeps exactly one integer attempt.

## Behavior and non-retry boundary
- Reject any returned CAS receipt whose `attempt` is not genuinely `int` or is not exactly `1`, even when all source SHA, claim token, original image and object path values match.
- A rejected post-commit receipt represents **AMBIGUOUS DB OUTCOME**. Never attempt a second commit or quarantine/delete the staged PNG automatically; a human operator reconciles it.
- Existing `_metadata` intake already enforces integer attempt. New tests prove both input and post-commit sides fail closed.
- Scoped code: `poster-engine/feature3_private_output_v1.py`; offline tests: `tests/media/test_feature3_private_output.py`.

## Review, test and original package state
- Targeted: `python -m unittest discover -s tests/media -p 'test_feature3_private_output.py'`; required four-job final-head Part 1 CI on this PR; independent private-output/financial review before merge, then fresh `main` four-job CI.
- F3-07 remains **source partial**, not DONE until genuine immutable hosted output, signed user rights/lease, approved model/garment/license and real provider/financial evidence. F3-13 also remains hosted incomplete until real signed negative tests. A success in offline fixtures is not commercial approval.
- Do not duplicate prior merged Wave A/B source work; original source-component receipt tracker is proposed in #860. This PR addresses a genuinely new typed **post-commit ACK** check (separate from already-integrated F3-06 operator evidence typed-attempt guard in #834).
- No sample, GPU, paid image generation, PROD, hosted SQL, user accounts, WineShopPOS or cloud deployment.
