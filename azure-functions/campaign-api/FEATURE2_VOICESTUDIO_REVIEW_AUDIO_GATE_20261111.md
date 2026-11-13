# Feature2 private VoiceStudio original: current-retailer review gate (2026-11-11)

**Security-boundary source, staged for independent review; not deployed.**

The producer saves TWO private PCM WAV objects per one-shot original request: unpadded `original.wav` for a retailer to **listen and review**, and full-reel `render.wav` for the separately approved Feature4 video. Neither is a public link.

`VoiceStudioPrivateStorage.read_verified_original` was added in parent PR #936; this new `feature2_voicestudio_review_audio.read_current_voiceover_for_review` service method enforces the *existing* `SupabaseJWTVerifier` and `TenantStore.member(write=True)` before touching private bytes. It calls the four-RPC SQL client's authoritative `read_private_receipt` for the currently approved shop/campaign/original-key job. It requires `NEEDS_REVIEW`, source-private, rights-confirmed, no publish approval and a valid original SHA, then fetches only the `{shop}/voicestudio/{campaign}/{request}/original.wav` object from private Supabase Storage using server credentials, independently checks SHA again, then repeats current receipt and JWT/RLS membership after I/O. Any cross-shop, viewer, unknown receipt, revoked consent, mismatched digest, expired JWT or failed storage read denies without disclosing data or the secret.

This is **a service method, not an HTTP route**. A future independently reviewed root route must map denied/unauthenticated outcomes to sanitized HTTP statuses, apply `Cache-Control: no-store`, never log WAV/JWT/body, and choose stable content type `audio/wav`. It must NOT expose `render.wav` to a `NEEDS_REVIEW` human; Feature4 can consume it only after a different current `APPROVED_FOR_EDITING` source/tenant/rights check.

Current SQL RPC itself is still a REVIEW-ONLY proposal in PR #923, and the protected Feature2 source/route is staged in #920/#925. No live authenticated two-shop request, licensed model, human reviewer action or physical preview has occurred. Safe production integration requires independently reviewed SQL schema, actual verified DEV identities, human plan approval and licensed model. Any downstream HTML audio control must use only a short-lived *authenticated* same-shop response, not the Supabase service key, a public bucket or a permanent signed link.

No paid model, GPU, Azure/PROD mutation or WineShopPOS change.

## 2026-11-11 next code action — exact branch checkpoint
- Commit `99e87276195bf8d124ddf83c08f4d9ce84722ab9` repaired a critical escaped-newline source bug: `_wav(content)` had been part of a Python comment, so malformed digest-matching WAV payloads were not independently rejected. The validator now executes before post-read SQL/JWT/membership checks. Existing synthetic negative tests `test_digest_matching_non_wav_denied_even_with_swapped_storage_reader` and `test_digest_matching_wav_with_hidden_trailing_bytes_denied` exercise this behavior.
- NEXT CODE ACTION: run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py` on this exact branch; inspect the latest exact-head four-job Part 1 CI for the new commit and repair failures within F2-owned paths. Then verify #937 independent security review and reconcile latest main without bypassing protected #920/#923/#925. Do not merge until independently approved and exact-head 4/4, followed by fresh main 4/4.
- Local pytest and exact-head CI **not verified** at this checkpoint; no deployment or paid model execution.


## 2026-11-11 continuation checkpoint — JWT identity and approved-plan rotation
- Source test commit `563a2c39d914dc59bc54b3591a1fd03243eaee56`: two additional synthetic denial tests cover a JWT subject changing after private WAV read and an approved plan SHA changing between SQL receipt reads. Both must deny bytes before any downstream handoff.
- NEXT CODE ACTION: run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py` at the **current** #937 head, repair any owned test failures, and inspect exact-head four-job Actions. Reconcile with latest main only after checking changed paths and concurrent workers. Independent review of #937 and protected #920/#923/#925 remains required; do not merge or deploy without it.
- Tests and exact-head CI for this new commit are not yet verified. No model inference or hosted resources were used.

