# Feature #7 — Uploaded Footage Semantic Editor: source handoff (2026-10-28)

**Owner:** Feature #7. **Branch:** feat/feature7-uploaded-footage-semantics-20261028. **Integration:** proposed, NOT merged into main, NOT a deployed feature. The existing Feature #4 editor, renderer, queue, ledger, JWT/Supabase Auth, media manifests and DB approvals remain authoritative. No new ad script or Creative Director is introduced.

## Source adoption and attribution

Actual AutoBroll code source: https://github.com/andriidrok1/autobroll (main tree pinned at evaluation to 4aef3afb099c866bd2977c184f9912ba57318f77; upstream LICENSE MIT © 2026 Andrii Drok, retained as AUTOBROLL_MIT_LICENSE.txt). Files inspected:
- scripts/trim-silence.mjs (source-relative WhisperX word gaps >600ms, 100/300/80ms pads, >=350ms segments). Adapted into speechRuns, preserving its gap and padding strategy.
- scripts/captions-multiclip.mjs (phrase-aware max-five-word pages, glue words, punctuation, 450ms breaks, orphan merging), adapted into buildCaptions. Captions remain anchored to the original asset and source-relative word offsets.
- scripts/broll-multiclip.mjs (startIdx/endIdx word-to-time anchoring and preference for owned assets), adapted into strictly tenant-granted broll_advisory cues. No stock/Pexels fetch and no automatic licensed content claims.
- src/captions.ts and src/timeline.ts inspected for source-relative and timeline/trim projection. Timeline projection is emitted as review-only timeline_start_ms/timeline_end_ms, without importing the Remotion timeline editor.
- scripts/lib-transcribe.mjs (WhisperX/FFmpeg, cache and transcription handling) evaluated as a *potential* isolated source preprocessing stage. Runtime integration is not complete and is NOT claimed to have performed live AI inference here.
- scripts/arrange-clips.mjs inspected for the original AI retake ordering/pick-best flow; no Gemini call, unreviewed retake removal or promotional script rewriting is adopted.

The implementation lives in video-engine/feature7/autobroll_semantics.mjs and uses standard Node APIs only (no npm dependencies). The original AutoBroll editor UI, renderer, browser storage, Gemini/Pexels credentials, Remotion Player and export code are deliberately excluded.

**License gate:** AutoBroll's MIT license does *not* grant permission to use its Remotion dependency outside Remotion's own license. Official https://www.remotion.dev/docs/license/pricing currently says eligible individuals / organizations of up to 3 people may use its free license; others building automated video tools can require a Company / Automators license (currently advertised $0.01 per render with a $100/month minimum). Eligibility depends on actual operating entity and terms. To preserve minimum cost, **Feature #7 installs and invokes no Remotion, no Pexels, no Gemini, no WhisperX model**, and performs no render. Transitive dependencies of any future upstream adoption must be audited independently.

## Authoritative boundaries

1. A trusted coordinator first authenticates the current user JWT, checks active same-shop OWNER/EDITOR membership, reads RLS-approved source media metadata, checks commercial media rights and original bytes from private Storage, and produces a server-trusted manifest. NEVER pass browser-provided media grants directly to this source module.
2. Upstream transcription/vision processing on a trusted private worker (not implemented in this PR) must bind the exact source-asset bytes hash and transcript provenance. The pure semantic module currently consumes already *verified server* word timings; a string field in an untrusted request is **not an authentication proof**.
3. Each original Feature4 scene must contain an existing authorized retailer-uploaded VIDEO asset. A full scene permutation is not proposed automatically. Output preserves the approved original total 15/30/60s duration, every source scene exactly once, and original audio (explicit mute_source:false). No external URL/path, new asset or ad content may enter the executed edit plan.
4. The public review-only result has version feature7_uploaded_footage_v1; status NEEDS_REVIEW; approved=false; renderable=false; review-only edit scenes with source_scene_index/duration/trim_start/mute_source, source-relative captions, audio/silence and B-roll cue advisories.
5. **Feature4's existing video-engine/feature4_edit_execution.py (draft PR #322)** accepts the exact edit scene fields above BUT requires an independent persistent trusted snapshot with edit_plan:{source_feature:'feature7',approved:true,approval_id,timeline_version:'creative_reel_v1'}; it checks canonical draft_fingerprint, same-tenant campaign/shop, fixed scenes, full duration, allowed transitions and the authoritative Feature4 compiler. This Feature7 module deliberately NEVER returns an approved executable record. Server must recompute the Python canonical hash, store an approval receipt and populate the exact Feature4 envelope only after human review.
6. Feature4's current adapter can execute one contiguous trim per original scene, not arbitrary internal jump-cut split/duplicate scenes. Therefore the source-level pause runs are only suggestions, and the strongest speech-containing contiguous window is the only immediate trim recommendation. Multi-jump-cut expansion, timed caption overlays and actual B-roll inserts remain non-executable advisories until the Feature4 owner agrees a versioned, tenant-checked contract and tests that the existing renderer supports them. Never silently drop these effects while marking "fully edited".

