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
