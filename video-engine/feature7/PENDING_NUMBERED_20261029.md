# Feature #7 — Numbered Remaining Work Ledger (2026-10-29)

**Scope:** Feature #7 Smart Editing / speech-to-text only. This is NOT a combined
all-features RetailGrowthAI backlog; Feature2 #551, Feature4 #322, and
coordinator integration work are identified as dependencies, not claimed as F7
owned work. Branch `feat/feature7-uploaded-footage-semantics-20261028`; draft PR #513.

**Verified at audit:** F7 HEAD `3c3ec5e59241c12ef30fde0ca87170c8273f9b00`,
PR CI [#40932986523](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40932986523)
and push [#40932979014](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40932979014):
4/4 success, 537 media tests OK, five explicit skips. Feature2 #551
`0a3c28610cd04fc30080ee1456ab34b291630656`, DRAFT;
Feature4 #322 `6ffd79b980ac161e9022a7c3fbfabe313b7d1647`, DRAFT;
Feature3 #630 is MERGED. Main was checked separately. This audit creates
TASK IDs, not model-inference evidence, production deployment or new passes.

**Counting rule:** Exactly 23 unique remaining acceptance/development work
items: **6 F7-owned independent CPU/non-GPU source tasks**, **17 gated external,
owner-dependent or real-asset tasks**. A prepared conditional test is NOT a
passing live test. Several dependents are non-GPU too. No task requires paid GPU.

## A — Feature7-owned independent non-GPU tasks (6)

| ID | Priority | Task — exact missing acceptance | State |
|---|---|---|---|
| F7-01 | P1 | Run the exact SHA-pinned Feature3 original 9s Full-HD MP4 through Feature7's actual **local edit proposal/review pipeline**, not just FFprobe/manifest validation; retain original bytes and do not imply virtual try-on | TODO; genuine artifact acquired/verified, pipeline handoff not tested |
| F7-02 | P1 | Stage original Feature3 Actions ZIP 12879355229 on a private CPU runner and execute optional **positive** `test_feature7_feature3_artifact_preflight.py` + `test_feature7_feature3_actual_demo.py`; capture independent command result. Routine CI currently skips original-asset tests | CONDITIONAL TEST NOT RUN in normal CI |
| F7-03 | P1 | Add real (not fake DOM) standalone browser/keyboard/mobile accessibility QA for existing F7 reviewer and caption-correction UI: focus, screenreader labels, pending/retry, blob URL revocation, VIEWER readonly. Feature4 mounting is separately blocked | Partial: source and fake DOM tests pass; browser acceptance pending |
| F7-04 | P1 | Extend F7-owned worker/job crash, process-timeout, SIGKILL, stale lease/replay and concurrent original-WAV recheck regressions using CPU local backend; **do not** duplicate the coordinator's PostgreSQL persistence | Partial: SQLite CAS/retry tests exist; full worker-failure matrix incomplete |
| F7-05 | P0 | Prepare reproducible CPU-only **transitive** wheel/dependency lock and offline installation/readiness receipt for pinned Faster-Whisper + CTranslate2 + FFmpeg; record approved hashes/OS targets, no per-job downloads. Do not self-approve model/commercial rights | Partial: model inventory & CPU preflight code exist, deployable dependency closure unverified |
| F7-06 | P1 | Review latest separate Feature2 signed-original-WAV reviewer and Feature4 review/edit payload against current F7 envelope; maintain machine-readable compatibility fixtures, versioned coordinator proposal and scoped negative tests without changing shared contracts | Partial: versioned signed contract and conditional tests exist; latest cross-branch drift review outstanding |

## B — Dependent release/acceptance tasks (17; all possible without GPU)

| ID | Priority | Task — exact missing acceptance | Blocked on / owner |
|---|---|---|---|
| F7-07 | P0 | Provision the actual pinned `Systran/faster-whisper-small` CTranslate2 checkpoint and operator-reviewed commercial model/dependency permissions, immutable SHA256 manifest; do not mistake test-weight bytes for a model | Approved assets/CPU runner + rights reviewer |
| F7-08 | P0 | Pass real no-egress CPU/INT8 worker preflight with the installed checkpoint and pinned wheels, then execute actual `WhisperModel.transcribe` on non-synthetic speech | F7-07 + infrastructure operator |
| F7-09 | P0 | Assemble rights-cleared **human voice + independently authored transcript** samples for English (including Indian English), Hindi and Marathi with retailer terms, speech/music/noise/pauses | Audio rights owner + independent human transcriber |
| F7-10 | P0 | Run genuine source-SHA-bound ASR word-error-rate (WER) tests, per language/accent/retailer term with documented targets and repeated CPU results | F7-08 + F7-09 |
| F7-11 | P0 | Human-listen verification of actual word-level timestamps, repeated words, mixed languages, speech/music discrimination, mispronunciations and subtitle alignment; record false positives | F7-10 + bilingual reviewers |
| F7-12 | P1 | Measure real loaded-model CPU RAM, real-time factor, simultaneous jobs, timeouts, throughput and actual hourly CPU-only cost; define tenant safety/scale policy from evidence | F7-08/10 + CPU host price |
| F7-13 | P0 | Obtain a real approved original Kokoro WAV from Feature2's actual TTS worker, bound to shop/asset/script/creative-plan/source SHA and private rights; no tone fixture | Feature2 #551 weights/voice/legal checks and coordinator |
| F7-14 | P0 | Run same-checkout **actual** F7 signed original-WAV result through Feature2 Python `review_signed_audio_transcript` and signed WER consumer, with active tenant/job; verify altered SHA, foreign job and revoked grant denials | Feature2 #551 integrated with F7 + F7-08 + F7-13 |
| F7-15 | P0 | Obtain actual rights-verified retailer-owned spoken MP4 and associated current garment/stock rights; distinguish public CC0 technical test from customer approval | Retailer/asset rights & coordinator |
| F7-16 | P0 | Implement/enable hosted JWT+RLS authenticated private MP4/WAV upload, media registration, same-shop rights and quotas; bind F7 worker trust to real server registry | Coordinator / existing backend / Supabase DEV |
| F7-17 | P0 | Implement/verify authorized private video/audio playback, signed upload/download URLs, expiry, asset/source revocation, and no cross-tenant read | Coordinator / media storage backend |
| F7-18 | P0 | Implement actual Postgres durable ASR/reviewer job record, lease-fenced retry/poison/outbox, atomic human caption/edit approval/reject/revoke and idempotent execution | Coordinator / auth/schema and hosted DB |
| F7-19 | P0 | Mount the existing Feature7 review/caption editor inside authenticated Feature4 Video Studio with actual private preview, current role, reviewer confirmation and persisted callbacks | Feature4 #322 + coordinator F7-16..18 |
| F7-20 | P0 | Execute human-approved sparse jump cuts, B-roll, caption overlays, original or generated narration, music ducking and final HD video **in existing Feature4 renderer**, not new F7 render engine | Feature4 #322 + approved F2/F3/F7 source assets |
| F7-21 | P0 | Run actual final video human quality review: captions/audio/lip-sync/cuts/music/garment congruence and authorized rights; separately obtain signoff before publish | Feature4 output + F7-11, F7-15 |
| F7-22 | P0 | Run signed-in hosted DEV end-to-end: positive same-tenant upload→ASR→editor→approval→final private playback, and foreign/revoked/expired/replay/lease/rollback negatives | Coordinator + F7-08, 13..21; Azure #249 ingress as applicable |
| F7-23 | P1 | Resolve coordinator-owned compatible package/import closure (Issue #650 affecting Feature2/4), integrate cross-branch work, verify merge-base and **postmerge exact-head** four-job CI; coordinator updates shared PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG and chooses release | Coordinator + tested Feature2/4/F7 PRs |

## Explicitly NOT counted as pending implementation

Real upstream Faster-Whisper CPU **entrypoints** for private MP4/original WAV,
true staged WAV SHA rechecks and signed result, unsupported-language/model
revision hardening, offline model manifest inventory/preflight commands,
source-timed AutoBroll editing, original-audio-preserving trims, original private
video integrity, caption correction source/UI, real FFmpeg CC0 smoke, local
SQLite fencing, safe review-only permissions, 9s original Feature3 artifact
SHA/FFprobe validation and ZIP negative tests, 537 media tests and four green
branch jobs. These do not establish actual model weights, live customer
authorization or release.

**Progress convention:** Refer to `F7-01`...`F7-23`. Mark only observed
completion, not prepared-source or mock tests as live acceptance. If
an item moves from dependent to executable (e.g. asset delivered), preserve
its ID and update owner/status rather than renumbering. No GPU/paid providers,
WineShopPOS, shared coordinator docs or PROD modifications.


## 2026-10-29 — Continue independent source work while dependencies remain blocked

- **A new coordinator intake matrix** `video-engine/feature7/DEPENDENCIES_F7_07_23.md` records 17 exact stable `DEP-F7-07` ... `DEP-F7-23` IDs, each with owning feature, required output and measurable acceptance, without changing or renumbering the 23 fixed F7 task IDs.
- **F7-01**: new conditional original-artifact source-to-`preparePrivateReview` two-scene **test-only** pipeline (`test_feature7_feature3_private_review_actual.py`) uses the authentic F3 9s technical MP4 SHA twice as distinct local scene inputs (two 7.5s trims to fill 15s). Transcript fixture has **zero words**, F7 yields no captions and zero paid/model calls; claims neither inference nor a garment-wearing model, production ownership, final render or approval. Since ordinary PR CI has no original F3 ZIP, **actual pipeline positive is NOT accepted until staged external artifact test succeeds**. Asset ZIP/hash/ffprobe verified independently in session, not as actual model speech.
- **F7-02**: authentic original ZIP is available to operator and SHA/stream verification already observed; the exact positive CI test remains opt-in using `FEATURE7_F3_ORIGINAL_ARTIFACT_ZIP`, not counted as passed in an ordinary CI run with skip.
- **F7-04**: incrementally added CPU worker crash / bounded-timeout failure-denial regression (see `test_feature7_original_wav_cpu.py`); this is local source behavior, not production PostgreSQL crash recovery.
- **F7-06**: reviewed Feature2 separate current `docs/feature2/F7_SIGNED_WER_HANDOFF_20261029.md` and Feature7 `feature4_speech_review_handoff.mjs`; F2 requires actual signed original WAV+human reference, F4 requires real kept-source preview evidence; an advisory/fixture cannot be coerced to publishable. True cross-branch integrated test remains DEP-F7-14/19.
- **F7-03 and F7-05**: real installed browser/worker wheelhouse evidence still missing; existing fake-DOM and mocked dependency tests remain source evidence only, and no checkpoint/rights license approval is inferred. Continue their source test enhancements independently; don't block other tasks.
- The feature remains **DRAFT** and F7-owned code/docs only. Shared coordinator docs and `.github/workflows` are intentionally unchanged. Each pending acceptance is preserved under the existing ID.


## 2026-10-29 — Six independent tasks: source progress, separate from acceptance

| ID | Verified source work in this batch | Outstanding acceptance (do not mark DONE without it) |
|---|---|---|
| F7-01 | Added `test_feature7_feature3_private_review_actual.py`: two separately identified 7.5s segments of the **same exact pinned 9s F3 source** use zero-word, zero-AI-call review-only proposal; original SHA checked twice; foreign/hash/revoked negatives | Run actual positive using downloaded original ZIP staged in **same** repository test runner; no speech inference or new media rights may be claimed |
| F7-02 | Original Feature3 technical ZIP `12879355229` locally checked: image SHA manifest and real 1080x1920 H264/AAC 9s MP4 hash match | Set `FEATURE7_F3_ORIGINAL_ARTIFACT_ZIP` and execute repo's exact original ZIP + pipeline positive tests. CI without artifact will skip |
| F7-03 | Added optional actual Chromium + Python Playwright 390px mobile/keyboard and 375px VIEWER read-only UI tests using actual JS modules via loopback HTTP; checks duplicate submissions, callback-not-approval, caption edits and destroy/revoke contract | Execute in runner with Chromium + Playwright; still not hosted Feature4 reviewer/auth/real screenreader certification |
| F7-04 | Added real CPU child process nonzero-exit/SIGKILL/bounded 5s timeout regression to original WAV worker tests. Existing SQLite concurrency/fencing tests retained | Full server Postgres crash/restart/journal resume and current shared job lease are DEP-F7-18, not simulated by these tests |
| F7-05 | Added strict `offline_wheelhouse_audit.py` + tests: independently SHA-check operator wheel archives, verify names/versions/declared conservative transitive dependency closure; always `approved_for_deployment:false` | A real reviewed transitive Linux CPU wheelhouse and actual CTranslate2 ABI/model readiness still require DEP-F7-07 and DEP-F7-08; fake wheel fixtures are not real installations |
| F7-06 | Reviewed F2 signed original WAV and WER consumer (PR #551) and current F7→F4 speech-review source adapter; existing versioned F7 handoff unchanged, exact-feature consumer test remains conditional | Coordinator must combine latest F2/F4/F7 source in one checkout and run real contract/authorization tests (DEP-F7-14, -19, -23) |

**Do not stop:** F7 continues all independent tests as inputs become available. Stable `DEP-F7-07` ... `DEP-F7-23` owner/output/criteria are in `DEPENDENCIES_F7_07_23.md`. A passing unit/security/fixture test **never** establishes actual model recognition, customer ownership, publication or hosted approval. No GPU/paid API/PROD/WineShopPOS/shared-coordinator file modified.


## 2026-10-29 — F7-03 safety continuation (source, not accepted completion)
- Implemented stale async response fencing for review and caption submissions, denies duplicates from unchanged scene/cue selection, and prevents callback DOM updates after reviewer destroy. Added offline Node regression and optional real Chromium mobile test.
- Evidence to verify: `tests/media/test_feature7_reviewer_async.py`, `tests/media/test_feature7_reviewer_actual_browser.py`, and exact final-head PR CI. F7-03 remains **PARTIAL**, not an integrated DONE; authenticated Feature4 mounting and true live account/rights tests are outstanding. No paid services, production operations, shared coordinator documents or WineShopPOS changes.


## 2026-10-29 — F7-04 actual worker SIGKILL source regression
- Added bounded POSIX child-process kill → SQLite WAL reclaim/new fencing token → deny late old-worker completion acceptance test. This closes one previously unexercised local crash path but does not replace coordinator Postgres or remote execution idempotency. F7-04 still PARTIAL. Exact-head CI and actual run evidence must be checked independently before marking the local test passed.


## 2026-10-29 — F7-05 wheelhouse archive/inventory security continuation
- The existing offline wheelhouse verifier now validates strict wheel filename distribution/version/tags, root inventory equality (reject extra unapproved .whl), dist-info directory scope, archive member duplication/path/symlinks and bounded decompression of package metadata; malformed Requires-Dist and non-object operator manifests fail closed. New regression cases re-pin altered fake wheel SHAs to prove metadata/ZIP checks aren't only hash checks.
- This is a **source-only** hardening; real Faster-Whisper+CTranslate2 version constraints, CPU ABI, model licensing, original weights, offline installation and human transcript tests remain external DEP-F7-07/08; no inference/hosting. Exact-head 4/4 branch CI required. F7-05 remains PARTIAL.


## 2026-10-30 — F7-02 original binary artifact locally verified, source pin hardening
- The original Feature3 Actions artifact `12879355229` archive was downloaded through connected GitHub and staged as a private offline test fixture. Its 7 actual ZIP members match independent SHA256 inventory; the 9-second 1080×1920 H.264/stereo AAC technical MP4 has SHA256 `16ceaa91a5dad57de023f45b21eee45772f361a18299801e9e27b6ae49ce9f22`. An isolated copy of the source preflight and original-artifact unit tests returned **5/5 PASS** including a new re-packaged-metadata tamper regression, with `FEATURE7_F3_ORIGINAL_ARTIFACT_ZIP` set. This is genuine technical media, NOT customer media, VTON or human speech.
- Previously the preflight pinned the MP4 SHA and checked (but did not hash-pin) the embedded manifest, license and image data. F7 now pins **all seven original entry digests**, refusing semantically altered licensing and metadata alongside image/video changes, and adds opt-in original-ZIP regression. The optional archive is *not* committed into the repository; routine 4-job CI must skip original-asset tests until the runner is explicitly staged with those bytes.
- This local isolated preflight is **not** a combined same-checkout Feature7 `preparePrivateReview` positive execution: `F7-01` and the original-run acceptance portion of `F7-02` remain pending until that hosted/original source test runs under an authorized checkout. F7-02 does not become integrated DONE from a local artifact/negative test. No cost-bearing AI, GPU, PROD, retailer rights or trusted approval was involved.


## 2026-10-30 — F7-01 audio-truth fail-closed source hardening
- `preparePrivateReview` now rejects a supplied nonempty word transcript when exact-byte local FFmpeg analysis confirms **no audio track** or **entirely silent decoded AAC**. This closes the previous F7-01 opt-in test's `fake_speech` no-op/skip case: the actual pinned F3 silent source must reject fabricated speech words. `tests/media/test_feature7_pipeline.py` now exercises this with a genuinely encoded silent H264/AAC engineering fixture, unchanged source SHA, empty-word advisory success and fabricated word failure.
- **Critical boundary:** `silencedetect` is not speech/VAD; non-silence never proves real words or model inference. All real words still require signed actual ASR and human QA. Original external artifact full `preparePrivateReview` positive and negative acceptance remains unexecuted in a combined authenticated checkout, and no user sample or model call was produced.


## 2026-10-30 — F7-05 conservative dependency version audit (source-only)

- Tightened `offline_wheelhouse_audit.py` to compare actual pinned numeric dependency versions against declared bounded `Requires-Dist` constraints (`==`, `!=`, `>=`, `<=`, `>`, `<`, `~=`); deny conflicting versions, direct URL references, unsupported version syntax and trailing garbage. Existing SHA, ZIP metadata and no-symlink checks remain. Markers are NOT evaluated for host applicability: every marker-qualified dependency remains required, conservatively. This is not a full PEP 440/508 resolver.
- Added synthetic repinned wheel tests for a conflicting CTranslate2 constraint, safe numeric range with a marker, direct URL and malformed/trailing syntax. No actual wheel/model downloaded, installed, licensed or executed. CI outcome must be checked at the exact new head.
- **F7-05 remains PARTIAL**, awaiting a real operator-reviewed Linux CPU wheelhouse, CTranslate2 ABI install proof, commercial/model rights and actual offline speech WER; dependencies `DEP-F7-07` and `DEP-F7-08` unchanged. Do not mark integrated DONE. No paid/GPU/PROD/WineShopPOS or shared coordinator files touched.


## 2026-10-30 — F7-06/F7-G batching: shared F2/F4 contracts (source-only)
- **F7-06 + F7-F:** Feature7's existing Feature4 review-only AutoClip/AutoBroll speech packet is now deeply frozen at the nested cut, projection, caption, music and QA arrays after digest creation. Reversed or zero-length visible cut spans are rejected. Security regressions check denied post-digest mutation and unchanged caller inputs; no new F4 renderer or approval state.
- **F7-G + F7-14 readiness:** Added cross-feature test for F2's real signed original-WAV consumer to refuse a source-rights revocation between its initial and final authority lookups. This is a conditional source contract test **skipped until PR #551 is integrated**; no mock claims of genuine F2 inference/authorization.
- **Batch policy:** Grouped three independent source/test adjustments in one commit and one branch push, then inspect mandatory 4/4 exact-head CI. This reduces repeated full CI, but does not defer safety regressions or bypass coordinator postmerge 4/4. F7-06 remains PARTIAL; main/production integrated DONE unchanged. No GPU, paid services, PROD, WineShopPOS or shared coordinator doc edits.

## 2026-10-30 — Feature7 batch: review/caption request mutation fences
- **F7-N/F7-X/F7-G (independent CPU-only source):** Human edit request constructor now deeply freezes the cloned proposal scenes, captions and metadata, rather than freezing only the outer request. A queued callback cannot mutate nested trim or mark the proposal approved in the same JS process. Server still reloads rights/revision and persists authoritative approval.
- **F7-O/F7-X/F7-G:** Caption correction request constructor freezes each digest-bound correction row and the array, rather than just the outer request and array. Host can no longer mutate corrected words after the request hash hint is formed. The hint is not a cryptographic authorization signature or approval. Existing media test modules gain denial regressions.
- **Batch policy:** Four production/test files and two F7-owned ledgers, one push plus exact-head CI, no demo, paid inference, GPU, hosted authentication, PROD or WineShopPOS. DEP-F7-16/18/19/23 still require coordinator/Feature4 integration. 0/35 integrated DONE before accepted merge and new main 4/4.

## 2026-10-30 — F7-04 local dispatch fencing/bounded CPU QA batch
- **F7-04 / F7-Q / F7-G:** The Feature7 SQLite-approved-edit dispatch prototype now validates an incoming lease *before* any SQL lookup and binds every copied lease identity/scope field to the persisted tenant-scoped dispatch: dispatch ID, idempotency key, shop, campaign, draft SHA, candidate SHA, attempt, fence and expiry. Prior code validated the last four but not all copied scope/hash fields; an altered dataclass is now denied with a domain error rather than accepted or raising an unhandled AttributeError.
- **Targeted negative coverage:** Add tests for altered fields across all three worker lifecycle methods (heartbeat, fail_and_retry, finish); malformed/non-dataclass leases; and approval revocation during an active lease blocking heartbeat/retry/ACK. Each test checks a valid lease can still complete or a revoked job remains terminal. Existing SIGKILL/retry/concurrent SQLite tests remain active.
- **Exact scope:** This local regression is a *prototype*, not actual authoritative Postgres/Azure worker approval or exactly-once media rendering. Real server JWT/RLS, durable outbox, provider ACK and Feature4 final output remain coordinator/Feature4 DEP-F7-18/19/20. No GPU/paid inference, customer media, hosted DEV/PROD changes or WineShopPOS. Source-ready only: F7-04 remains PARTIAL until the full failure/worker matrix and approved integration; no new integrated DONE before coordinator merge and fresh main 4/4.


## 2026-10-30 — Verified five-stage progress-reporting convention
- New Feature7-owned `video-engine/feature7/PROGRESS_STAGES_20261030.md` keeps **source-complete 8/35**, **tested 8/35 source-complete tracks (mapped individual media tests)**, **PR-ready 0/35 (draft PR)**, **integrated 0/35**, **blocked 8/35**, and **in-progress 19/35** separate. Media evidence: PR #513 head `a394f2f406422a5969b783d2d719a27fd2d510ab`, push #41054432688 and PR #41054442704 each 4/4; 391 media tests, 12 skipped. Tested is offline/source-only; no real ASR, hosted JWT, rights or Feature4 renderer acceptance.
- The stages overlap; do not add `tested` to `source-complete`. Coordinator proposal included for shared 159-task reporter and Feature5 22-task ledger. This Feature7 worker has **not** edited coordinator task manager, main or canonical docs. Pending full coordinator review/merge + fresh main CI.
