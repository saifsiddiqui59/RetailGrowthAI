# F5 source-only visual QA recovery — 2026-11-19

Original parent #323 remains OPEN/DRAFT at `ffc464c09f719a0bfb6b15b5c34608f89d76234b`. This current-main PR restores two unchanged Git blobs after the separately accepted and exact-main-green source-contract slice #1011:

- `feature5_motion/quality_review.py` — original SHA `d71164603d829e81614770d21e92e49e2da0cb5a`.
- `tests/ai/test_feature5_quality_review.py` — original SHA `c04c7c8e7cbcd0e3ac48037e630668b660a56cef`.

This is an **in-memory review contract only**; manual reviewer decisions still require a real authenticated tenant-scoped JWT/RLS writer and a separately verified immutable private clip SHA before any Feature4 handoff. All success fixtures simulate a reviewer and are NOT actual visual quality evidence. The checks require all categories, disclosure, reviewer explanation, tenant, write-role and media hash match; automatic approval is forbidden.

Offline validation: `python -m unittest discover -s tests/ai -p 'test_feature5_quality_review.py'` plus the mandatory 4/4 PR and fresh-main CI. No Hunyuan/Wan model weights, GPU, paid inference, hosted SQL, cloud resources, PROD or WineShopPOS. Original 22 F5 task IDs stay unchanged/not DONE. Do not merge source-only contracts as permission to run video models or publish.
