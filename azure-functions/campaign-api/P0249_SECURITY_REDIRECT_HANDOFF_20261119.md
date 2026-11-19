# #249 current-main PostgREST transport security slice — 2026-11-19

Original larger security [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965), head `63f5cbe4bbc3840b3ced6aeb60938976137782bc`, changes 12 files touching shared auth, JWT verifier, root Azure app and privileged stores. This focused current-main slice restores only:

- `tenant_store.py`: reject unsafe initial HTTPS origins, **never follow a 30x redirect while carrying user JWT**, close HTTP error sockets on every denial.
- `admin_store.py`: same strict HTTPS origin validation, **never follow redirect while carrying a service-role API key** (including mutating RPCs), close error sockets.
- Exact original negative-test Git blobs `test_p0249_admin_store_redirects.py` SHA `d43028356c743edfadfaa46c7fe99d768aae1378` and `test_p0249_tenant_store_redirects.py` SHA `d6f4620d8322e543101d17096461112134221092`.

Existing newer current-main RPC allowlists, tenant membership, method restrictions and privacy behavior are retained. This PR neither imports the obsolete root Azure Functions router nor changes JWKS error classification, routing, cache, billing, queues, host configuration, deployment or SQL migrations. The other original #965 changes remain **review pending** and are **not** DONE.

Run `python -m unittest tests.infra.test_p0249_admin_store_redirects tests.infra.test_p0249_tenant_store_redirects` and mandatory exact-head 4/4 CI. Global auth/privileged service transport requires **independent affected lead/security review** before merge; no self-approval based only on green CI. This source fix does NOT resolve original markerless Flex HTTP 503 or certify DEV live RLS, p95/p99, old or new Y1 production endpoints.

GPU/OPEX paid model OFF; Azure/DEV/PROD resources and WineShopPOS untouched.

## Same-current-main batch: isolated JWKS outage classification

Source-only extension from original #965 to the existing already-cached project verifier: `security.py` distinguishes `PyJWKClientConnectionError` (sanitized `SigningKeysUnavailable`) from `jwt.PyJWTError` invalid signature/kid (401); the original `HTTPAPI` and Feature2 trend/draft reader map the temporary outage to fixed sanitized 503 bodies. Every JWT is still signature/issuer/audience/role/expiry checked; this is NEVER an unsigned fallback or provider retry. Existing `function_app.py` uses `cached_supabase_verifier` on current main and is **not replaced** by older root code.

Restored exact original negative regression files:
- `tests/infra/test_p0249_jwks_outage_classification.py` old SHA `5ad89e93b7476a34a0ae28360d3d944c4919757a`.
- `tests/infra/test_p0249_feature2_cached_verifier.py` old SHA `b1ead1811989cff4e963671dba4a4a688f875a8f`.

Prior PR CI #44460641511 **4/4** predates this extension; it MUST NOT be counted for the new head. Run focused Python suites and all four required exact new-head CI jobs, then obtain independent JWT/RLS service-role security review before any source merge and new exact-main CI. This source-only change does not fix original Flex 503, deploy cloud routes, activate Y1, or establish hosted customer proof.

## Original root Feature2 builder defect detected by actual CI

The exact-new-head Python regression in GitHub Actions #44462808283 exposed a preexisting **real Functions enabled-code NameError**: `function_app.py` imports only `cached_supabase_verifier`, but `build_feature2_api()` still called now-unimported `SupabaseJWTVerifier(origin)`. This can produce a nonfunctional Feature2 route whenever enabled; it is not an acceptable reason to classify all real 503s as resolved. Ported the historical #965 one-line correct source usage against the current-main builder and preserved the original test source blob `test_p0249_feature2_cached_verifier.py`. The two tests previously failed with `NameError` and wrong AST call, now require an exact new-head four-job CI rerun. No role, claim, external provider, or SQL approval was enabled. All code remains **review-blocked** for independent shared Functions/auth security review before main merge.
