# Feature3 Task3.3 — model-library private object key compatibility (2026-10-28)

**Actual interoperability defect corrected, not full model registry completion.**

The existing `model_library_v2.import_model_image` wrote a deterministic
`shops/{shop_id}/model-library/...` key (or bare
`model-library/platform/...`), while the deployed private Supabase Storage
and existing backend `PrivateMedia._path` require **the canonical owner
tenant UUID as the first path segment**. No live Feature3 models exist in DEV,
so this new source contract does not migrate or rename user objects.

The corrected immutable keys are:
- Shop-owned: `{owner_shop_uuid}/model-library/{model_uuid}/{sha256}.png`
- Curator-shared metadata: `{owner_shop_uuid}/model-library/platform/{model_uuid}/{sha256}.png`

A platform catalog grant is **not** a license to read another shop's binary.
Even shared catalog metadata stays tied to the true original owner key;
private pixels require separate, current, requesting-tenant media authorization
and server-side delegation. The `checked_model_for_use` exact path validation,
projection and cross-feature reference tests now use this same private rule.
No real model image, license evidence, human approval or tenant grant has been
registered; tests run against synthetic local pixels only.

Remaining Task3.3: genuine signed owner/EDITOR image upload, byte-level
SHA-256/Storage/media_assets proof, protected registration RPC and human review
with rights revision/revocation, shop/curator permissions, real approved reuse
and negative hosted JWT/RLS tests. No GPU, paid inference, PROD or WineShopPOS.

## 2026-10-28 — coordinator current-main conflict reconciliation

The originally green branch CI for #504 did not imply a mergeable current-main PR; a concurrent Feature3 POST-denial repair made the PR integration suite fail. This superseding source branch reapplies only the owner-first Storage key fix to the current `main`, retaining POST=404/default-OFF GET=503 and registering the missing Azure Functions GET-only job-history decorator. The new exact-head four-job CI and integration merge are independent checks, not inherited from #504/#507. No GPU flag, paid endpoint, synthetic media approval, remote SQL or Storage write is created.
