# Feature #5 — Pexels stock candidate rights and originality audit (28 October 2026)

**STATUS: PUBLIC SOURCE-PAGE / LICENSE REVIEWED; ORIGINAL FILE BYTES NOT VERIFIED. NO CUSTOMER OR AI MODEL ACCEPTANCE.**

This document is a source audit, not a customer model release or implied endorsement. All 2026-10-28 URLs below were independently checked against Pexels pages, with no automated bulk download, web scraping or ML evaluation corpus.

| Candidate | Source | Confirmed on public source page | Evidence state |
|---|---|---|---|
| Walking footage | https://www.pexels.com/video/fashionable-woman-walking-in-urban-summer-setting-30706004/ | Gaidar Iskakov; 1080×1920; 9 seconds; 30 fps; marked Free | **Page metadata only** |
| Red kurti fashion photograph | https://www.pexels.com/photo/photo-of-a-woman-wearing-a-traditional-red-kurti-20702674/ | Muneeb Malhotra; 4000×6000; red garment; marked Free | **Page metadata only** |
| General licensing | https://www.pexels.com/license/ | Modification/commercial use permitted; do not imply depicted persons/brands endorse merchant | **License terms verified** |
| Detailed rights | https://help.pexels.com/hc/en-us/articles/360042295214-Can-I-use-the-photos-and-videos-for-a-commercial-project | Depicted brands, trademarks, personality/publicity rights may need independent releases | **Important restriction** |
| API/AI dataset restrictions | https://help.pexels.com/hc/en-us/articles/900005880463-What-are-the-Terms-and-Conditions | Prohibits unapproved dataset/training/evaluation extraction for ML; no automated bulk collecting | **Do not use for model training/evaluation corpus** |

### Actual test status
- Internet requests for `images.pexels.com` and download endpoints failed DNS resolution in the restricted execution environment. No raw photo/video bytes were uploaded to GitHub or staged in a local test runner. **No SHA256 of actual Pexels originals exists**.
- Existing FFmpeg tests render original CPU-generated moving color charts at native 704×1280 / 121 frames and verify pipeline behavior. This is real local video decoding but **NOT walking-model video or licensed garment product comparison**.
- The Pexels clip and kurti photo are DIFFERENT people wearing DIFFERENT clothing. They cannot prove the same person wearing a selected SKU or correct embroidered garment preservation.
- Before a production ad uses a recognizable person as a retailer endorsement, independently confirm any required release and retailer-owned garment/commercial rights. Pexels general license alone does not prove that.
- The current `feature5_motion/stock_media_review.py` takes only already-downloaded locally authorized media paths, checks video and image bytes, records SHA256 and two frame fingerprints, and never activates paid model inference.
- To re-run local offline screening **once permitted original bytes are available**: `inspect_downloaded_stock_pair(local_video=Path(...), local_photo=Path(...))`. Accept its technical output only as pending human review, not a commercial rights grant.

**No Pexels asset was automatically downloaded, redistributed, fed into a paid provider, or used to train/evaluate an AI model.** The Feature3 retailer-owned model/try-on source and Feature4 independent human approval remain distinct production gates.
