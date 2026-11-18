# F2-05 current-main Pexels metadata discovery extraction (2026-11-17)

- Source lineage: original conflicted Feature2 parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) head `d80d6b50705323290c4b214bf2f006eacef1ef33`.
- Preserved **byte-for-byte Git blob originals**:
  - `ai-agents/src/ai_agents/feature2_pexels_live.py` at blob `61b92aae1b06781507d59fee0f81085815b24aef`.
  - `ai-agents/tests/test_feature2_pexels_live.py` at blob `b5e672416ae62870dee8187bd44ba8b9c22ec0a3`.
- Existing `feature2_pexels_renditions.py` was previously merged and remains untouched.
- Discovery is **OFF by default** (`RETAIL_FEATURE2_PEXELS_ENABLED`), server-only existing key, HTTPS-bound official endpoints, bounded response size/term/page, redirect forbidden, current signed editor callback both before and after discovery.
- **Only source metadata** returned. Neither downloaded Pexels bytes, rights licenses, current tenant media registration, retailer-owned product proof, video generation nor publication is authorized. `can_publish: false`, `can_import: false`; no provider executed by tests (injected mock transport).
- These original pytest tests cover no-network default, account denial and revocation, two official endpoint mock payloads, source/host spoofing, bounded queries, and partial provider failures.
- This source-only extraction must pass exact-head four CI jobs and a separately verified fresh-main four CI jobs after review/merge. Original F2-05, F2-32, F2-37 hosted/rights/integration remain IN PROGRESS. No GPUs, paid models, DEV/PROD deployments, hosted SQL or WineShopPOS changes.
