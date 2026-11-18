# Feature #4 F4-05 — footage/scene transition parity handoff (2026-10-30)

**IN PROGRESS — SOURCE ONLY; no encoded quality or integrated DONE claim.** Parent Feature4 draft #322.

## Implemented
- The existing trusted HyperFrames composition compiler now applies the approved `fade`, `slide`, or `cut` transition to the *separate actual video footage layer*, not just the HTML scene text/overlay. The video carries the scene's validated `--span` duration, and the existing CSS keyframes are reused; no second renderer, new contract, dynamic JS, or browser-controlled CSS.
- Extended `tests/media/test_feature4_professional.py` to compile a real synthetic 15s H264/AAC source into a three-scene plan and verify all three footage transitions, corresponding scene transitions, and per-clip duration attributes.

## Outstanding acceptance
- Targeted Python test on exact head, branch four-job CI and actual encoded FFmpeg/HyperFrames decoded transition parity still pending; HTML compiler assertions do **not** prove final MP4 transitions.
- Coordinator: `F4-22` shared ZIP packaging Issue #650 and `F4-23` PR #322 merge/reconcile/fresh postmerge main 4/4. Owner: coordinator. Required: protected 120-member package and successful reviewed integration.
- `F4-05` remains IN PROGRESS until encoded visual parity and approved integration. Human editorial review and retailer media rights remain external gates; no mock media as production evidence.
- No GPU, paid model, hosted deployment, PROD, WineShopPOS, schema or shared canonical document changes.
