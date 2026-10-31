# Feature2 F2-17/F2-26 — private voice reviewer UI hardening (2026-10-30)

This distinct, independent Frontend batch starts from the current unified Feature2 draft PR #551; it complements Python signed-ASR display guards in existing sibling PR #809. The signed backend is the authority, while this browser projection must independently reject hostile display text.

Changes: reject bidi/zero-width/control/soft-hyphen U+00AD display spoofing and multiword whitespace in ASR words/hints; preserve valid Indic ZWJ/ZWNJ word composition; require v4 private audio-asset identity and bounded signed WER source job; freeze verified word/issue rows to prevent mutable review evidence. Add deterministic Node fixtures proving denial and positive original Hindi/Marathi conjunct display.

Original tasks F2-17/F2-26 remain IN PROGRESS. No genuine real model, signed JWT/RLS playback, commercial approval, hosted mutation or public user demo. Coordinator owns producer-verified F7 signed original-WAV, issue #650 immutable Functions ZIP, #249 Azure 503, sibling PR #809 reconciliation, exact-head 4/4 and postmerge main 4/4. GPU OFF, no paid inference, PROD or WineShopPOS edits.
