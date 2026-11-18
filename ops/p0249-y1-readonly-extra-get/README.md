# Issue #249 — next Y1 original-API read-only endpoint source

**Current status: SOURCE-ONLY, NOT PACKAGED/DEPLOYED/ENABLED.** Existing isolated Y1 still has exactly two indexed routes (`p0249_health`, `campaign_read`); original Flex stays live and intermittently times out.

## Original GETs staged here

- `GET /api/render-jobs/{job_id}` — calls original `HTTPAPI` → `RenderAPI.get` → original JWT-scoped `TenantStore.render_job`.
- `GET /api/poster-jobs/{job_id}` — calls original `HTTPAPI` → `PosterRenderAPI.get` → original JWT-scoped `TenantStore.poster_job`.
- `GET /api/poster-drafts/{draft_id}` — calls original `HTTPAPI` → `PosterDraftAPI.get` → original JWT-scoped `TenantStore.poster_draft`.

All three use strict GET-only v1 manifests. The original `cached_supabase_verifier` validates JWT cryptography/issuer/audience/expiry on every call; `TenantStore` is new for every request and passes the **caller JWT** to current PostgREST RLS. No service-role key, queue client, timer, renderer, AI model, subscription mutation, table write or privileged identity is constructed by these GET routes. The existing `HTTPAPI` can also handle writes, but these wrappers accept only GET and construct paths from hard-coded literal prefixes plus canonical UUIDs; they cannot dispatch arbitrary HTTP methods or paths.

## Two independent OFF-by-default gates

Both `RGAI_P0249_READONLY_SHADOW=true` **and a separate NEW flag** `RGAI_P0249_EXTRA_GET_SHADOW=true` are required, along with `RETAIL_SUPABASE_URL` and its public **publishable** key. This second flag is absent from existing Y1 and **not included in protected trial #939**. Without both flags the source returns fixed handler-marked `503 SERVICE_NOT_CONFIGURED` to properly shaped Bearer credentials; without Bearer it returns `401 UNAUTHORIZED` before importing JWT/DB or checking config. Invalid UUID returns fixed `400 INVALID_REQUEST`. No acceptance claim from synthetic 404s without authenticated user/tenant data.

## Verified source checks (no hosted acceptance)

`tests/infra/test_p0249_y1_extra_get_source.py` covers strict GET-only manifests, literal paths, canonical UUIDs, no-Bearer 401, both flags OFF 503, existing adapter composition without privileged key or queue, deferred JWT import, and sanitized 405/500 responses. `tests/infra/test_p0249_y1_extra_get_signed_two_shop.py` runs real original cryptographic JWT verification plus original HTTPAPI/RLS-aware TenantStore and render/poster status handlers against a fully synthetic signed two-shop fake PostgREST transport. It checks own-shop 200, deliberately leaked foreign-row 404, immediate membership revocation, invalid JWT claims/signature and **GET-only transport**. No real GoTrue users, Postgres rows or tokens are created; this is offline evidence only. Exact PR-head four-job CI remains mandatory.

## Required steps before any rollout

1. After current Y1 signed Auth-only 240s idle test is independently reviewed and genuinely passes with both disposable users, review these three new route sources and the original JWT/RLS, poster, job, and tenant requirements with affected leads. A source-only PR with four green CI jobs **is not** permission to deploy.
2. Independently prepare a **new** isolated-Y1 ZIP assembly and protected, manual-only deployment PR, with strict tag/SKU/region/ownership and original Flex unchanged checks; include original `http_api.py`, `security.py`, `tenant_store.py`, `render_api.py`, `poster_draft_api.py`, `poster_render_api.py`, original supporting models/dependencies, these three GET handlers, and existing `campaign_read` + `p0249_health` unchanged. Validate **exactly 5** GET-only function manifests and Python 3.12 v1 indexing offline **before any Azure write**; no worker or timer triggers, no real customer credentials.
3. Do not reuse the old one-time shadow-deployment workflow: its preflight expects **one** function (actual Y1 now has two) and would intentionally refuse overwrite. Require separate reviewed rollback of exact deployed ZIP and any extra temporary settings. New extra flag OFF until separate protected activation and E2E.
4. Hosted acceptance: real signed Auth users; own-shop result and foreign-shop/current-member revocation denial for each relevant endpoint; after 240s idle; per-route observed status/latency/handler marker; no SQL trigger outbox, quota or private data mutation; exact cleanup. DEV campaign inserts currently trigger outbox and subscription reservations and cannot be casually seeded. Do not switch frontend, paid provider, GPU, queue, PROD, or WineShopPOS while these steps are pending.

**Fresh comparison evidence (2026-11-17):** Original Flex [#40100546239 attempt 3](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40100546239) observed **6/9 anomalies**, including 18-second timeouts on exactly the three new read-status routes. Isolated Y1 [#42964811296 attempt 3](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) passed **40/40** health/unknown GETs and **12/12** handler-marked unauthorized GETs across two windows separated by 240 seconds. These are real hosted *anonymous/no-JWT* observations, not proof of hosted authenticated read parity.

No runtime routing, Azure, SQL, Supabase Auth, customer data or WineShopPOS mutations in this source PR. Issue #249 remains OPEN.

## 2026-11-19 — five-route source staging (stacked, no cloud deployment)

`stage_five_get_sources.py --target <new-empty-dir>` now copies only an explicit
allowlist of the original five Python v1 GET manifests/handlers plus unchanged
original auth, tenant, render/poster GET APIs and the pinned v1 dependencies
*requirements file*. It strictly rejects route/verb/trigger/binding changes,
unknown dependency pins, missing or symlinked originals and pre-existing
staging destinations **before any staging output is created**. It does not
install dependencies, create a deployable ZIP, touch Azure app settings or
start any endpoint. The isolated Y1 still hosts only the existing two routes.

The new `tests/infra/test_p0249_y1_five_get_source_stage.py` exercises the
real source files, rejects extra queue triggers and unsafe package inputs,
and checks verbatim bytes of each staged original source. This work is
*stacked on unmerged #968*; independent source/security review, exact-head
four-job CI, then a **separately approved** vendored ZIP, indexed five-route
deployment and real signed two-shop/idle acceptance are still mandatory.
Do not enable the second flag or cut over the frontend. Issue #249 stays OPEN.
