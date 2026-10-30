# RetailGrowthAI Feature #2 — real engine sample (fictional boutique)

This is a **test**, not a live trend or an actual shop. It uses the repository's unchanged `ai_agents.trend_intelligence.collect`, `recommendations` and `content_intelligence.create_content_draft` to build a seven-day sample.

Test retailer: **Thread & Loom Studio (FICTIONAL TEST SHOP)**, Nagpur. Category: clothing. Product context: cotton kurtis. Brand voice: warm and practical. Language: English (India). Platforms: Instagram, Facebook, LinkedIn, YouTube. Objective: styling education. No discounts or inventory claims.

**Mock trend:** `Kurti clothing styling ideas` is an explicitly synthetic XML RSS fixture. The real DEV feed (26 October 2026) has no verified clothing trend and is not used to manufacture one. It is not safe to claim this test search is really trending. The approved image UUID is likewise a fixture, not an uploaded media record.

## Execute with the actual code

```bash
uv run --project ai-agents python demo/feature2/generate_sample.py demo/feature2/out
```

Produces `feature2-sample.json` with the full campaign and `feature2-sample.txt` with readable daily examples. Every result remains **DRAFT / PENDING_RETAILER**, never auto-published. `MockFoundryProvider` is deterministic, with no paid Azure Foundry or GPU calls; this is not a model-generated premium advertisement.

GitHub CI also runs `tests/ai/test_feature2_fictional_retailer_sample.py`. Outputs are uploaded by the coordinator-owned sample workflow as artifacts. This fixture does not create or modify accounts, shops, inventory, RLS, Supabase DB, Azure resources, WineShopPOS or PROD.
