# Feature #3 queue-envelope invalid-Unicode denial — 2026-10-30

**Original tracked task:** F3-13 (cross-tenant, rights and ambiguous-ACK regressions). **State:** SOURCE PROPOSED, not integrated DONE. F3-04 (real Azure consumer/ACK) remains independently blocked.

## Defect and scoped repair
The GPU-OFF queue decoder accepted Python `str` and measured `len(payload.encode("utf-8"))` before the JSON parse. A lone UTF-16 surrogate in in-memory text raised an untyped `UnicodeEncodeError` rather than the existing `GPUEnvelopeDenied` contract. This could bypass downstream poison-message classification, although no GPU execution or ACK is performed by this decoder. Reject invalid Unicode explicitly before JSON parse, preserving existing byte-length, strict JSON and UUIDv4 gates.

## Verification and limitations
- Added deterministic negative tests for high/low lone surrogates, a surrogate inside a claimed resource ID, and illegal UTF-8 bytes. Existing valid roundtrip remains unchanged.
- Targeted tests are **not yet executed locally**. Review exact-head four-job GitHub PR CI; coordinator must integrate only after required checks pass and confirm fresh main 4/4.
- No Azure Queue messages sent, no SQL writes, no paid GPU or AI, no user-facing sample, no PROD or WineShopPOS modification. This does **not** prove real queue poison/ACK, signed DEV tenant isolation, commercial rights, or approved generated media.

## Dependency and acceptance handoff
- **F3-04 / Feature3 + coordinator:** approved real one-shot Azure consumer/ACK/poison implementation, immutable lease and rights checks; required output is an actual reviewed deployment and safe unknown-ACK reconciliation. This PR only strengthens the offline decoder.
- **F3-LICENSED-MEDIA / Feature3:** current human-reviewed licensed retailer originals and likeness/commercial grant before real inference.
- **#249 / Azure reliability lead:** stable signed DEV HTTP gateway before hosted E2E.
- Proposed coordinator status: F3-13 remains **IN PROGRESS**; `coordination/task_progress.json` remains coordinator-owned and unchanged.
