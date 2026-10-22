# RetailGrowthAI HTTP adapter — milestone 1

**No cloud deployment.** Python Azure Functions v2 entrypoint `function_app.py` exposes:
- `POST /api/campaigns` — returns **503 until durable queue milestone**; never persists unqueued jobs.
- `GET /api/campaigns/{id}` — verifies asymmetrically signed Supabase Auth JWT (ES256/RS256), issuer, audience, expiry and user subject; reads tenant-authorized RLS rows using the *user token*.

Environment: `RETAIL_SUPABASE_URL` (dedicated HTTPS project) and `RETAIL_SUPABASE_PUBLISHABLE_KEY` (non-secret). Never use WineShopPOS keys; never expose a service role key. HTTPS-only verification and exact project JWKS; HS256 legacy tokens fail closed until asymmetric signing is configured.

The Azure Functions app is not provisioned or hosted; cross-origin access must be allowlisted in Azure Functions before use. No signup, queue, rendering or new cloud resources are created here. For this stage, any live request to POST receives 503, by design. Next PR adds a durable write/queue adapter, tests and deployment readiness gates.

Install locally from Git Bash: `cd azure-functions/campaign-api && uv pip install -r requirements.txt` into an activated venv; package `ai_agents` separately for runtime. CI validates security via `uv run --with PyJWT[crypto] --with pytest` and never needs cloud credentials.