## 2026-11-11 checkpoint — post-read fail-closed cases
- Added two synthetic tests on source commit `1c0c1f668198c25c457841d52a27843f6eea1f86`: JWT expiry after private WAV GET and SQL receipt timeout after GET must both deny audio without retry or leaked provider error.
- Prior run #43038370849 had Python success (1/4), with the other three jobs failing at system-package/Chromium installation steps; a failed-job rerun was requested, but it is NOT exact-head evidence for this newer commit.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py` on exact head; inspect four-job Actions on head `1c0c1f66`, diagnose any failures and retry only safe transient infrastructure errors. Reconcile fresh main and independently review protected #937/#920/#923/#925; no merge or deployment before review and 4/4 exact-head, then fresh main 4/4.
- No inference, GPU, paid model, hosted SQL, DEV/PROD deployment or WineShopPOS change.

## 2026-11-13 scoped F2 continuation
- Added four parameterized fail-closed regression cases for mid-read rights revocation, private flag revocation, approval-state change, and review-status revocation in commit `6ad31df98dc6467f73637870f2aa1ad4c5511a8a` (source-only; no inference).
- Local checkout/pytest blocked by `github.com` DNS resolution in execution container; do not claim tests passed. No retry of uncertain provider/SQL/storage effects.
- **NEXT CODE ACTION:** on exact PR #937 head run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py`, inspect the new head's four CI jobs and repair any F2-owned failures; recheck latest main and changed paths, request independent security review, and do not merge protected #937/#920/#923/#925 without review and exact-head 4/4. After any eligible merge verify fresh main 4/4.

## 2026-11-13 latest-main reconciliation checkpoint
- Live GitHub comparison: `main` at `3122079bc818eca2fcd2da8a68657ad0dec81bd1`; F2 review branch diverged **52 ahead / 14 behind**. Seven compared paths include private reader, storage and tests. Do not blindly rebase or overwrite concurrent changes.
- Latest recorded source test commit `6ad31df98dc6467f73637870f2aa1ad4c5511a8a` exists, but commit-specific pull-request workflow query returned **zero runs**; this is **not** a 4/4 CI pass. #937 review submissions: **zero**. Local git checkout remains blocked by `github.com` DNS resolution.
- **NEXT CODE ACTION:** obtain a checkout of `feat/feature2-voicestudio-review-audio-gate-20261111`, run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py`, inspect current exact-head CI via Actions, and fix any owned failures. Then carefully reconcile 14 incoming main commits while preserving seven changed paths, rerun 4/4, and request independent protected security review. Do not merge or deploy before review, then verify postmerge main 4/4.


## 2026-11-13 secure RIFF regression continuation
- Added two synthetic digest-matching RIFF metadata-chunk injection denial cases (`LIST` and `JUNK`) to `tests/ai/test_feature2_voicestudio_review_audio.py`, commit `6973c2076cfb5d2d5a3202c617b0a456a709a3f9`. Source implementation unchanged; no model/cloud execution.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` at the current exact PR #937 head, verify all four Part 1 CI jobs on that head, and fix any failures within F2-owned paths. Check fresh main and reconcile the stacked branch only with protected independent review; do not merge/deploy #937/#920/#923/#925 without required approvals. After an eligible merge, verify new main 4/4 before marking accepted DONE.

## 2026-11-13 F2 exact-head source checkpoint
- Added two parameterized digest-matching RIFF `LIST`/`JUNK` metadata injection denial fixtures to `tests/ai/test_feature2_voicestudio_review_audio.py` on source commit `39c92ac8a502c91f1800bd525db3f8e3887ce3ff`. No model, cloud or SQL mutation.
- At inspection, latest `main` was `3122079bc818eca2fcd2da8a68657ad0dec81bd1`; #937 was 58 ahead / 14 behind before this commit. #918 is merged; #920/#923/#925/#937 are open draft and #937 has zero reviews. Previous head `d8598f19` had zero commit-associated workflow runs. No local pytest: container DNS cannot resolve github.com.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` at `39c92ac8`, inspect exact-head four-job CI, repair F2-owned failures, reconcile with fresh main only after checking overlaps, and obtain independent security review. No protected merge/deploy before review and 4/4 exact-head; verify fresh main 4/4 after any eligible merge.


