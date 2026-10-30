# Feature3 P0: signed human model review/revocation HTTP route — source only

Date: 2026-10-28. Source work continues without upstream feature inputs; GPU OFF.

New server-side routes:
- `POST /shops/{shop_id}/feature3-models/{model_id}/review`
- `POST /shops/{shop_id}/feature3-models/{model_id}/revoke`

Both use the **existing** HTTPAPI `SupabaseJWTVerifier` asymmetric signed
JWT verification, then `TenantStore.member(...,write=True)` to require a
CURRENT same-shop active OWNER/EDITOR; the signed review/revoke PostgREST
store sends the SAME user token to the previously merged
`public.feature3_review_model`/`public.feature3_revoke_model` SQL RPCs.
The SQL independently derives `auth.uid()`, checks current rights, expected
image SHA/evidence and CAS revision, and writes a durable review event.
The client cannot pass a reviewer identity, a Storage path or auto-approve
via the backend. Review requires EXACT six review booleans and notes; revoked
rights can be withdrawn without a currently valid external license. Failed
decisions return a generic 409 and are **not retried**.

**Two activation gates default OFF:**
`RETAIL_FEATURE3_V2_ENABLED=true` and independent
`RETAIL_FEATURE3_MODEL_REVIEW_ENABLED=true`. No public GPU POST endpoint,
service-role evidence insert, paid inference or media download is added.
Neither gate has been set by this source change. The corresponding
private evidence model-review DB migrations still require separate
owner-authorized DEV deployment and genuine account/rights testing.

Offline tests `tests/api/test_feature3_model_review_http.py` use fictional
user/model/shops and a fake JWT verifier; role, expired auth, foreign shop,
wrong method/path, forged extra fields, ambiguous ACK and no-retry are
checked. This does **not** prove actual signed-in hosted authorization or
independently licensed fashion models.

Remaining: real original commercial model/garment rights and signed live
import, verified backend rights source and service-only write, independently
reviewed human model/try-on; encrypted private generated output, queue/lease,
replay/cost, Feature2/4/5 reference consumer tests, genuine visual quality,
hosted E2E and Azure #249. Keep GPU OFF until separately authorized.
No WineShopPOS/PROD/cloud writes.
