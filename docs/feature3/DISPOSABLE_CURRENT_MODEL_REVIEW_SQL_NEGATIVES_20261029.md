# Feature3 service-only current model rights proposal — disposable SQL security gate

## Source-only verification (2026-10-29)

`tests/security/poster_feature3_current_model_review_proposal_negative.sql` runs only in the existing four-job GitHub Actions **disposable Supabase Postgres** security job, under the existing `tests/security/poster*.sql` loop. It `\\ir`-imports the source-only `supabase/proposals/feature3_current_model_review_20261029.sql`, executes actual PostgreSQL privilege/identity denials, then drops that proposal function from the disposable database. It does **not** migrate hosted DEV or rewrite any of the existing 31 versions.

- Require an executable service-role-only RPC: `anon`/`authenticated` have no function EXECUTE; a service-role JWT claim and SQL role may read only matching current independently reviewed shop/model/source records.
- Missing/unreviewed foreign shop/media identifiers, malformed SHA or NULL parameters must return NULL and cannot create an approval, job, lease, charge, output media or browser grant.
- An `authenticated` claim in an otherwise privileged local PostgreSQL session must be explicitly rejected with SQLSTATE 42501 even with SECURITY DEFINER.
- Never insert fabricated evidence or approve a model to force positive tests. Positive current approved source test remains blocked until a legitimate independent model/licence/customer authority is available.
- This is stronger than static text inspection, but is not real customer licence verification, live JWT/TenantStore/Storage acceptance or a real provider invoice.

No new migration or hosted DB/Storage/Queue/PROD/WineShopPOS mutation; paid GPU stays OFF. Coordinator/DB owner approval, versioned migration and signed live tenant-role negative tests remain required before the RPC may be deployed.
