# Y1 full backend migration — protected cutover workstream (#249)

**This PR prepares code; it does not deploy Y1 or disable Flex.**

## Existing live evidence (2026-11-22)
Protected Y1 run [#45021333842](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/45021333842) deployed exactly five read-only functions. Indexed **5/5**, public HTTP **20/20 twice** separated by 240 seconds and unauthenticated **8/8 401**. It did not install any write handlers, render/queue consumers, timer recovery, billing parity or frontend cutover. Original Flex remains the worker and write host.

## New HTTP artifact (source only)

`ops/p0249-y1-cutover/prepare_http_only.py --check` audits the existing original Flex `function_app.py` and expects exactly its 30 reviewed HTTP handler registrations and nine background registrations. It refuses new/unreviewed registrations. For a prebuilt, **already-verified** existing Flex release ZIP, `--source-zip ... --output-zip ...` rewrites only the nested `azure-functions/campaign-api/function_app.py`, removing **all nine** `@app.queue_trigger` and `@app.timer_trigger` registrations and preserving HTTP handlers, original JWT/RLS tenant code, `HTTPAPI`, durable outbox/queue writes and exact reviewed packaged dependencies. It re-adds the original Y1 health route with the same response/marker. Input/output ZIPs must pass the original builder's independent package/FFmpeg/license verification. No Azure writes.

**This is an intermediate stage:** Y1 HTTP requests can in principle enqueue to the existing authorized `RETAIL_STORAGE` queues while *Flex remains the only worker owner*. The artifact does not index a second timer or queue consumer, but HTTP parity is not live until separate protected deployment, configuration and real signed verification. The Y1 artifact preserves unchanged original backend API logic; this does not assert that all optional Feature2/3/4/VoiceStudio routes are ready or enabled.

## Actual connections required before Flex retirement

1. **Authorization/data:** Same dedicated Supabase DEV URL, public JWT verifier and server-only service key. Verify fresh signed JWT, current OWNER/EDITOR/VIEWER RLS, own/foreign/revoked reads, campaign writes, subscription/quotas, private media downloads, no redirects or other-project access.
2. **HTTP API:** Y1 has all required indexed GET/POST/PATCH and feature-specific enabled paths, original response/body/error semantics, exact trusted CORS origin and frontend routing. Exercise original POST/PATCH, jobs, media rights and both successful/failed cases.
3. **Durable jobs:** Reuse only existing DEV `RETAIL_STORAGE` queues (`retail-campaign-planning`, `retail-reel-render`, `retail-poster-render`, poison queues) and one authoritative PostgreSQL outbox/claim/lease/quota ledger. Do not enable Y1 background functions while Flex background functions are active in a way that permits duplicate timer/poison or conflicting reconciliation. Audit backlog, in-flight claims, retries and billing idempotency.
4. **Worker transition:** Deploy and separately verify Y1 planning, FFmpeg/video, poster, poison and recovery workers using original package, private Storage, 20-minute host/780-second encode guard and least-privilege credentials. Controlled single-owner handoff with rollback; no dead queue or billable double processing.
5. **Traffic and reliability:** After signed Y1 functional E2E, switch *every* Free SWA DEV API source from Flex hostname to Y1 hostname; inspect served deployed JS/config, rather than trusting source flags. Verify 503 cold/warm, p95/p99, media/queue latency, 240s idle, no pending jobs and a functional rollback to original before stopping Flex. Then stop only **the exact original RetailGrowthAI DEV Flex Function App**, monitor, validate after stop, and optionally retire the Flex plan only under a separate guarded owner-authorized Azure change.

## Stop/close decision

Do NOT disable `rgai-dev-functions-d4e5ddbd` or delete `rgai-dev-flex` now. The live Y1 package is GET-only and would cause an outage. Do NOT close #249 until hosted Y1 fully replaces the original connection paths, its workers are proven, old Flex is no longer routing traffic, and independent post-cutover health/rollback/latency acceptance passes. The user's other chat owns campaign test execution: this branch only prepares Y1 host packaging and connection ownership, not duplicate shop fixtures.

No PROD, GPU, paid provider, WineShopPOS or global auth approval mutation.
