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

## 2026-11-12 — mutable lease alias denial
- Child #942 source commit `8ec09195d81d5ed52a6aacda987119206141d383` snapshots the first authoritative lease before signing; the final lease read is compared with that snapshot, not with a potentially mutated alias. This closes in-place revocation/scope mutation bypass in a storage adapter returning the same object twice.
- Regression commit `d81a5e32efa6ec3d6c5edf411e1739ef21a9c5ee` adds eight deterministic in-place lease mutation denials (active, tenant, asset, job, source SHA, audio SHA, model, expiry) and stable-object positive coverage.
- **Verification:** GitHub workflow lookup for code/test head returned zero runs. Local Git checkout blocked by `Could not resolve host: github.com`; targeted tests and 4/4 CI not verified. No merge performed.
- **NEXT CODE ACTION:** run `python -m unittest tests/media/test_feature7_voicestudio_verified_media.py` on a checkout; verify exact-head four-job PR CI, repair owner-scope failures, then integrate eligible #942 into parent #513 using expected head and review the parent-to-main conflict. F4 dependency #910 remains linked. Keep GPU/paid/hosted/PROD/WineShopPOS OFF.

## 2026-11-12 — final lease own-property hardening
- Source `8d7d82df` and regression `3b3dbdf9` on child #942: require all eight authoritative lease fields to be **own properties on the second lease receipt**, not only the first. Deny prototype-forged final active/scope fields; preserve valid null-prototype own-field receipts.
- Exact-head GitHub PR workflow lookup returned zero runs at inspection; child #942 remains open and GitHub reports non-mergeable. Targeted runtime suite not executed in this run. No child/parent/main merge or hosted activity.
- **NEXT CODE ACTION:** run `python -m unittest tests/media/test_feature7_voicestudio_verified_media.py` on checkout, repair any owned test failures, obtain exact-head mandatory 4/4 CI, then safely integrate eligible #942 into parent #513; reconcile parent against main separately. F4 dependency #910 remains linked. SOURCE IN PROGRESS.


## 2026-11-12 canonical word export hardening
- Scoped source commit `e6eda7d83d73b78481fc565aff256981303b3584`: the signed review's `whisperx_json` now exports only normalized word/text and millisecond-rounded timestamps, not untrusted arbitrary properties copied from upstream VoiceStudio word objects. HMAC transcript hash and captions use the same normalized words.
- Regression commit `e478709c686957e88aff4ef4f7566652886266fa`: negative injected tenant/token metadata case and positive fractional-time canonicalization.
- Verification pending: local git checkout cannot resolve github.com; exact-head four-job CI must be inspected before merging. No main merge. NEXT: verify test_feature7_voicestudio_verified_media.py, exact-head four-job CI, then merge eligible child #942 into #513 and resolve parent/main drift under integration writer. F4 dependency #910 already merged to its feature parent. No GPU/paid/PROD/cloud/WineShopPOS.

## 2026-11-12 F7 word-list descriptor hardening

On child #942, reject accessor-backed or inherited `review.words` before any array inspection, snapshot or lease access. This closes an execution gap left by earlier protections for word entries, array indices and review scalar metadata. Deterministic negative tests cover getter non-execution, inherited list rejection, zero lease reads; frozen own-data word list remains accepted. Source commit `dfb8f81c`, regression commit `4429c8e2`. The original VoiceStudio `/v1/audio/transcriptions` adapter remains the sole upstream word-timing source; no new STT/model/GPU path.

**Verification pending:** local git checkout cannot resolve github.com; targeted Python/Node tests and exact-head four-job CI have not been observed. Do not merge #942 into #513 until test and CI evidence exists. Parent #513 remains the only candidate for serialized main integration. F4 dependency #910 was merged into its own F4 parent, not main. Next code action: inspect other untrusted input descriptors and the signed source/lease boundary; run `python -m pytest tests/media/test_feature7_voicestudio_verified_media.py -q` when a checkout is available, then verify exact SHA CI before child merge.

## 2026-11-13 — signed bridge descriptor boundary
- Parent #513 code commit `9a1f69b4`, regression commit `668abe89`: fail closed on inherited/accessor-backed VoiceStudio review and lease scalar fields before evaluating signing inputs; positive null-prototype data-record coverage. Existing upstream `/v1/audio/transcriptions` remains unchanged, with no model execution.
- Exact code/test head `668abe899b8c9b6098d7bff15b30bb2448ba54f9` had **zero PR workflow runs returned** at lookup. Local checkout failed because github.com DNS resolution was unavailable; targeted tests and exact-head 4/4 are NOT verified. Parent #513 is OPEN and non-mergeable against main; no main merge.
- **NEXT CODE ACTION:** run `python -m unittest tests/media/test_feature7_voicestudio_signed_handoff.py` on a checkout; inspect/fix owner-scoped failures and exact-head four-job CI, then review/reconcile parent #513 with current main for serialized integration. Upstream #911 and #942 are already merged to parent; F4 dependency #910 remains linked. No GPU, paid, cloud/PROD or WineShopPOS activity.

## 2026-11-13 — lease TOCTOU regression batch
- Parent #513 code commits `a98f992c`, `0bba3327`: snapshot eight authoritative lease fields once and revalidate own data descriptors and unchanged values after transcript normalization, before HMAC signing. Reject in-flight revocation, scope mutation or expiry changes.
- Regression commit `48cca4a9`: deterministic adversarial word Proxy cases mutate lease active/shop/expiry while normalizer reads the word; all must reject before signing.
- Offline checkout `git ls-remote` failed with `Could not resolve host: github.com`; targeted Node/Python tests cannot be claimed passed. Exact-head four-job CI still requires verification. No main merge.
- **NEXT CODE ACTION:** execute `python -m unittest tests/media/test_feature7_voicestudio_signed_handoff.py`, inspect exact-head 4-job CI and repair any owner-scope failure; reconcile #513 with current main via serialized integration writer. #911/#926 merged to parent; F4 dependency #910 linked. No GPU/paid/PROD/cloud/WineShopPOS.
