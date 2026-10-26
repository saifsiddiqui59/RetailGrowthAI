# Feature #2 — Real Azure model activation, source integration (not paid DEV inference)

As of 2026-10-26, source implementation is split into [#401](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/401), [#402](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/402), and [#403](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/403).
This document **does not** authorize a model charge or production release.

## What is now implemented as code

- `ai_agents.feature2_llm.AzureFeature2PromptLLM`: actual Azure Foundry/OpenAI-compatible v1 chat HTTP model for retailer prompt revision (not deterministic).
- `ai_agents.feature2_ai_writer.AzureFeature2ContentLLM`: actual structured 1–7 day LLM writer for distinct Instagram, Facebook, LinkedIn, YouTube, poster and 30-second Reel scene *copy*. `create_ai_content_draft` attaches only reviewed copy to the existing canonical campaign; identifiers, assets, licensing, storyboard timings and DRAFT status are created by trusted local code.
- `ai_agents.marketing_guidance`: original compact writing/editorial guidance inspired by MIT-licensed upstream `coreyhaines31/marketingskills`; no executable third-party agent copied or loaded.
- `feature2_ai_budget_store.Feature2BudgetStore`: backend service-role-only RPC facade, always reserves a conservative maximum first and settles actual usage after model response; unsettled reservations remain charged at their upper bound. A money/tenant quota must be approved in durable Postgres BEFORE any paid request.
- `feature2_ai_activation.Feature2AiActivation`: joins the trusted caller identity, reserved budget, true HTTP inference and settlement.
- `/api/shops/{shop_id}/improve-prompt-ai` and `/api/shops/{shop_id}/content-drafts-ai`: additive signed OWNER/EDITOR routes. The latter also requires a genuinely verified, relevant unexpired trend and registered licensed image, exactly as the original template-based DRAFT path.
- The `/trends` UI has a new explicit **Use real Azure AI model** checkbox, OFF by default. Old free routes unchanged; no automatic fallback to pretend a paid generation occurred. The existing one-POST/no-retry and signed shop history reconciliation is preserved.
- Unit tests simulate the **real Azure v1 HTTP protocol** with local injected fake transports; they do not prove that an actual paid model executed or that hosted JWT acceptance succeeded.

## Hard gates that intentionally prevent paid inference today

1. Real AI is off unless the Azure Functions server environment has `RETAIL_FEATURE2_REAL_AI_ENABLED=true`; not a browser `VITE_` setting.
2. Server-only `RETAIL_FOUNDRY_ENDPOINT`, `RETAIL_FOUNDRY_DEPLOYMENT`, `RETAIL_FOUNDRY_API_KEY`, and reviewed model rate values `RETAIL_FEATURE2_INPUT_USD_PER_MILLION`, `RETAIL_FEATURE2_OUTPUT_USD_PER_MILLION`, `RETAIL_FEATURE2_MAX_CALL_USD` must be configured. The last value is bounded to **USD 0.05/request**; verified Azure provider pricing must be added by an operator, never guessed. Do not expose the API key in source, logs, frontend bundle or test fixtures.
3. The reviewed atomic-budget SQL is ONLY a non-executable proposal at `docs/feature2/sql/PROPOSED_20261026_feature2_ai_cost_ledger.sql`. A coordinator must assign a compatible executable migration version, update the project migration manifest, prove disposable Postgres migration order/RLS/concurrency/permission tests, and independently authorize a protected DEV migration. The SQL has **no default-enabled shops**.
4. An explicitly operator-approved positive spend cap and expiry is required for each test shop, plus an active subscription and real signed OWNER/EDITOR user JWT. The RPC verifies those conditions under a subscription row lock. An unconfigured, missing or failed RPC means **no model request**.
5. Real hosted sample validation requires approved DEV deployment on the existing Azure Functions/Free SWA, a test shop with the real approved budget, a genuinely deployed text-capable model and credentials, then a ROOT-authorized disposable user account, finally archived real model response and logged token/cost accounting (no secrets). The full trend→media→DRAFT E2E additionally requires genuine current relevant trend and a rights-cleared, registered image.
6. Never convert Azure #249 gateway lost ACK into an automatic duplicate paid inference or DRAFT POST. For true once-only charged AI generation on retries, durable correlation/idempotency should be reviewed before expanding beyond this manual opt-in pilot.

## Cost and completion truth

The implementation works against a real model **in principle** (the model HTTP path is coded, validated and tested with a stub). Until gates 1–5 are satisfied and a signed hosted model response is collected, status is **source merged / opt-in model disabled**, not “Feature2 real paid AI fully live.”
No GPU, new paid compute, separate data store, Wan, PROD, WineShopPOS, social publishing or automatic spend has been activated here.
