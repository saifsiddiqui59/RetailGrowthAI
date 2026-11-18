# Feature2 official Pexels fixture **plan-only CI** (2026-11-18)

Current-main source recovery from original #551 (`d80d6b50705323290c4b214bf2f006eacef1ef33`). Verified existing current-main `test-fixtures/clothing-shop-pexels/manifest.json` at Git blob `55674b4260508b799abf8d70bcecff0c31d986a2`, so no manifest replacement.

Preserves 5 original Git blobs, without changing deployed APIs:
- `test-fixtures/clothing-shop-pexels/import-official-pexels.mjs` — `42ae313dd8842fbb767161fbf6813296098e2a3c`
- `tests/test_feature2_pexels_import_contract.py` — `cd747cba28aa7f1da19079e6f623f673c4af749c`
- `tests/test_feature2_clothing_fixture.py` — `2f4ade1c2d1f38365936a2277a60019a1c7986a6`
- `test-fixtures/clothing-shop-pexels/README.md` — `d028dcfd0ea9d9f92d6e1fadcb318e6e78976fe6`
- `test-fixtures/clothing-shop-pexels/.gitignore` — `27a8f70ca5ccab3e61f474eea87e84e016cb4eec`

**CI runs only `node --check` and `node import-official-pexels.mjs --plan`.** This uses manifest references and does not import Pexels SDK, read API secrets, call external network, download media, write assets, pay for inference or claim licensed clothing, real customer product, model release, approved tenant media or publication rights. The original script includes an **explicit operator-only `--import` mode** that requires a separately provided PEXELS_API_KEY, optional pinned Pexels SDK installation and independent commercial/legal/media review. That mode is never invoked here or in CI and cannot authorize retailer product/third-party model identity. No media is committed or uploaded.

Source-only FIxture integration needs final exact-head 4/4, safe main merge and fresh main 4/4; no feature task DONE for hosted Pexels rights/import, F4 rendering, or F5 I2V. GPU, paid providers, SQL/Azure, PROD and WineShopPOS unchanged.
