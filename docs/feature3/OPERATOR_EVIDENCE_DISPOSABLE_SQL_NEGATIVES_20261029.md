# Feature3 private generated PNG evidence RPC — disposable SQL negative qualification

The existing `supabase/proposals/feature3_operator_evidence_read_20261029.sql` is **not** a canonical migration or live Supabase function. `tests/security/poster_feature3_operator_evidence_proposal_negative.sql` adds a genuine PostgreSQL parser, ACL and denial test under the existing offline security CI job's `poster*.sql` loop, then drops this source-only function from the disposable local database.

Negative outcomes checked:
- The proposed RPC exists only after explicit import into disposable Postgres; only service_role has EXECUTE, never anon/authenticated.
- Nonexistent same-shop/foreign-looking job, media and NULL identifiers yield no immutable private output approval or object path.
- A caller presenting a forged `authenticated` JWT role claim is denied even when the local SQL test has switched to a service-capable DB role; SECURITY DEFINER must fail closed.
- The code executes no GPU claim, payment, Storage mutation, media registration, queue ACK/retry, settlement or refund.

This test **does not prove** the presence of a real signed customer output, provider invoice, actual blob SHA, reviewer approval, current rights or approved hosted SQL. It is additive source qualification only and requires a distinct DB owner/coordinator-reviewed migration, genuine licensed output evidence, signed DEV role/cross-shop/revocation tests and independent human financial reconciliation before operational release. Keep 31 existing hosted DEV versions unchanged, GPU OFF and PROD/WineShopPOS untouched.
