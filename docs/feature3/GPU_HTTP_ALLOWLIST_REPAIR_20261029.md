# Feature3 real HTTP store path repair — 2026-10-29 (source only)

## Root cause

The already-implemented `Feature3V2API.gpu_jobs` / `gpu_download` call `TenantStore.feature3_gpu_jobs` and `feature3_gpu_job`, but `TenantStore._request` did not allow the table `feature3_gpu_jobs`. Actual requests raised `ValueError('unsupported table')` BEFORE making their JWT/RLS-scope PostgREST read. Existing tests monkeypatched `_request`, so they did not catch this end-to-end source-level failure.

The existing `Feature3GPUServiceStore.commit_private_output` and `Feature3GPUOutboxService.claim_dispatch` / `confirm_dispatch` / `audit_recovery` likewise used RPC paths missing from the `AdminStore.request` allowlist. Actual backend-only calls raised `ValueError('unsupported worker path')` without reaching the deployed v31 PostgREST functions, even though RPC-specific tests had mocked `store.db.request`.

## Source changes

- `azure-functions/campaign-api/tenant_store.py` now permits **GET only** for `feature3_gpu_jobs`. User-signed JWT and publishable key still flow through `TenantStore._request`; existing post-query exact shop/job checks, role checks, object namespace and 60s signed private URL remain unchanged. Browser writes to `feature3_gpu_jobs` and browser RPC access are *still denied*.
- `azure-functions/campaign-api/admin_store.py` adds exactly four existing **POST-only backend-secret RPCs**: `feature3_commit_gpu_private_output`, `feature3_claim_gpu_dispatch`, `feature3_confirm_gpu_dispatch`, `feature3_audit_gpu_recovery`. All other unapproved paths remain rejected; the service-only SQL and RLS still decide authorization/financial state. This is NOT GPU enablement or a new spending endpoint.
- `tests/api/test_feature3_gpu_http_transport_allowlist.py` uses genuine Python `urllib.request.Request` objects with an injected in-memory HTTP transport. It exercises the real `TenantStore -> Feature3V2API` history/download flow, tenant denial, foreign output, existing 60s signing, the real `Feature3GPUServiceStore.commit_private_output` call, real `Feature3GPUOutboxService` dispatch/recovery RPCs, and rejection of user write attempts and unknown/non-POST privileged paths. No real network, private credentials or paid provider.

## Remaining release gates

This closes **only the source-level transport allowlist blocker**. The generated history/download routes are still behind Feature3 rollout flags; no hosted Azure source deploy or live JWT/Storage test occurred. Supabase DEV must be verified separately for live RLS/subscription/source approval and exact current schema; the previously confirmed 31 canonical migrations were not modified. Existing signed URLs can remain usable until their **60-second** expiry after a user/model is revoked: newly issued links are checked under current JWT/RLS, but pre-existing signed links are NOT instantly revocable. Server-proxied per-request authenticated download or Storage object revocation requires a separate reviewed architecture/implementation and real hosted negative tests.

Safe dependency order for coordinator: merge reviewed Storage one-shot ACK fix #629, financial unknown-output fence #632, worker composition #634 and zero-secret queue v1 #636 with exact-head/postmerge 4/4 CI; combine this transport repair without enabling GPU. Demo input byte consumers #630 remain separate and strictly not VTON or publish-approved. Azure #249 is unrelated and still open. Never touch PROD/WineShopPOS or paid GPU without explicit release gates.
