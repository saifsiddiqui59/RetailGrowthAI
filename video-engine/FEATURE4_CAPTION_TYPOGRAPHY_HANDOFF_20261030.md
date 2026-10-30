# Feature4 F4-12 caption typography and reviewed-text integrity — 2026-10-30

**IN PROGRESS — source-only, not actual human legibility proof.** Isolated Feature4 development branch `feat/feature4-caption-typography-bidi-20261030` stacks on original F4-11 endcard draft #835.

## Reviewable change
`feature4_caption_track.py` now rejects explicit Unicode Bidi overrides/isolate controls, hidden zero-width spaces, BOM, word joiners, soft hyphens, forbidden nonprinting categories and invisible-mark-only cues. This prevents a visually reversed/hidden label from escaping otherwise exact approved script matching across the real `creative_reel_v1` -> `rg_video_v2` -> HyperFrames and private SRT/VTT export pipeline. It **does not** reject legitimate Arabic, Hindi/Devanagari, and Indic shaping joiners. The original 0–60s approved cue timing and text are returned exactly, never translated/reworded.

`professional.py` now uses a fixed, backend-owned `caption_font_px` from the same trusted validator: 1080p caption text uses 56px for <=45 chars, 46px for 46–70 and 38px for 71–90; 540p has correspondingly halved sizes. CSS balances line wraps without introducing user-provided CSS. Invalid font/source dimensions or over-90 strings are refused.

## Tests & acceptance
- SRT/VTT test with Hindi, Arabic and ZWJ-containing Hindi cue asserts **unchanged exact subtitle text**; explicit RLO, isolation markers, zero-width/BOM/soft-hyphen and blank-combining-mark spoof strings are blocked.
- Actual trusted offline Python compositor test compiles long/short/mid approved spoken cues to HyperFrames HTML at 1080p, checks per-cue selector font size, exact text, and safe wrap rule. These are **source-level compositor tests**, not a real encoded MP4, OCR, commercial speech quality or human legibility signoff.
- Require current exact-head four-job branch CI, coordinator review/merge after all parent drafts, fresh main four-job CI. F4-12 still needs actual revised Full-HD 60s native output, verified music/voice rights and human text placement approval. No GPU, charged model, hosted DB, PROD, WineShopPOS, public media or fake approval.
