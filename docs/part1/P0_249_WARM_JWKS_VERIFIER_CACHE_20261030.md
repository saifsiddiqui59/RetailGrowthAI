# Issue #249 — bounded warm JWT verifier reuse (2026-10-30)

**Status: source candidate only. The original Python Flex ~61-second unmarked gateway 503 is NOT fixed or explained by this change.**

## Observed source behavior and narrow improvement

The original `function_app.build_api()` constructs `SupabaseJWTVerifier(url)` for **every** protected HTTP request. That constructor allocates a fresh `PyJWKClient`; consequently its five-minute project JWKS set cache could not benefit subsequent warm requests, potentially causing a repeated network fetch and additional signed GET latency.

The HTTP adapter now reuses one `cached_supabase_verifier(url)` per exact configured Supabase origin. The cache holds the verifier only, **not** a user JWT, verified session/claim, role or membership; it changes when the configured origin changes. Every request cryptographically re-verifies JWT signature, issuer, audience and expiry and then runs caller-token RLS authorization. `cache_keys=False` turns off PyJWT's indefinite per-kid public-key cache, while `cache_jwk_set=True` retains only the bounded 300-second JWKS set with a 5-second network timeout. Unknown signing kids trigger a JWKS refresh per normal PyJWT behavior. No secret, service-role privilege or unapproved fallback introduced.

Unit regressions: same-origin warm caching, different-origin isolation and no retained per-origin verifier across a config change, bounded JWKS constructor options, repeated signed/expired/bad-algorithm token checks with the same warm verifier, and exercising the **actual source** `build_api` with inert local stubs to verify fresh per-request tenant-store objects. All tests offline without Azure, JWT secrets, roles, paid models or HTTP traffic.

## Coordinator/validation handoff

Scope: `azure-functions/campaign-api/security.py`, `azure-functions/campaign-api/function_app.py`, `tests/api/test_jwt.py`, this doc. PR head must pass fresh four-job CI; coordinator alone merges and checks postmerge main 4/4. This reduces *possible repeated JWKS network calls on warm signed paths*, **not** platform ingress / scale-group cold start or pre-handler gateway 503. A real signed two-shop live acceptance and full Azure ingress→instance trace remain separate approval/dependency gates. Do not enable paid GPU or modify PROD/WineShopPOS.
