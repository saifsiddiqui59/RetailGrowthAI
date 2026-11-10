# Feature #3 GPU-OFF private output SQL CAS — source handoff

Date: 2026-10-28. All work remains **source-only**. GPU OFF. No hosted Supabase SQL, Azure deployment, paid model or WineShopPOS operations.

## Actual code
- `20261028230000_feature3_gpu_private_output_cas.sql` adds a service-only immutable `retail_private.feature3_gpu_output_evidence` row with content-addressed SHA, exact job/media/claim token/attempt, source IDs, byte count and `UNREVIEWED` state.
- New `public.feature3_commit_gpu_private_output` atomic RPC locks the original one-attempt RUNNING claim, validates unexpired lease, RESERVED prepaid ledger, active OWNER/EDITOR, current subscription and exact DRAFT design revision/SHA, same-shop registered source assets, model approval where applicable, and private PNG Storage metadata. It inserts one private `media_assets` record and one immutable evidence row in the same transaction, without settling the reserved bill or approving the image. Duplicate/stale/foreign claims yield null.
- New restrictive `storage.objects` policies prevent normal authenticated users from inserting, overwriting or deleting the reserved `{shop}/feature3/gpu/` prefix, without changing other original upload paths or private read permission. Only the trusted server's service Storage writer may stage this prefix.
- Existing `Feature3GPUServiceStore.commit_private_output` sends one service-key PostgREST RPC with strict request/receipt checks, never replays an uncertain POST and never returns browser object paths.
- New `poster_feature3_gpu_output_cas_negative.sql` performs disposable rollback security and positive/negative SQL metadata tests; `test_feature3_gpu_output_cas_transport.py` mocks service POST/ACK and failure paths. Migration inventory/capability preflight recognizes the new version and retains `authorized_to_apply=false`.
- PR #562 is a **separate** GPU-off `PrivateOutputRegistrar` that validates actual local bytes and stages the object; this SQL transport is the proposed transaction callback for future coordinator wiring. No automatic merger or provider invocation.

## Critical boundaries
PostgreSQL only checks **Storage metadata**; it cannot SHA256 the actual Supabase object bytes. The trusted worker must verify actual private PNG bytes and storage ACK before calling this SQL. A customer-supplied license string, fictional PNG, hosted RLS test, or a returned private asset is never real commercial/right-to-use evidence. The real independent source/likeness authorizer must run both before staging and immediately before output consumption. The SQL's media row intentionally has `license_name=null`, so an unreviewed generated output is not independently licensed for other features.
The existing settlement RPC remains separately fenced, and there is **no** automatic retry of an uncertain paid attempt or unknown output commit. Real signed download/review eligibility must check current rights and review state before publishing. An actual post-upload private-object SHA readback, durable queue dispatcher, poison/cost reconciliation and real model-output human fidelity acceptance remain unfinished.

## Release conditions
Coordinator reviews all source PRs and shared changes, exact-head 4/4 and post-merge main 4/4. Independently approve versioned RetailGrowthAI DEV migration, protected one-shot real Storage bytes/SQL QA, signed tenant/curator tests and reversible rollback. No part of this PR is permission to apply hosted DDL or start A100/T4/FLUX.
