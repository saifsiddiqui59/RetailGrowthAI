# Feature3 F3-08 / F3-13 — private PNG IDAT integrity handoff (2026-11-06)

**Existing source PR:** [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879) targeting `main`. Continue original F3-08 private no-URL binary and F3-13 adversarial regression; this is not a new Feature3 task.

## Source defect and repair
A CRC-valid PNG with a matching whole-file SHA can contain extra bytes after the zlib end-of-stream *inside* IDAT. Pillow can display the image while ignoring those bytes. A second valid zlib stream, or extra decompressed scanline bytes, can likewise smuggle data in an otherwise apparently valid private image receipt.

- `feature3_private_binary_http.py`: validate the complete IDAT zlib stream across PNG chunks, exact filtered scanline byte count for noninterlaced and Adam7 layouts, decompression bounds, zlib EOF and no unused/trailing compressed bytes before serving a private response. Opaque 503/empty body on failure.
- `tests/api/test_feature3_private_binary_idat_payload.py`: synthetic valid CRC/SHA attacks for a trailer suffix, second compressed stream, extra inflated data, and truncated zlib trailer; prove recovery and RGB/RGBA/grayscale/indexed/16-bit positive coverage, plus cross-shop denial.

**Scope:** CPU-only deterministic PNG bytes and injected reader; no customer images, hosted JWT/RLS, real current rights provider, signed Azure route, paid provider/GPU, queue send, hosted migrations, PROD or WineShopPOS.

## Acceptance gate
- Source is **IN PROGRESS** until exact final PR-head four-job Part1 CI and affected security/media independent review.
- Before a permitted merge, check the current main delta and PR changed paths. After merge, verify four new main CI jobs at the exact merge SHA before recording source receipt; keep 0/33 *hosted* accepted without live genuine rights and signed DEV role tests.
- No automation should create another F3-08 task or merge #880's separate current-rights adapter into this PR without compatibility review.
