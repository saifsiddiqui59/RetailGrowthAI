# Feature2 Azure GPT-4.1-mini — pricing evidence and no-spend release gate (26 October 2026)

**READ-ONLY investigation. This document is not payment approval or a configuration change.**

Existing protected Azure OIDC success https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40382879442 reports exactly one reuseable GPT-4.1-mini Standard deployment `rgai-gpt-41-mini` in `rgai-dev-openai-d4e5ddbd`, `southindia`, S0, `rg-retailgrowth-dev`; existing Functions `rgai-dev-functions-d4e5ddbd`. The four Feature2 specific settings `RETAIL_FEATURE2_REAL_AI_ENABLED`, `RETAIL_FEATURE2_INPUT_USD_PER_MILLION`, `RETAIL_FEATURE2_OUTPUT_USD_PER_MILLION`, `RETAIL_FEATURE2_MAX_CALL_USD` were absent at last read-only inspection.

Indicative **published**, NOT subscription-specific confirmed Azure rates for **South India Regional Standard** GPT-4.1-mini: **USD $0.44 / million uncached input tokens**, **USD $1.76 / million output tokens**, **USD $0.11 / million cached input** (effective 2025-11-01 in the retrieved third-party Azure retail meter snapshot):
https://www.azurespeed.com/AzureAiModelPricing/Models/openai-gpt-4-1-mini

Microsoft documents the official Azure Retail Prices API to verify precise `productName`, `skuName`, `armRegionName=southindia`, `effectiveStartDate`, `retailPrice`, `unitOfMeasure`, and deployment profile:
https://learn.microsoft.com/en-us/azure/cognitive-services/openai/faq
https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices

The Microsoft dynamic Azure OpenAI pricing webpage renders placeholders when its region/pricing selection fails to load; the third-party snapshot must **not** be used as a silently approved billing rate. Verify original Microsoft meter and applicable account contract before setting Functions pricing.

## Hard stop
1. Fresh hosted DEV SQL/migration prefix from exact RetailGrowthAI project only; currently 21 applied and 2 pending source migrations, including Feature3's earlier independent protected DDL. No blanket push.
2. Verified tested backup/restore, approvals for any DDL, and reviewed new migration/version hash with coordinator.
3. Separate explicit user-approved USD test cap, expiry and synthetic retailer account/ROOT testing authorization. Prior USD0.20 proposal is **not** an approval.
4. Server-only secrets, model and rates approved through the existing protected release process, real AI explicitly OFF until the above hold; at no time expose credentials to browser.
5. A single real text-only prompt/7-day model sample with real provider request/response, usage and USD accounting is still blocked until steps 1–4. Authenticated saved marketing DRAFT additionally requires rights-cleared media and authentic clothing trend.

No model inference, hosted migration, Azure setting mutation, new paid infrastructure, PROD or WineShopPOS operation was done by this readiness work.


## 2026-10-26 — VERIFIED official Azure public Retail Prices meters
- Protected Azure OIDC run [#40401262949](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40401262949) **SUCCESS**: existing `rgai-gpt-41-mini` South India Regional Standard S0 verified, `FEATURE2_MODEL_CREDENTIALS_READ=NO`, `FEATURE2_OFFICIAL_RETAIL_METER_LOOKUP=PASS`, `azure_inference_attempted=false`.
- Source Azure Retail Prices API effective **2025-11-01** returns input SKU `gpt 4.1 mini Inp regnl`, meter ID `7ca44ee4-48c4-5fae-9880-e880a3015337`, unit **1K**, rate $0.00044 / 1K = **$0.44 / 1M**; output `gpt 4.1 mini Outp regnl`, meter ID `3eb7aea7-33d2-5be3-a87d-04be825c632d`, unit **1K**, rate $0.00176 / 1K = **$1.76 / 1M**. These are PUBLIC retail prices, not proven account contracted rates or a paid bill. Source #437 fixed 1K conversion with tests.
- Owner **US$0.20 TOTAL** one-time isolated paid text test authorization does NOT permit protected hosted SQL, ROOT account creation or uncapped server configuration; no paid call has occurred. Existing ledger tables remain absent; real seven-day Thread & Loom Studio content still gated.
