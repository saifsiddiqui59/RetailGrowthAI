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


## 2026-10-26 — Source promotion checkpoint; release remains gated
- #431 merged: source canonical migration `20261026194000_feature2_ai_cost_ledger.sql`, 5th request UUID arg, RG005 fail-closed repeated spend, micro-USD rounding; disposable SQL and 4/4 branch/PR/main passed. #433 merged: signed DRAFT submission UUID bound to reservation. No call may be retried after lost Azure/backend acknowledgement.
- Fresh hosted **READ-ONLY** DEV `jeearzffnjbvghwjjjrf` migration history 21 applied, 2 later source versions (Feature3 first and Feature2 second); AI budget tables null, registered media/drafts 0. Do not run unscoped `db push` or apply either without independent written protected approval and tested restore. Do not enable Feature2 flags until actual expiring shop spend cap approved.
- Existing model `rgai-gpt-41-mini` region South India confirmed by OIDC #40382879442. Third-party published Regional Standard prices $0.44/$1.76 per million input/output are **indicative**; query official Azure Retail Prices exact `southindia` SKU and contract before budgeting or configuring rates. No paid sample has been run; proposed USD0.20 remains unapproved. Trend-backed draft needs genuine clothing signal and owner-cleared tenant media; text-only isolated actual inference remains an independent gated step.


## 2026-10-26 — Verifiable Microsoft regional token price, still zero live model calls
- OIDC #40401262949 verified existing South India GPT-4.1-mini Regional Standard S0 and official Microsoft Retail Prices API $0.44 uncached input/$1.76 output USD per million (unit originally 1K; multiplied by 1000), effective 2025-11-01. No credentials read, no inference or Azure configuration writes; account-specific billed rate is not verified. User separately approved max $0.20 total synthetic DEV test, but protected schema/ROOT and expiring per-shop reserve remain unapplied. Do not enable paid flags or attempt billable inference without these gates.


## Feature2 2026-10-27 — LIVE DEV migration verified, paid generation legitimately gated
- Owner waived Supabase backup and canonical cost migration `20261026194000` is now hosted with 22 exact versions, both service-only/RLS cost tables, zero enabled budgets and no money spent. Real protected canary #40469565233 reached no Azure model network call: `/shops` HTTP403 from correct signed-owner trigger. One synthetic GoTrue actor exists without shop, onboarding request PENDING. Source #441 retries **no model call** until a genuine Platform Super Admin approves the pending user through the existing audited Platform Control `/platform-admin` workflow. Never use SQL SET ROLE/JWT forgery or bypass gated service-only spend controls. Run only one signed manual DEV canary with expected US$0.20 total maximum after approval.


## 2026-10-27 — LIVE success: one bounded Azure GPT-4.1-mini seven-day DRAFT
- **REAL inference now proven** in protected run #40489632633; model `gpt-4.1-mini-2025-04-14` returned valid 7-day JSON, 623 prompt/2440 completion tokens, estimated campaign cost $0.00456852 from published South India prices, actual SQL campaign settlement $0.004569. Exact artifact 12728895512 under that GitHub Actions run (expires 2026-11-03 UTC). Independent main 4/4 CI #40489632525. One synthetic signed OWNER, legitimate admin-approved signup, tested browser spend-RPC denial, capped cost. Budget disabled and membership revoked afterward. No actual hosting of draft, trend lookup or licensed media; no social publication.
- Separate prompt-improver inference FAILED_NO_RETRY; budget row for `prompt` remains `RESERVED` $0.002030, eventual bill unknown. Do not replay without a **new explicit paid-test approval and reconciliation**; do not settle it to 0 without evidence. Keep `RETAIL_FEATURE2_REAL_AI_ENABLED` off for unrelated users. Source review and costs: `docs/feature2/REAL_AZURE_7_DAY_ACCEPTANCE_20261027.md`.
