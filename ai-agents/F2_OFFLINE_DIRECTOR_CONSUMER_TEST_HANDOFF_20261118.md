# Feature2 Offline Director ↔ F4/F5/F7 Source Contracts (2026-11-18)

This current-main scoped test batch recovers exact original F2 #551 `d80d6b50705323290c4b214bf2f006eacef1ef33` Git blobs without replacing newer Creative Director code:
- `tests/test_feature2_cross_feature_export.py`: `9ae4b5dfc6a5ab6a80bde2acbee2741803e7d9b9`
- `tests/test_feature2_diwali_mocked_foundry_positive.py`: `f17054769b8a5890e33a30d0aa1bf9bebfe6bb85`
- `tests/test_feature2_f4_consumer_compat.py`: `9c69ec9bbeb2d5de80ef7a906e2c0dc755c62e18`
- `tests/test_feature2_upstream_caption_preview.py`: `e33d262fd7b87ce65c4113df7f1f7c8c7ca5ad91`

The existing current-main pinned Kuble/MIT Director scripts, F2 Azure adapter and creative quality source were confirmed present before port. All added Python tests invoke **local Node test scripts or injected Fake LLM transport** only. The code checks 15/30/60s source packets, F2/F4/F5 OFF-by-default render and paid-motion gates, preview captions from upstream, and a fake use-budgeted Foundry response. No actual Azure AI/provider requests, internet downloads, customer data, licensed clothes, GPU frames, real music/speech inference, commercial rights, hosted JWT/RLS or F4 publishing are asserted.

This integrates **test coverage only**, not user-visible product features; preserve every current newer original module. Exact-head PR four CI jobs and fresh main four CI jobs required for source-level acceptance, and original F2/F4/F5/F7 hosted tasks remain IN PROGRESS. No GPU, paid models, cloud/SQL/PROD or WineShopPOS mutation.
