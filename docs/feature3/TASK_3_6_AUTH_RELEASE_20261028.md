# Feature3 Task3.6 — Offline HTTP release-gate test handoff

`tests/api/test_feature3_release_routes.py` exercises the **actual**
`HTTPAPI.handle` routing under a fake JWT verifier (no network calls).

The regression suite checks:
- Feature3 v2 stays 503/DISABLED unless an operator enables it.
- No public paid GPU job submit POST has been added.
- Absent/forged/expired bearer tokens are denied before all Feature3 handlers.
- Source asset ownership, generated PNG signed download and approved-model
  metadata endpoints take only exact GET route/method/tenant IDs; wrong methods
  and forged extra path segments cannot reach the privileged adapter.
- This is a source contract. It is NOT a genuine hosted owner JWT, Supabase
  Storage review, live PNG, browser E2E or CUDA test.

Remaining Task3.6 acceptance after integration requires actual signed-in
OWNER/EDITOR, VIEWER, revoked, foreign and expired account proofs; real
model registration+human rights; durable 1-attempt GPU spend and outbox
concurrency; private image bytes/review; and a separately approved GPU
smoke. Hosted signed-in browser acceptance stays deferred in the current
user sprint but cannot be called passed.

No GPU rental, billable AI, production or WineShopPOS modification.
