# RetailGrowthAI E2E test handoff (isolated, not deployed)

This branch owns only tests/e2e/** and frontend/e2e/**. It does **not**
modify global scripts, GitHub Actions, production resources or WineShopPOS.

## What is exercised

- tests/e2e/test_campaign_journey.py: real Python HTTPAPI, DraftAPI and RenderAPI
  handlers driven by a tenant-aware in-memory store, fake durable queue and
  fake completed render. Exercises API creation/GET, seven-day draft contract,
  optimistic PATCH, render queue idempotency, job GET, private download signing
  and denial paths for forged auth, foreign shops/assets, VIEWER/revocation,
  queue faults, edit conflicts, unlicensed sources and pending downloads.
- frontend/e2e/campaign-journey.spec.mjs: Chromium Playwright against the
  real React/Vite UI and its real browser API clients. The external Supabase
  and Azure API **origins are intercepted**; the tests use dummy credentials
  and route.fulfill fixtures. Flows include login, real browser-form upload
  with test bytes and user-declared rights, campaign submission, seven-day
  draft polling, edit/Save day, render status polling, signed-link navigation,
  and login/tenant/VIEWER/registration/conflict/render/download failures.

## Run locally (Git Bash, from repository root)

API boundary tests (same Python environment as the existing CI job):

    uv run --project ai-agents --with pytest --with "PyJWT[crypto]==2.10.1" -- python -m pytest -q tests/e2e

Browser tests (requires Node 22+, Chromium download; never use live secrets):

    cd frontend
    npm install --no-audit --no-fund
    cd e2e
    npm install --no-audit --no-fund
    npx playwright install chromium
    npm test

Playwright starts a Vite server with local test-only environment values. All
third-party origin calls are mocked; do not set live SUPABASE/Azure URLs.
The test uploads only 128 bytes with a PNG signature to a mocked endpoint;
it is not a real licensed image. The signed-link response is a stub, not a real MP4.

## Coordinator CI integration needed

The existing four jobs do not discover these paths: frontend/package.json
lists three explicit Node tests, and the Python job lists tests/api and other
named directories, but not tests/e2e. **A green existing four-job run does
not mean these new tests ran.** Coordinator owns .github/workflows/** and
frontend/package.json. Ask coordinator to add a separate optional browser E2E
job (npm installs, playwright install chromium, npm test in frontend/e2e) and
append tests/e2e to the Python pytest command. Keep job permissions read-only,
run against offline mocks, never supply secrets, and do not disable existing
checks. Commit a reviewed lockfile here before adopting npm ci.

## Outside the scope of mocked E2E

Not verified: cryptographic JWT against real JWKS; real Supabase Auth,
RLS/PostgREST/storage/network CORS; database migrations; queue delivery or
crash-recovery; FFmpeg/video codecs; storage signatures issued by Supabase;
true file download and 30-second licensed media; deployed Azure Functions,
billing, browser accessibility/performance, or production publish readiness.

After explicit RetailGrowthAI DEV authorization/deployment, create a separate
staging-only suite with non-production test users/shops, rights-cleared images,
and verified MP4 bytes. Never point these offline mocks at WineShopPOS.
