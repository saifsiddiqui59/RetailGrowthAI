# Feature7 F7-L / F7-P — reuse upstream VoiceStudio transcription

VoiceStudio already implements `POST /v1/audio/transcriptions` with `response_format=verbose_json` and `timestamp_granularities[]=word`. This stacked Feature7 PR adds a private, disabled-by-default service-to-service adapter to that real API, with a bounded original WAV, expected SHA256, no redirects, fixed model selector, optional en/hi/mr locale, strict JSON/word timing checks and no retry. Synthetic tests validate source/response integrity and Hindi words without a real ASR model.

The returned object is **UNSIGNED, NOT RENDERABLE, NOT APPROVED**. It is deliberately not a substitute for existing Feature7 HMAC tenant-scoped signed transcript, actual word alignment QA, original footage preflight or human review. Existing Feature7 parent PR #513 continues to own those contracts. This change is stacked onto its existing branch rather than replacing working STT checks with a new engine.

Next: adapt this validated word list to the existing Feature7 signed transcript production/lease, run actual offline CPU inference using licensed pinned weights and signed two-shop inputs, then hand caption cues to Feature4. Upstream VoiceStudio commercial model/component rights and AGPL need review. All GPU/paid/prod/hosted operations remain OFF.

## 2026-11-11 F7 padding checkpoint
- Child #942 head `54d9467c042f2d995e9a4e3a7b3452118a793bcc`: strict zero RIFF odd-chunk padding before trusted HMAC signing; positive canonical padded WAV and negative poisoned/missing padding tests.
- Source and tests committed to the existing child branch; local execution blocked by GitHub DNS in runner; exact-head four-job CI still needs verification. No merge or product acceptance claimed.
- **NEXT CODE ACTION:** inspect exact-head #942 CI and repair any owner-scope failures; merge green child into parent #513 with expected head and verify parent CI; then reconcile parent against current main without concurrently merging main. Keep F4 dependency #910 and human approval boundaries intact.

## 2026-11-11 F7 PCM word-clock boundary
- Child #942 code SHA `c682d3a6`, regression SHA `25ddf70e`: verified WAV parser returns sample rate with PCM duration; signed ASR word ends now require <= actual PCM end plus one 16-bit PCM sample (rather than 20ms). Synthetic Marathi word tests cover 1.001s denial, exact one-sample acceptance, and two-sample denial on a 1s/16kHz WAV. No STT inference or model activation.
- Parent #513 remains the integration target; #911 VoiceStudio adapter and F4 dependency #910 are already merged into their respective feature branches, not accepted on main.
- Exact-head mandatory 4-job CI and targeted offline Node/Python tests require verification on final child head. Do not mark DONE or merge main from this checkpoint.
- **NEXT CODE ACTION:** run `python -m unittest tests/media/test_feature7_voicestudio_verified_media.py` against a full checkout, inspect child exact-head 4/4 CI, repair within F7 paths if needed, then merge eligible #942 into #513 with expected head and verify parent 4/4. Reconcile parent-to-main conflicts only after reviewing all changed paths and approvals.

## 2026-11-12 — F7 PCM/video sample-clock boundary
- Owned source/test commits `f7b90c2f` and `3778352f` on the existing F7 VoiceStudio child branch: replace the 20ms original-video duration overrun allowance with one PCM sample (verified sample rate); add positive one-sample and negative two-sample Marathi fixture cases. No STT model invocation, GPU, cloud, paid inference or shared contract changes.
- **Verification:** GitHub commit workflow lookup on `3778352f` returned no PR runs at inspection; local repository checkout unavailable (GitHub DNS resolution failed). Tests and exact-head 4/4 are **not claimed passed**. The subsequent handoff commit changes head again.
- **Next code action:** verify exact latest head's four mandatory CI jobs, repair owned failures; compare PR #942 with parent #513, integrate eligible child only after green and policy review; reconcile parent against current main without merging main concurrently. Feature4 dependent PR #910 remains linked. Maintain SOURCE IN PROGRESS until accepted main 4/4 and product acceptance.
