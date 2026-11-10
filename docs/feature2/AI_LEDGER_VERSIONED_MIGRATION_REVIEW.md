# Feature2 canonical AI spend migration candidate

Source-only migration: `supabase/migrations/20261026194000_feature2_ai_cost_ledger.sql`. This document does not authorize hosted DEV/PROD application, subscription updates or any paid inference.

## Atomic and security changes
- Reuses existing `shop_subscriptions` row `FOR UPDATE` serialization and checked OWNER/EDITOR membership. Browser roles cannot approve expenses or execute budget RPCs.
- A server-owned `p_request_id` UUID and unique `(shop_id,request_id)` constraint block a second reservation for the **same** logical request, including ambiguous acknowledgement. A retry gets RG005 and must **never** proceed to call the model, even if the original was settled.
- The verified predicted max cost is rounded **up** in PostgreSQL to one micro-USD before applying caps and inserting a receipt (as already done in the Python facade).
- Reservation and settlement remain service-role-only. An unsettled inference conservatively consumes the full maximum. Existing 0.05 USD per-call ceiling and default-deny expiring per-shop budget remain.
- All modified SQL is only run by disposable CI at local `127.0.0.1:54322` with an explicit marker. The old proposal is retained for audit but must not be re-applied in CI.

## Limitations and release gates
- An entirely **new** HTTP POST has a new request ID, so repeated deliberate POST submissions are not deduplicated. Azure lost ACK must not be retried automatically. A durable external HTTP submission journal is a separate follow-up before broad SaaS use.
- Check exact 4/4 branch and PR CI, including Postgres negative and actual two-session concurrency with different request IDs and same-ID lost-ACK denial. After merge verify independent main CI.
- Versioned migration was hand-assigned by coordinator because a Supabase CLI executable was not available in this tool runtime. Confirm the canonical CLI/version convention before deployment.
- Fresh hosted DEV read-only migration history is mandatory; migration `20261026173000_feature3_model_catalog_drafts.sql` precedes this file and may be unapproved. **Never blindly run `supabase db push`**, which could apply unrelated pending versions.
- Separate written protected DEV approval, specific project/ref, hash manifest, recoverable backup and restore test, maintenance window, and ROOT/operator acknowledgement required before hosted application.
- Operator must separately approve nonzero expiring synthetic shop budget and model rates/credentials. Real GPT-4.1-mini response has not been generated here.
- No GPU, model provisioning, Azure app setting, PROD or WineShopPOS changes.