## 2026-11-13 source-only checkpoint (F2-19/F2-20)
- On PR #937, `bd510b0293697da310d831b671574847b74d499b` rejects untrusted `str` subclasses for Authorization at the private original WAV gate; `662380b7b13949561874e87b75bc37e8858ba0b7` adds a regression verifying rejection before JWT, membership, SQL, or storage. No route, SQL migration, paid inference, cloud or WineShopPOS changes.
- Local targeted pytest unavailable: runner cannot resolve `github.com` to clone repository. **Do not count tests or CI as passed.**
- NEXT CODE ACTION: verify the new final head of #937, run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` in a connected worktree, repair failures in F2-owned files, then verify all four mandatory exact-head CI jobs. Recheck latest main and protected #920/#923/#925 reviews before any reconciliation; #937 remains protected and requires independent security approval. After eligible integration verify fresh main 4/4 before marking task done.


## 2026-11-13 F2-19/F2-20 continuation — receipt revocation regression
- Commit `b7c2008f19fa50b9171ab43ac3e1949d7f609879` adds four parameterized security regressions for mid-read SQL receipt changes: audio asset identity, commercial rights, publish approval, and reviewed plan digest. No production runtime, models, cloud, SQL or root route changed.
- `main` inspected at `3122079bc818eca2fcd2da8a68657ad0dec81bd1`; #918 merged; #920/#923/#925/#937 remain open and protected. #937 remains draft/stacked on a feature branch and is NOT main-merge eligible.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` at the latest exact PR head. Inspect exact-head four-job CI, repair owned failures, then reconcile stacked base against fresh main only after independent security review. No merge or deployment without approvals, exact-head 4/4 and fresh postmerge main 4/4.


## 2026-11-13 F2 hourly source checkpoint
- Prior exact head `6af02564fabfdf7092ab5e0e09d1a35e65fa5732`: GitHub Actions run [43425661916](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43425661916) completed SUCCESS, all four mandatory jobs green (Python, frontend, FFmpeg, Supabase isolation). This evidence is for the **prior** head only.
- Added two source regression tests in commit `d61b0db99506be488209b94a3d5642b93db6427f`: fail-closed SQL factory exception before private storage and rejection of mutable bytearray storage payload without post-read disclosure. No production change, cloud call, paid model or deployment.
- Current protected PR #937 remains unmerged; latest main `3122079bc818eca2fcd2da8a68657ad0dec81bd1`, source branch previously 74 ahead/14 behind; no independent PR review recorded at inspection. Protected #920/#923/#925 remain open. Do not merge or force rebase on this evidence.
- **NEXT CODE ACTION:** verify the new exact-head four-job CI and targeted `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py`; if failures, repair F2-owned tests/source. Then reconcile latest main non-destructively, repeat exact-head 4/4 and obtain independent protected security review before merge. Verify fresh main 4/4 after any eligible merge. Do not apply SQL migrations or enable model inference.

## 2026-11-13 F2 code-first checkpoint
- Previous exact head `dd460395ad0650952a7c983b704bda3c15de9aad` had four successful mandatory jobs in [Actions run 43434353167](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43434353167/jobs). Independent reviews: zero; PR #937 remains protected and draft, stacked on the private-reader parent branch.
- Commit `161d0cba0a0faecd272b637c4e5292c3e5f8a29b` added three synthetic digest-matching malformed PCM format cases to the F2 reviewer security test: float format, non-16-bit declaration, and invalid frame alignment. No service behavior, cloud, paid model, or protected SQL changes.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py` on current #937 head; inspect exact-head four mandatory CI jobs, repair any failed owned test, then request independent security review. Reconcile current main and protected parents only after review; never merge draft/protected work without approval. Do not infer green from prior-head CI.