## Integration input example (non-sensitive synthetic fixture)

The function proposeUploadedFootageEdits({shop_id,campaign_id,draft,footage,grants}) accepts:
- Draft: the existing exact original Feature4 creative_reel_v1 draft with shop_id,campaign_id,duration_seconds, scenes[{asset_id,asset_type:'video',source_feature:'retailer',duration,...}].
- Footage entries each have scene_index, asset_id, source_duration_seconds, has_audio, transcription_status:'verified_server', transcript_sha256, words:[{word,startMs,endMs}] in source-relative milliseconds, optional broll_candidates:[{startIdx,endIdx,mode,assetId}].
- Trusted internal grants each have asset_id,shop_id,issued_by:'trusted_server',source:'retailer_upload',rights_status:'APPROVED',active:true,media_type:'video'|'image',has_audio where relevant. These are **not** cryptographic tokens and may never be accepted from a browser or model.

Run an isolated review-only fixture by piping JSON to Node:
node video-engine/feature7/autobroll_semantics.mjs < /path/to/synthetic-fixture.json

There is no user-facing API/route, Supabase migration, tenant persistence, browser integration, AI provider call or cloud deployment.

## Verification / scope

- New offline unittest suite: tests/media/test_feature7_semantic.py (picked up by existing video-engine/ci.sh) tests allowed same-tenant input, silence gaps, word/page timing, approved in-shop B-roll proposal, source-audio preservation, stable draft hint, duplicate/missing/foreign assets, license revocation, transcript spoofing, out-of-range/out-of-order word timestamps, invalid B-roll indexes, invalid scenes/lengths.
- The fixtures are synthetic and **do not** establish real human audio intelligibility, legal rights in customer video, actual WhisperX speech accuracy, neural B-roll recommendations, hosted JWT/storage checks, or an integrated Feature4 editor execution.
- The upstream AutoBroll original application/tests were NOT run here: its separate Remotion/Gemini/WhisperX environment is not installed and it would not constitute a lawful/authorized SaaS renderer.
- All actual uploaded-footage inference is OFF pending coordinator-trusted preprocessing, rights-bound private staging and source hash checks. No WineShopPOS, PROD, Azure billing or Supabase mutation.

## Coordinator / Feature4 next actions

1. Review this draft PR and compare exact current Feature4 PR #322 contract (feature4_edit_execution.py) after any Feature4 source-adoption changes. Only the coordinator can change shared docs/INTERFACES_V1.md or persist/review the trusted approval envelope and user roles.
2. Authorize a no-leak private FFmpeg/WhisperX staging and transcription service with hash-based tenant ownership and bounded CPU/time/memory; evaluate model license and runtime cost before enabling. Connect real transcription to source-relative word timings.
3. Ask Feature4 to accept versioned caption/B-roll/multi-segment instructions or explicitly leave them as suggestions. Keep HyperFrames/FFmpeg as only output engines. Never install Remotion simply to get an AI cut.
4. Run real **approved retailer-owned** source-video/audio fixtures; verify words, spoken audio, selected cuts, subtitles, rights revocation, cross-tenant rejected requests, private preview and Feature4 output quality. Human approve before commercial publishing.
5. Update coordinator-owned docs/PROJECT_STATE.md, docs/NEXT_TASK.md, docs/DECISIONS.md and docs/WORK_LOG.md *after* integration; this feature worker must not edit those shared files in parallel. Record PR head SHA and exact four-job CI, not assumed success.

**Current disposition:** feature-source proposal, not production-capable Feature7 AI. Keep PR draft until real data/model and Feature4 integration gates pass.


