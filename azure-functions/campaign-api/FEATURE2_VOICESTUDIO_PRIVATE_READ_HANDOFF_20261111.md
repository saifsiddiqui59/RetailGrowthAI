# Feature2 VoiceStudio private WAV read contract (2026-11-11)

This Feature2-owned change adds **real, bounded, SHA256-verified private WAV byte readers** to the existing server-side Supabase Storage adapter at `azure-functions/campaign-api/feature2_voicestudio_storage.py`.

- `read_verified_original(shop_id,campaign_id,request_id,sha)`: exact original VoiceStudio PCM, for a **separately authenticated human reviewer** only.
- `read_verified_render(shop_id,campaign_id,request_id,sha)`: exact padded Feature4 PCM, for the independently authorized Feature4 renderer only.
- Both derive immutable object paths solely from canonical v4 shop/campaign/request IDs, fetch from existing private `retailgrowth-media` bucket with backend-only API key, reject redirects/status changes, cap binary bytes to 8MiB, require valid PCM WAV and compare actual SHA against current trusted SQL evidence. No signed/public URLs or credentials are returned to callers. Existing `verify_pair` now uses the same read code but returns only verified byte counts.

**No public endpoint is created.** These are server-only byte transport primitives and **do not** perform user authentication, editor membership, review authorization or rights grants. They must only be called *after and before* an independent current user/JWT/RLS rights and SQL original-key receipt check. The new synthetic tests prove correct object selection, no path injection, fail-closed readback, bounded profile and no automatic retry.

Integration next: server-only authenticated `NEEDS_REVIEW` audio preview with current editor membership and original-key receipt; Feature4 current `APPROVED_FOR_EDITING` rights check before calling render reader; then true audio/video, reviewed captions and two-shop DEV E2E after an approved commercial model. Root HTTP registration and SQL schema still require independent security review in PRs #920/#923/#925.

Source-only, model OFF, no GPU/paid provider, hosted DEV/PROD or WineShopPOS change. F2-19/F2-20 not fully accepted.


## 2026-11-13 F2-19/F2-20 source-only checkpoint
- PR #937 source/test commit `82d60339222d0d4c050ccc4045f7cf02a73556f6`: added seven parameterized denial cases for SQL receipt truthy integer coercion, list-valued review state, and uppercase SHA digests. No runtime behavior or cloud resources changed.
- Exact-head PR workflow query returned **zero runs at inspection**; 0/4 verified, not green. Targeted pytest not executed in this run. PR #937 remains draft, stacked on private reader branch, and requires independent protected security review; #920/#923/#925 remain open.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` at head `82d60339222d0d4c050ccc4045f7cf02a73556f6`; inspect exact-head 4-job Actions, fix any owned failures. Compare latest main and all changed paths before safe reconciliation. Do not merge/deploy protected branches without independent review and 4/4 exact-head, then fresh postmerge main 4/4.


## 2026-11-13 F2-19/F2-20 next source checkpoint
- Head `86ee03c2b93e241dec741d9756b4fdf7b35ee564` on draft PR #937: tightened SQL review receipt validation to require an exact primitive string for `review_status`; added regression denying equality-spoofing provider objects before private Storage GET. Two source/test commits; no cloud or model operations.
- GitHub Actions exact-head query at checkpoint returned no PR runs (0/4 verified). Local checkout/pytest unavailable: sandbox cannot resolve github.com; do not claim passing tests. Independent security review remains required, and this stacked PR is not eligible for direct main merge.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` on exact latest PR head; inspect four exact-head CI jobs and fix failures. Compare latest main and all protected PRs, safely reconcile stacked parent and obtain independent protected review before any merge. After merge verify fresh main 4/4 and only then propose canonical task DONE receipt.


## 2026-11-13 next F2-19/F2-20 code checkpoint
- Added four post-storage-get revocation regression cases for commercial rights, publish approval, private visibility and review state in commit `66d461a4eae3b06d839b9386a0d0be4e3c0db63f` on PR #937. No runtime/cloud/model changes.
- Prior head `3bea13d347ea45ffaf07c0dd3a4b2a6adeef36c8` had four successful GitHub Actions jobs (run 43462581416). This is NOT evidence for the new head.
- **NEXT CODE ACTION:** inspect exact final PR head, run targeted `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py`, fix any failure, verify four exact-head Actions jobs. Then reconcile stacked parent/current main only after reviewing changed paths; obtain independent security review before protected merge. Do not deploy SQL, cloud, GPU or paid model.


## 2026-11-14 F2-19/F2-20 PCM format enforcement
- Source commit `d1cdba9f29dae3fa72f5d6da0cb0d48b14d1d804`: enforce literal PCM format tag 1 and 16-bit fmt depth before private review disclosure, independent of Python wave decoder behavior.
- Regression commit `532c631d790bfb1e446ec08f60d186a14a352704`: four matching-SHA malformed WAV format cases (float, extensible, 8/32-bit). Source-only; no model, SQL migration, cloud deployment or WineShopPOS change.
- **NEXT CODE ACTION:** on exact current PR #937 head run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py`, inspect exact-head four mandatory CI jobs and fix any failures; check latest main and protected PR #920/#923/#925 before reconciliation. Stacked draft PR #937 cannot be direct-main merged and independent security review is still mandatory. Verify fresh main 4/4 after any eligible reviewed merge; do not mark F2-19/F2-20 DONE prematurely.


