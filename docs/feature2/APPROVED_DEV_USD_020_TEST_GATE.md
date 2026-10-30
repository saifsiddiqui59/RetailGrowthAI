# RetailGrowthAI Feature2 — owner-approved US$0.20 isolated DEV AI test scope

Date of operator decision: **2026-10-26**. Tracking [issue #403](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/403). After explicit question that separated paid-test scope from hosted DDL approval, the user answered **"do it"**.

## Approved
- Maximum **US$0.20 total** across this ONE isolated synthetic RetailGrowthAI DEV text-model acceptance exercise. This is NOT a daily, per-call, per-shop-multiplier or monthly allowance.
- Reuse only the existing South India Azure OpenAI S0 `rgai-dev-openai-d4e5ddbd`, Standard `rgai-gpt-41-mini`. No new model, dedicated compute or GPU.
- One genuine prompt-improvement request and one genuine seven-day Thread & Loom Studio, Nagpur, kurtis TEXT-ONLY content sample once all separately protected DB/identity/security requirements are satisfied.
- A server-enforced maximum of **US$0.05 per AI request**, and a cumulative, single-shop **US$0.20 maximum cap** expiring as soon as the approved test finishes; no blind retry and no automatic publishing.

## Not approved: hard stop
- Applying new SQL DDL to hosted DEV, reordering/migration-repairing the independent Feature3 migration, touching PROD or WineShopPOS, creating identity accounts or changing live retailer subscriptions.
- Opening server-only keys to public CI/frontend, enabling Function App real AI before reviewed protected release, provisioning models or paid infrastructure.
- Spending above US$0.20, or repeating the same approval for more testing after the exercise is closed.
- Since the currently hosted DEV ledger tables are ABSENT and 2 unapproved later source migrations exist, real billable calls must remain disabled until separate protected DDL and test-fixture approval, exact version/order and recovery are independently satisfied.

## Reconciliation record
- Fresh authenticated read-only `list_migrations` on RetailGrowthAI DEV `jeearzffnjbvghwjjjrf`: **21** applied through `20261026152102_p0_249_reel_render_intent`.
- Fresh read-only SQL: `public.shop_ai_budget_controls` and `public.shop_ai_spend_reservations` ABSENT; zero `media_assets`, zero `shop_content_drafts`. No write was performed.
- Latest merged `main` at authorization: `0805b23816da7f2ee2ab00bc2bfb4715d6769b72`, main CI #40394477895 **4/4** success.
- Source-only model and cost path already merged: #405, #409, #410, #411, #417, #427, #431, #433; new source-only readiness probe is NOT an Azure billable action.
- Source order: protected Feature3 migration `20261026173000` precedes Feature2 ledger `20261026194000`; **NO blanket `supabase db push`**.

## Cost-rate gate
An operator must independently compare the existing Azure subscription's actual contractual charge with **Microsoft's public Retail Prices REST API** regional Standard uncached input/output meters. Use the read-only price probe in `scripts/ci/feature2_price_probe.py` as a public list-price audit; it does NOT assert a contract discount, tax treatment or authorization to set Function App billing rates. If prices cannot be verified exactly, stop.

## Actual result
**Total model requests executed under this approval here: 0. USD spent: $0.00.** Future real token usage, cost and seven distinct generated topics must be recorded from Azure's actual response before status can change. CI/mock output must never be mislabelled.


## 2026-10-26 — Public meter rates independently verified; no spending yet
- Microsoft actual REST public price data confirmed in protected read-only OIDC [#40401262949](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40401262949): South India GPT-4.1-mini Regional Standard $0.44 input and $1.76 output per 1 million (converted from Azure's USD/1K meters). No secret was read, no model API called. This is not evidence of applicable account contracted rate. Limit remains **US$0.20 TOTAL** across single isolated DEV synthetic test, **US$0.05 max per call**, no standing spend authority.
- Separate protected hosted migration+rollback, exact-root-approved synthetic accounts, service-owned budget grant and expiry are still missing; keep real model disabled with **0** requests and **USD0.00** actual spend so far. No WineShopPOS/PROD.


## 2026-10-27 — Scoped one-time DEV spend allowance USED; budget now disabled
- Owner's prior $0.20 cumulative allowance has been used for one synthetic seven-day Azure text acceptance plus one prompt improvement attempt. It is **not** a standing license to retry or enable further calls. Protected GitHub Actions #40489632633 verified seven-day campaign DRAFT real GPT-4.1-mini model; 623 input/2440 output, published-list-cost estimate $0.00456852; campaign ledger `SETTLED $0.004569`. Prompt attempt FAILED_NO_RETRY; its reserved $0.002030 remains unsettled/charge unknown. Conservative ledger usage $0.006599, not actual Azure bill total. Budget `enabled=false`, owner membership `active=false`; no hosted content/media/publishing. Refer to `docs/feature2/REAL_AZURE_7_DAY_ACCEPTANCE_20261027.md` for evidence. New billable attempts require separately documented fresh approval.
