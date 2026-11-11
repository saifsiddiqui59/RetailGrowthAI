# Feature7 F7-L / F7-P — reuse upstream VoiceStudio transcription

VoiceStudio already implements `POST /v1/audio/transcriptions` with `response_format=verbose_json` and `timestamp_granularities[]=word`. This stacked Feature7 PR adds a private, disabled-by-default service-to-service adapter to that real API, with a bounded original WAV, expected SHA256, no redirects, fixed model selector, optional en/hi/mr locale, strict JSON/word timing checks and no retry. Synthetic tests validate source/response integrity and Hindi words without a real ASR model.

The returned object is **UNSIGNED, NOT RENDERABLE, NOT APPROVED**. It is deliberately not a substitute for existing Feature7 HMAC tenant-scoped signed transcript, actual word alignment QA, original footage preflight or human review. Existing Feature7 parent PR #513 continues to own those contracts. This change is stacked onto its existing branch rather than replacing working STT checks with a new engine.

Next: adapt this validated word list to the existing Feature7 signed transcript production/lease, run actual offline CPU inference using licensed pinned weights and signed two-shop inputs, then hand caption cues to Feature4. Upstream VoiceStudio commercial model/component rights and AGPL need review. All GPU/paid/prod/hosted operations remain OFF.

## 2026-11-11 F7 padding checkpoint
- Child #942 head `54d9467c042f2d995e9a4e3a7b3452118a793bcc`: strict zero RIFF odd-chunk padding before trusted HMAC signing; positive canonical padded WAV and negative poisoned/missing padding tests.
- Source and tests committed to the existing child branch; local execution blocked by GitHub DNS in runner; exact-head four-job CI still needs verification. No merge or product acceptance claimed.
- **NEXT CODE ACTION:** inspect exact-head #942 CI and repair any owner-scope failures; merge green child into parent #513 with expected head and verify parent CI; then reconcile parent against current main without concurrently merging main. Keep F4 dependency #910 and human approval boundaries intact.