## 2026-10-28 parallel source continuation (after PR #513 initial success)

A new independent offline test-data implementation was added on this same Feature7 branch:
- \`media_preflight.mjs\`: strict tenant-approved local staged MP4, SHA256, ftyp, ffprobe codec/duration/size, path and symlink guards. This does NOT register or authorize an actual Supabase video upload and does not accept browser-supplied signed rights.
- \`audio_activity.mjs\`: read-only FFmpeg \`silencedetect\`; structured non-silent regions are **not speech recognition** or VAD. AAC is preserved, not muted, rewritten or billed.
- \`transcript_adapter.mjs\`: actual AutoBroll-style WhisperX JSON word parsing, bounded timecodes, caption projection through trim and source hash binding for a *trusted worker*. No live WhisperX model invocation; a supplied synthetic transcript is a test input.
- \`private_review_pipeline.mjs\`: stitches private media bytes, trusted grant, source-relative transcript and audio-activity evidence into the already existing Feature4-compatible \`NEEDS_REVIEW\` draft, with no self-approval.
- \`semantic_suggestions.mjs\`: pure deterministic similarity ranking of retailer-uploaded retakes plus sparse keyword matches to approved tenant-owned B-roll. Zero cloud/AI calls, no automatic scene deletion or insertion.
- \`tests/media/test_feature7_pipeline.py\`: generates an original 16-second **low-resolution synthetic MP4 with AAC 440Hz tone** via actual FFmpeg and supplies synthetic WhisperX-shaped word timecodes. This is *not a real recorded spoken advertisement*. Executes positive end-to-end pure source preflight and negative forged/foreign/revoked, traversal/symlink, audio/hash and ASR timing paths.
- \`tests/media/test_feature7_suggestions.py\`: tests similarity and owner-approved cutaway guidance, including foreign/revoked stock denial.

Feature4's F4-15 adapter still applies **only one contiguous trim per original scene**. Speech silence-gap runs, retake drop choices, overlays and B-roll suggestions are not yet supported by its renderer. Every output is \`approved:false\`, \`renderable:false\` and human-review-required. Do not treat successful unit tests as actual speech intelligibility, private signed production assets, customer footage, published ad, approved video rights or hosted DEV.

All independent workstreams and blockers are tracked in \`video-engine/feature7/TASKS_20261028.md\`. Check final PR head/4-job GitHub Actions outcome before claiming this continuation is green. The coordinator alone updates the canonical \`docs/**\` state, tasks, decisions and work log after integration.


## 2026-10-28 — Independent P0 continuation: CPU model hook, signed evidence, review receipt, timeline

**Source additions** (PR #513, draft, no shared APIs, deployment or branch merges):
- \`offline_whisperx_cpu.mjs\` invokes a **preinstalled** WhisperX CLI (CPU, int8) on an FFmpeg-extracted private 16kHz WAV from an *already same-shop SHA256/ffprobe-approved MP4*. It demands an absolute trusted executable and locally staged model directory; \`HF_HUB_OFFLINE=1\`/other offline flags, 10-minute cap, private scratch and cleanup. Runtime network egress isolation and preinstalled alignment models are **still mandatory**; environment variables alone do not guarantee network isolation. The GitHub tests use a deterministic **stub executable**, not WhisperX weights. Genuine speech recognition precision, model licensing, multilingual coverage and CPU cost remain unverified.
- \`transcript_evidence.mjs\` binds reviewed \`shop_id\`, \`asset_id\`, \`job_id\`, actual source media SHA256, normalized transcript SHA256, model reference and <=10-minute TTL in a constant-time checked HMAC. The signing key exists only inside a trusted worker. This does not grant user membership or commercial footage rights.
- \`evidence_bound_review.mjs\` recomputes the transcript digest from supplied words, checks that HMAC against the exact video/source/job and rechecks real private source bytes through the existing preflight. The prior \`preparePrivateReview\` is a lower-level **fixture/trusted-caller-only** function; a browser-provided \`verified_server\` string is not admissible production proof.
- \`review_fence.mjs\` accepts candidate scenes only in NEEDS_REVIEW/nonrenderable form, requires an injected server-authorized active OWNER/EDITOR review context, current source rights and revision, and signs a short-lived receipt. A later call rechecks receipt MAC, actor/shop/campaign/revision/source-snapshot hash, candidate hash and canonical F4 draft hash, then emits exactly the \`feature4_edit_execution.py\` \`approved_edits\` fields + \`snapshot.edit_plan\` shape. **It is not a database; coordinator must persist human action and prevent replay transactionally and recheck all media before F4**. No browser-facing approval route is created.
- \`review_timeline.mjs\` projects and validates existing caption pages and B-roll cues against contiguous original scene intervals, live same-shop media metadata, safe caption text and source-audio preservation. It rejects foreign/revoked input, time overflows and HTML; all caption/B-roll inserts explicitly remain **Feature4 unsupported advisory effects**.
- Added \`tests/media/test_feature7_cpu_evidence.py\`, \`test_feature7_review_fence.py\`, \`test_feature7_review_timeline.py\` and additional positive/negative \`test_feature7_pipeline.py\` scenarios. Tests execute actual FFmpeg + MP4 bytes while the ASR process executable itself is a **clearly marked stub**; do not claim real ML inference.

**Real remaining gates:** coordinator-owned authenticated MP4 registration, current RLS source grants, actual offline WhisperX model download/licensing and true CPU speech benchmark, independently human-reviewed audio accuracy, database-backed approval/lease/idempotence, Feature4 caption/B-roll/multicut rendering (without another renderer), exact approved customer footage and hosted DEV signed-in acceptance. Model/GPU inference spend and WineShopPOS unchanged; the original file's AutoBroll MIT attribution remains intact.

**Run verification:** inspect exact-head four-job GitHub CI and negative tests after the last commit. Source branch work alone is not successful deployment or complete Feature #7.


## 2026-10-28 — Independent third continuation: durable local approval CAS + gap-cut previews

Delivered within Feature7 ownership only:
- \`review_journal.py\`: standard-library SQLite **offline transaction fixture**, persisted locally with \`BEGIN IMMEDIATE\`, optimistic revision compare-and-swap, explicit human approval flag, current role/media snapshot fences, 10-minute expiry, one-time claim and revocation. Stores IDs/SHA256s only, not transcripts or customer media; testable across independent SQLite connections. Its context must be injected by a trusted authenticated server, **never** user JSON. It is NOT the shared Supabase approval table, not multi-instance-ready, and not an authorized REST API. The coordinator must own the durable multi-tenant PostgreSQL approval/lease/outbox transaction and reconcile render failures; a local \`CONSUMED\` marker does not deliver exactly-once final production.
- \`gap_cut_advisory.mjs\`: AutoBroll-style word-gap suggestions with explicit source-relative intervals, bounded cut counts, speech-run pads, target-duration diagnostics and intact original audio. These are **review-only**: current Feature4 F4-15 can apply just one trim per source scene, not this sparse jump-cut plan.
- \`private_review_pipeline.mjs\` includes \`silence_jump_cut_advisory\` alongside existing retake/caption/B-roll advice. No new external API or renderer.
- \`tests/media/test_feature7_review_journal.py\` tests real SQLite persistence, stale revision, OWNER/EDITOR checks, negative rights scopes, expiry, change/revoke and concurrent one-time claims. \`tests/media/test_feature7_gap_cuts.py\` tests gap detection and time bounds. These test inputs are **fabricated** and do not prove customer-authenticated media access or actual human approval.

Follow-up for coordinator/Feature4: attach genuine signed-in human action, authoritative grant/revocation and stable media snapshot to a DB transaction, then send exactly one persisted reviewed edit to existing F4-15; extend renderer only in Feature4 if sparse jump cuts/captions/B-roll are accepted. Separate production upload/registration+private playback remain unbuilt. Check the exact-head 4/4 CI status before marking this incremental PR ready.


## 2026-10-28 — Real internet video and added visual-quality development

**Real media fetched by the GitHub media tests, verified on PR #513:**
- Public CC0 fixture repository: \`shotstack/test-media\`, pinned upstream commit \`b790a2b72325feecd189291c52663ed8123b1839\`, files \`captioning/scott-ko.mp4\` and \`captioning/transcript.srt\`. License: repo \`LICENSE\` CC0-1.0, \`captioning/README.md\` attributes Scott Ko. Original video is 25s, 1920x1080 talking head; audio contains real English speech. **Not a retailer video or customer-owned approved production media.** Test-only internally fabricated grants must NEVER be used in a deployed service.
- New \`tests/media/test_feature7_public_cc0.py\` pins the upstream Git blob SHA1 and source byte lengths, downloads directly from \`raw.githubusercontent.com\` using HTTPS only during GitHub Actions (\`CI=true\`) or explicit \`RETAIL_F7_CC0_WEB_TEST=1\`, and deletes all bytes after tests. Limits download size to 34 MiB and verifies exact Git blob ID. FFmpeg converts first 16s to a local H264/AAC test excerpt and confirms original audio and source hash are preserved. SRT words are *uniformly approximated inside human-supplied cue timestamps*: this is NOT WhisperX inference or verified word alignment. This is a useful real-video integration acceptance fixture only.
- Real test calls existing private preflight, FFmpeg audio analysis, AutoBroll-derived semantic review, captions and gap cut advisories; tests wrong-shop, revoked, tampered fixture cases. [GitHub CI at \`ae8b12de\`](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40695721962) **4/4 PASS, 234 media tests**, including real fetched original video and subtitle reference. Later commits require their own exact-commit CI.
- New development \`visual_activity.mjs\`: **real read-only FFmpeg blackdetect + freezedetect** for verified local footage, with bounded process duration and source-coordinate intervals. It explicitly does not auto-delete still talking heads, classify content semantically, or render an edit. \`private_review_pipeline.mjs\` exposes it as optional per-asset \`media_evidence[].visual_activity\` when trusted worker opts into \`include_visual_qa=true\`; default avoids needless compute. \`tests/media/test_feature7_visual_qa.py\` checks real black footage, untouched bytes and interval security. The CC0 internet video integration test additionally enables visual QA and checks its advisory output.

**Remaining actual development (not “only testing”):** live authenticated MP4 retailer upload/registration and private signed playback, reviewed local ASR model weights and real WhisperX word alignment/accuracy, actual reviewer UI and DB-backed approval/lease/outbox, executing captions/B-roll/sparse cuts in Feature4's existing renderer, source-audio QA and hosted two-tenant DEV acceptance. Do not treat source-only passing tests as feature-complete, production-enabled or genuinely approved retailer media. WineShopPOS and shared coordinator-owned files untouched.


### Internet CC0 test-preview extension (source-only, not deployed)
\`tests/media/test_feature7_public_cc0.py\` now also takes the chosen one-scene contiguous trim from the **unapproved review proposal**, transcodes a **test-only** 15-second MP4 using FFmpeg, validates the preserved H264 video/AAC original-speech audio tracks with ffprobe, and confirms the source video bytes remain untouched. The local temporary output is deleted automatically. This is *mechanical media QA* (not approval, not hosted download, not a new Feature4 renderer, not a substitute for human listener/word alignment). Full offline user workflow and P0 backend integrations are still not complete.


## 2026-10-28 — Fourth independent continuation: real reviewer controls and stronger media rights

- Human reviewer controls: `review_actions.mjs` and `reviewer_panel.mjs` + scoped CSS provide an embeddable, keyboard-accessible video review panel, selected-source trim preview, read-only caption/visual QA and explicit approval/rejection *requests*. A genuine Feature4 authenticated workspace integration remains P0; this component never auto-approves or uploads/renders.
- Strict worker rights: `media_rights_evidence.mjs` adds TTL-bound HMAC for shop/asset/job/registered video byte SHA/rights revision; `authoritative_private_review.mjs` requires injected authoritative current private-video rights, verifies exact MP4/ffprobe and signed ASR, then calls existing evidence-bound semantic pipeline. Do not treat a text marker as trusted media rights.
- `private_review_pipeline.mjs` now exposes verified media duration for safe manually adjusted trims. Caller must inject current membership and registry from actual backend, not frontend JSON.
- New independent source tests: `test_feature7_reviewer.py`, `test_feature7_rights.py`, with real synthetic H264/AAC, role/revocation/expiry/foreign/hash/tamper and browser-control review refusal checks. See `REVIEWER_INTEGRATION.md`.
- Source code is NOT a production video upload, signed private download, actual real-model transcription, mounted dashboard review UI, durable RLS human decision or Feature4 overlay renderer. Feature-owner only; coordinator-owned docs/SCHEMA unchanged. Exact-head four-job GitHub Actions proof must be checked and recorded on PR #513 before source-complete claims.