## 2026-11-14 F2-19/F2-20 source checkpoint
- Added three synthetic denial tests on PR #937 at commit `e68a9074ebc79ff6210b60453aedd25fa1add667`: SQL receipt audio-asset swap, rights revocation after private GET, and JWT revocation after private GET. No model/cloud/SQL deployment.
- Exact new-head PR Actions query returned zero runs at inspection (0/4 verified); no local pytest executed. Independent PR reviews: zero. Branch compare with current main: 93 ahead / 16 behind; stacked draft PR, not merge-ready.
- **NEXT CODE ACTION:** execute `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` on the new head, fix any actual failures, verify 4/4 exact-head CI; then independently review protected #937 and its parent dependency. Do not merge without approval or claim DONE. Continue F2-owned authenticated original WAV HTTP adapter only after reconciling shared/root route ownership with #925; retain generic denials, no-store, cross-shop negative cases and server-only credentials.


## 2026-11-14 F2-19/F2-20 malformed HTTP wrapper denial
- Source commit `310820e55a608044c90d668bae0a06363ebe28f7` treats missing/invalid request header wrappers as unauthenticated (401, empty body) rather than exposing provider-outage semantics; regression commit `749bec2cd61d55de1efa77edb28a8164862c24bc` adds five negative request shapes and verifies no private service call. Source-only; no route registration or deployment.
- Immediately after the test commit, exact-head PR workflow lookup returned zero runs; **0/4 verified**. No local pytest execution claimed. PR #937 is still draft/stacked, protected independent review required.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_http.py tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` on exact latest head; inspect four mandatory CI jobs for that SHA, fix failures on F2-owned paths. Reconcile parent/main only after inspecting current diff and protected #920/#923/#925, obtain independent review; no merge/deployment until requirements met and postmerge main 4/4.


## 2026-11-14 private HTTP cache hardening
- Source commit `c7014aa755b57a4361f37f420a6224568a40ab53` adds `Vary: Authorization` and `Referrer-Policy: no-referrer` on every private original-WAV response, including denials; test commit `79dfbe3af3b98fc5e8e18343bd68dca4d6035958` checks both authenticated success and missing-auth denial. No root route, paid inference, cloud, SQL, F4/F7 or WineShopPOS changes.
- Exact test-head workflow lookup returned zero runs immediately after commit (0/4 verified). Independent #937 reviews: 0. Local pytest not executed; source-only checkpoint, NOT accepted DONE.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_http.py tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` on latest #937 head; inspect exact-head four CI jobs, repair any owned failures. Recheck fresh main and protected #920/#923/#925/#937, secure independent review and preserve stacked parent before any eligible merge. Verify fresh main 4/4 after merge. Do not deploy or enable paid models.


## 2026-11-14 F2-19/F2-20 empty WAV fail-closed checkpoint
- Source commit `1f8b9c622cbbe3038a7d421bce25ee4152ba4da3`: reject zero-length byte responses from private review reader instead of returning HTTP 200 with `audio/wav`.
- Regression commit `9457634fe0996551e99a58aaffb2e493fdd39b00`: assert empty bytes yield HTTP 404, empty body and no audio content metadata. No root route, credentials, model, SQL or cloud mutation.
- Exact test-head PR Actions lookup returned 0 runs at inspection: **0/4 verified**. Local pytest not executed. Protected stacked draft #937 requires independent security review and parent reconciliation; #918 is already merged.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_http.py tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` on exact #937 head; fix F2-owned failures and verify all four exact-head CI jobs. Review current main and #920/#923/#925, reconcile stacked parent, obtain independent security approval before any merge. After merge verify fresh main 4/4 and only then record integrated DONE.


## 2026-11-14 blank Authorization fail-closed checkpoint
- Source `cb5d703bcf8c24748cacd7f15a6751c1cb833b12` rejects empty/whitespace-only Authorization before calling private review service. Regression `64c4581c74f76491896ea7a2906ec34a5769b677` checks denial and no downstream invocation. No model, cloud, database, route or F4/F7 mutation.
- **NEXT CODE ACTION:** execute `python -m pytest -q tests/ai/test_feature2_voicestudio_review_http.py tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` on exact PR #937 head, inspect all four exact-head CI checks, and fix failures. Independently review protected stacked PRs #920/#923/#925/#937 and reconcile parent against fresh main before merge; no bypass. After any eligible merge verify main 4/4.


## 2026-11-15 F2-19/F2-20 Authorization control-byte hardening
- Source `eb4a5c6ac83ed267d37ba26204ac01819944f511`: reject ASCII control bytes (including CRLF, NUL and DEL) in the HTTP Authorization header before private audio service invocation; test `d4985d8b74e21a2252694e1bc391b327fc9394c9` covers five injection/control cases and no downstream invocation.
- GitHub exact-head Actions lookup returned zero runs immediately after test push: **0/4 verified**, not green. Local pytest could not run because sandbox cannot resolve github.com. No independent review on protected draft #937; branch is stacked, not direct-main-ready. #918 merged; #920/#923/#925 remain open. No cloud/model/SQL/F4/F7/WineShopPOS changes.
- **NEXT CODE ACTION:** run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_http.py tests/ai/test_feature2_voicestudio_review_audio.py tests/ai/test_feature2_voicestudio_riff_envelope.py` on exact new head; fix owned failures and verify all 4 mandatory exact-head CI jobs. Recheck main and protected dependencies, reconcile parent safely, obtain independent security review before merge. Verify postmerge main 4/4 before any DONE receipt.
