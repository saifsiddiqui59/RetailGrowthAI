# Feature2 stock B-roll source reconciliation — 2026-11-15

Source parent: still-open conflicted Feature2 PR #551, exact head `d80d6b50705323290c4b214bf2f006eacef1ef33`.

## Extracted without rewriting

- `feature2_stock_media.py` — trusted-shop and media-original byte checks; forbids catalog references from granting garment identity/model consent/retailer endorsement
- `feature2_stock_cutaway.py` — immutable review-only editorial cutaway proposal; downstream Feature4 must reverify rights
- `feature2_pexels_renditions.py` — pure bounded rendition selection adapted from MIT `MoneyPrinterTurbo`, with its original `LICENSE` preserved
- Original candidate reference-only JSON and **all three original pytest files** (`test_feature2_stock_media`, `test_feature2_stock_broll_integration`, `test_feature2_pexels_renditions`)

The eight above are exact, original source Git blobs. Existing main already has the MIT Creative Director from accepted PR #949, so the synthetic integrated B-roll test invokes that same preserved compiler; there is no duplicate planner or new renderer. This is an independent source-only Creative Director input enhancement, not a customer Reel.

## No false rights or success claims

Public Pexels/Wikimedia URLs are **metadata for discovery only**, not downloaded content, merchant originals, model releases, licensed promotional music or upload permission. Synthetic test media bytes are fabricated locally and never represented as actual provider footage. Any use in a finished commercial ad requires separately sourced original asset bytes, verified license/release rights, real retailer JWT/RLS media grants and an authorized Feature4 approval at dispatch time. Do not automatically call external Pexels/stock APIs from this package, or promote catalog entries to approved product imagery. GPU, paid inference, Azure/SQL, PROD and WineShopPOS remain OFF/untouched.

Source review gate: final-head four-job CI (Python negatives plus Supabase, FFmpeg and frontend) and fresh current-main four-job CI; preserve Feature2 #551/#848 for unrelated remaining code. Original F2 tasks remain distinct source/integration/hosted statuses, and Feature4/7 integration is not claimed.
