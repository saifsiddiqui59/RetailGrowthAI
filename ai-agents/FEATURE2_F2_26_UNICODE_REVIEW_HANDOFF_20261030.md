# Feature #2 F2-26 — private word-review Unicode display safety

Feature-owned source-only follow-up based on existing PR #551. A typed Feature #7 original-WAV review previously accepted bidi override/isolates and invisible controls inside word-timing and suspected-error text. React escaping prevents HTML injection but not visual direction spoofing during human review.

- `frontend/src/features/voiceover/voiceover-quality-review.mjs`: reject C0/C1, direction override/isolates, invisible separators and line controls from untrusted review words; retain legitimate Indic combining marks and joiners.
- `tests/frontend/feature2-voice-quality-review.test.mjs`: negative tests for both ASR word timing and issue words, plus Hindi/Marathi-compatible positive fixture.
- These are synthetic typed records, **not** real speech, signed F7 execution or human approval.
- Task `F2-26` remains IN PROGRESS pending exact-head CI, coordinator review/integration and current JWT/RLS/rights verified backend. This is not integrated DONE. No paid inference, GPU, PROD, WineShopPOS, or media samples.
- Coordinator status proposal only: maintain F2-26 IN PROGRESS and attach reviewed PR/CI evidence after integration; shared `coordination/task_progress.json` and canonical docs remain coordinator-owned.
