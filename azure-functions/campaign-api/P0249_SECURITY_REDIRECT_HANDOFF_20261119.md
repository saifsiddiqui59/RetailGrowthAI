# #249 current-main PostgREST transport security slice — 2026-11-19

Original larger security [PR #965](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965), head `63f5cbe4bbc3840b3ced6aeb60938976137782bc`, changes 12 files touching shared auth, JWT verifier, root Azure app and privileged stores. This focused current-main slice restores only:

- `tenant_store.py`: reject unsafe initial HTTPS origins, **never follow a 30x redirect while carrying user JWT**, close HTTP error sockets on every denial.
- `admin_store.py`: same strict HTTPS origin validation, **never follow redirect while carrying a service-role API key** (including mutating RPCs), close error sockets.
- Exact original negative-test Git blobs `test_p0249_admin_store_redirects.py` SHA `d43028356c743edfadfaa46c7fe99d768aae1378` and `test_p0249_tenant_store_redirects.py` SHA `d6f4620d8322e543101d17096461112134221092`.

Existing newer current-main RPC allowlists, tenant membership, method restrictions and privacy behavior are retained. This PR neither imports the obsolete root Azure Functions router nor changes JWKS error classification, routing, cache, billing, queues, host configuration, deployment or SQL migrations. The other original #965 changes remain **review pending** and are **not** DONE.

Run `python -m unittest tests.infra.test_p0249_admin_store_redirects tests.infra.test_p0249_tenant_store_redirects` and mandatory exact-head 4/4 CI. Global auth/privileged service transport requires **independent affected lead/security review** before merge; no self-approval based only on green CI. This source fix does NOT resolve original markerless Flex HTTP 503 or certify DEV live RLS, p95/p99, old or new Y1 production endpoints.

GPU/OPEX paid model OFF; Azure/DEV/PROD resources and WineShopPOS untouched.
