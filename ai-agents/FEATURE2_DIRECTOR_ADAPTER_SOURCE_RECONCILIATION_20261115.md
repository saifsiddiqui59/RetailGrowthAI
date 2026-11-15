# F2-01 original pinned Director optional Azure bridge — source-only checkpoint

Exact original Feature2 parent #551 (head `d80d6b50705323290c4b214bf2f006eacef1ef33`) Git blobs preserved on current main, without changing older source implementation:

- `src/ai_agents/feature2_director_ai.py` — `993b16a55821bb9774a8277bb0ba31db4905b097`
- `tests/test_feature2_director_azure.py` — `f58e019b739337991de7ae5e934ad282180fe6d3`
- `tests/test_feature2_director_package.py` — `a4002f7ea46ffdd771e68f28fb4861ba714716d2`

This retains optional source-only `AzureFeature2DirectorLLM` from the parent, using existing `AzureFeature2ContentLLM` transport and one-shot cost-reservation; tests stub the transport entirely. No provider inference or billing is triggered by source integration or CI. An off-by-default `RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED` guard is present. This is NOT registered as an Azure Function route, and the currently deployed ZIP intentionally lacks Node/pinned JS source. The fail-closed package/runtime guards and standalone trusted-JWT context reader were integrated separately in #956. Only a verified server-derived context with current JWT/RLS grants and an approved runtime/payer can authorize any future paid use; this batch **does not** establish such a route or enable the flag.

**Unresolved:** independent production source/security/provider/billing review before wiring; verified runtime Node22 and signed reviewer; actual Azure #249/ZIP indexing; cost operator approval; tenant-private source and commercial media rights; end-to-end paid usage settlement and real creative QA. F2-01 remains IN PROGRESS (source extracted ≠ hosted accepted). Original #551/#848 remain open for the rest. No Azure deploy, Node binary install, HTTP route, SQL, models, GPU, paid API, PROD or WineShopPOS modification.
