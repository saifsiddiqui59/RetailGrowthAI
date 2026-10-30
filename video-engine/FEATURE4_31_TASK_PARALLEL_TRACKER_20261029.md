# Feature #4 — 31-work-item concurrent execution tracker (29 October 2026)

PR #322 (DRAFT). Feature4 owner: `feat/feature4-professional-video-studio`. Review against CURRENT HEAD / merged-base CI; no cross-branch direct writes, paid GPU/cloud/PROD, WineShopPOS edits or unreviewed customer media. This is an **honest backlog**, not 31 completed tasks.

## Independent Feature #4 — work may proceed concurrently within owned paths

| # | P | Required deliverable | Current source/evidence | Remaining gate |
|---|---|---|---|---|
| 1 | P0 | Standalone revised native 60s render + caption/visibility/endcard | Runner now calls mandatory v2 visibility and encoded 55s endcard QA, plus FFmpeg subtitles | **NEW native 60s exact-head render still needed** |
| 2 | P0 | Hash-linked final 60s quality receipt | Source now FAILS CLOSED if any caption, v2 visibility or real encoded endcard proof missing; negative tests added | Full updated media+SHA+report chain not rerun |
| 3 | P0 | 15/30/60 actual export regression matrix | Existing 15/30 CI & separate 60s stock artifact | One unified exact-code acceptance record |
| 4 | P0 | Encoded editor action parity after split/reorder/duplicate | Trusted JS/Python compiler tests; synthetic edit MP4 | Encoded visual tests for every supported edit |
| 5 | P0 | Renderer-supported transitions/fades/effects | Existing reviewed HyperFrames subset | Remaining effect/render parity and UI |
| 6 | P0 | Multi-track independent audio levels | Disabled unsupported controls in UI | Implement only matching actual renderer semantics |
| 7 | P0 | Actual audio fades/ducking and final QA | Private audio mastering, AAC, SHA tests | Spoken audio and more real mix profiles |
| 8 | P0 | Accurate timeline frame scrub/playback | Focusable keyboard video region supports 1/10-frame seek without editing draft, new mobile Playwright | Actual visual decoded-preview parity remains |
| 9 | P1 | Deep OpenReel adopted capabilities | Split/trim/reorder/snap/zoom/undo/repeat implemented | Unsupported advanced controls remain disabled |
| 10 | P1 | Mobile touch/keyboard/a11y/browser | New keyboard jog, approved readonly navigation, keyboard conflict avoidance, Playwright tests | Comprehensive manual accessibility/device usability |
| 11 | P0 | Near-black/repeat/motion/overlay detection | Added encoded 53/57.5/59.3s endcard proof (old rack repeated); mutation/forged receipts denied; F4-62 60 scene samples remain | Actual new Full-HD minute and human quality review pending |
| 12 | P0 | Typography/endcard/caption and shot composition | New distinct 55–60s disclaimer storyboard + encoded endcard QA; actual libass reviewer captions | **New native 60s footage + text legibility and human review pending** |
| 13 | P1 | Private input/license/dependency integrity | SHA-pinned source, npm audit, F4-63 mutation guard | Commercial attribution and transitive notices approval |
| 14 | P1 | CPU/RSS/latency budgets 15/30/60 | Prior CPU 30s benchmarks; local 60s five-probe QA took ~25.44s/136844 KiB max RSS | Real revised runner Azure budget |
| 15 | P1 | Worker retry/cancel/race/cleanup tests | Existing feature-owned source tests | Real v2 worker/RLS and hosted concurrency |

## Parallel cross-feature contracts — send handoffs, do not bypass owners

| # | Owner | Expected input | Status |
|---|---|---|---|
| 16 | F2 | Independently approved creative_direction/script/offer revision | Handoff to draft PR #551 |
| 17 | F2 | Licensed audio and actual voiced word-timed captions | Handoff to draft PR #551; test editorial captions are NOT speech |
| 18 | F3 | Tenant-granted original product/model bytes and identity/license | Synthetic test-byte #630 MERGED; actual approved retailer handoff absent |
| 19 | F5 | Approved encoded garment-matched real motion | Draft PR #465 source; GPU OFF, actual inference unavailable |
| 20 | F7 | Human-reviewed semantic trims/captions/cuts | Draft PR #513; only supported contiguous trims compile |
| 21 | F2/F3/F5/F7/F4 | End-to-end real approved integrated media | Mock/stock technical handoffs pass only, no true retailer Reel signoff |

## Coordinator-owned integration/production gates — cannot self-merge

| # | Owner | Expected action | Current blocker |
|---|---|---|---|
| 22 | Coordinator | Runtime-only deterministic Functions ZIP manifest preserving license, rollback, ELF, member guards | PR merged-base Python tests fail ZIP >120 entries; documented in FEATURE4_AZURE_HANDOFF.md |
| 23 | Coordinator | Rebase/reconcile main, 4/4 PR and postmerge 4/4, merge only after review | PR #322 remains draft |
| 24 | Coordinator | V2 JWT/tenant-approved snapshot & RLS | Feature4 HTTP adapter source-only, not live |
| 25 | Coordinator | Atomic lease/outbox/quota/accounting one-charge | Cannot bypass existing jobs/billing |
| 26 | Coordinator | Expiring same-shop private signed output & revocation | Private preview source-only |
| 27 | Coordinator | Queue retry/poison/cancel/cleanup hosted checks | Offline tests not Azure proof |
| 28 | Coordinator | Node22/Chromium/FFmpeg v2 worker package, lease/memory/cold-start | Local runtime preflight only |
| 29 | Coordinator/#249 | Repair/verify Azure HTTP timeout issue | Independent Azure canary required |
| 30 | Coordinator QA | Signed-in DEV 15/30/60 E2E + negative cross-tenant | Not run; no user/customer media in public CI |
| 31 | Retailer owner + coordinator | Exact finished MP4 license/visual/audio approval, canonical project docs and launch | NO commercial release approval |

## Evidence and immediate next work

- Owned source changes: `3cb13517`, `d1c7021e`, `80b54465`, `52bd614b`, `3bd94dd6`, `b6acbcc3`; F4 docs and shared-owner handoffs.
- Earlier 60s original Pexels source artifact was independently decoded in 60 interior samples (5 per each of 12 provenance-derived scenes); none almost all black, minimum sampled mean luma 34.69. 25.44s wall and 136844 KiB peak Python-process RSS. This is **not** the updated standalone current-head runner and not a commercial acceptance or video quality guarantee.
- PR merge-base Python/uv failure reproduced in logs at `scripts/deploy/package.py:134`; do not increase member cap or disable tests to make PR green.
- F2/F5/F7 PRs #551/#465/#513 and F3 merged PR #630 received direct source/rights/approval handoffs.
- Latest branch/PR CI runs require observation at the actual terminal commit; logs, not assumptions, determine status. Coordinator alone updates `docs/{PROJECT_STATE,NEXT_TASK,DECISIONS,WORK_LOG}.md` after integration.


## 2026-10-29 afternoon continued independent sprint — source checkpoints, no false closure

- CI on preceding exact branch head `50e700966f`: push [#40869461422](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40869461422) **4/4 SUCCESS**. Pull-request merged-base [#40869468107](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40869468107) **3/4**, with coordinator-owned Python ZIP >120 member count failure. PR remains draft and unmerged; latest main has advanced since baseline.
- F4-65: final `feature4_minute_quality_receipt.py` cannot issue `NATIVE_60S_TECHNICAL_EVIDENCE_ONLY` if any actual private captioned MP4/SRT/VTT/burn report, v2 scene visibility proof, or 55–60s encoded endcard QA proof is absent. Tests assert incomplete chains are rejected **before** media scanning and retain real garbage-media, oversized source and symlink negatives.
- F4-66: new `feature4_endcard_qa.py` performs actual FFmpeg 53/57.5/59.3s source-frame comparison and binds SHA/timestamps to final accepted receipt. Unit tests physically encode synthetic 60s red/blue and red/red H264/AAC scenes and reject old held shot, wrong 58s start, source mutation, forged approval. Local FFmpeg sanity red/blue change 46.83, internal stability 0.0; archived rack hold at 52.5→57.5 changed only 16.397. **Updated 60s HyperFrames media pipeline not yet rerun; do not claim visual acceptance.**
- F4-67: TimelineStudio video-track keyboard focus and preview-only frame jogging, one or ten frames, including approved direction but never editing assets/rights/copy; Playwright mobile negatives. Source+docs pushed to F4 branch, exact-head CI must be inspected. No WineShopPOS, GPUs, paid APIs, production cloud, coordinator-owned workflows/contracts or shared docs changed.

## 2026-10-29 — MVP-first Batch 1 / 30-second encoded edit parity

- **Implemented, source+local archive evidence:** The existing exact Timeline Studio JS split/reorder `[0,4,14,20]` → trusted Python compiler → 30s 540p HyperFrames **encoded mock** now runs `feature4_edited_export_qa.py` in the same existing media CI job; no second render. It verifies 30s H264/AAC, hashes source before/after four actual FFmpeg decoded scenes (2/7/16/24s), rejects gross swapped/missing shots and identical second video replay, and emits fail-closed technical-only report. Importantly this is a **synthetic owner-rejected technical fixture**, not garment/product visual quality or exact-frame inpoint proof.
- **Actual archived prior 30s edited MP4**, SHA-256 `1c69ede47eac07a2dba118ceca59beca118f337d67e801b7eecc4bbe94b57153`, 30.000s/540x960, passed the same local four-frame decoder/proof: video-pair delta 3.53; photo-pair 19.017; minimum video/photo 21.095. Four focused negative/positive Python tests pass locally, covering forged order, false replay, source mutation, wrong duration, and symlinks.
- **Status against 31 tasks**: progress on **#4**, with the 30s split/reorder encoded mock *technical regression slice* complete locally; duplication encoded pixels and real customer 30s footage remain open, so DO NOT relabel the full #4 (or MVP) as commercially complete. First run exact-head branch 4/4 and merged-base PR CI; shared ZIP issue #22 remains coordinator-owned. This batch touches only Feature4-owned CI harness, source, tests and docs. No GPU, cloud, WineShopPOS or production change.

## 2026-10-29 — F4-04 independent encoded duplication parity batch

- Task **F4-04** remains IN PROGRESS until coordinator-reviewed integration and fresh main 4/4 CI. Stacked branch `feat/feature4-encoded-duplicate-parity-20261029` is isolated from coordinator/shared files and based on Feature4 #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
- Reuses exact pinned Timeline Studio JS `studioDuplicate` via `duplicated_draft()`; trusted Python `compile_approved_storyboard` and the existing HyperFrames real 30s 540p H264/AAC CPU media job now physically encode both split/reorder and **separate 10/5/5/10 duplicate** actions. The real decoder checks two encoded replay positions 11.5s and 16.5s, distinct photo segments and source SHA; tests reject advanced replay, forged photo pairs, unexpected operations and missing proof. No GPU, paid inference, PROD, customer or WineShopPOS media.
- This is a deterministic **OWNER-REJECTED synthetic fixture**, not real retailer footage, commercial quality, or exact original-frame matching. Remain explicit `commercial_release_eligible=false`; source and QA are only complete after final branch/stack PR full four-job CI. Source-implemented is not integrated DONE; Feature4 #322 remains draft until coordinator resolves ZIP packaging and merges.


## 2026-10-30 — Unified branch-green source handoff; source is NOT integrated DONE
Five nonoverlapping technical source drafts have been batched for one final integration CI run: #686 F4-04 encoded duplicate parity (4/4 #40955296326), #690 F4-13/F4-15 staged input mutation guard (4/4 #40955734381), #695 F4-14 immutable CPU benchmark (4/4 #40961371565), #701 F4-10 tenant-safe pointer editing (4/4 #40961280016), and #705 F4-03 exact-head 15/30/60 evidence verifier (4/4 #40966895351). Combined branch `feat/feature4-batched-source-handoff-20261030` is intentionally made as one tree/commit from existing #322 parent. None are coordinator-merged or commercial accepted. F4-03 actual three same-head MP4s, F4-14 all duration CPU budgets and F4-10 manual accessibility still OPEN; #650, #249 and real approved F2/F3/F5/F7 outputs remain external. Original draft PRs become trace evidence only, not five changes to apply twice. No GPU, paid AI, hosted actions, PROD or WineShopPOS.

## 2026-10-30 — F4-11 independent continuous full-video black hold QA (draft #808)
- After consolidated source batch draft #779, F4-11 adds one FFmpeg continuous decode scan of the actual encoded 15/30/60s video, denying near-black holds of at least 0.65s that all five sampled interior frames can miss. The v3 60s SHA-linked source receipt requires this scan and explicitly disclaims shorter flashes, lettering/garment identity/rights and human approval; exact test-only 15s synthetic black-gap regression encodes a real 0.8s hidden hold. PR #808 is **draft, not merged**, dependency unchanged.
- First exact-head media CI #41052416541 caught an over-escaped raw regular expression while all other jobs passed; corrected parser and negative regression test in this follow-up source repair. Main integration/actual updated 60s technical and human acceptance still pending; F4-11 remains IN PROGRESS.


## 2026-10-30 F4-14 three-length CPU evidence aggregator (NEW source, CI pending)

Draft stack on F4-11 #808, based on exact 4/4 head `81023702673f48730d85e4b33fae26936e8b30cd`. The new `feature4_cpu_matrix.py` requires three **real** 15/30/60 original 1080×1920/24fps H264/AAC MP4 files and their corresponding independently measured `benchmark_render.py` receipts. It reuses F4-03's stable hash / actual ffprobe verification, rejects swapped media, wrong duration, forged benchmark SHA/bytes, missing or altered Git checkout claim, false Azure/cloud/commercial flags, non-finite/missing timing/RSS data, path traversal and symlinked JSON. No media render is executed by this aggregator; unit tests use explicit fake probe, not real GPU/quality evidence.

`benchmark_render.py` now embeds a **declared local Git SHA**, not an independently signed Actions attestation. The matrix aggregates source-only 15/30/60 sampled CPU/RSS observations and marks `cloud_budget_accepted=false`, `code_commit_attested_by_ci=false`, `human_visual_approval=false`. It **does not** claim a matrix actually ran: required three same-code real encoded outputs and measured reports do not yet exist together. F4-14 remains IN PROGRESS; later opt-in full 60s CPU run is required, never automatically trigger repeated lengthy GPU/CPU or public samples.

CI and coordinator review/main merge/fresh main 4/4 must be verified before an accepted source task. No Azure Functions/PROD, priced AI, SQL, WineShopPOS.

## 2026-10-30 — F4-05 animation/transition renderer CSS parity repair (draft pending)
- Verified trusted Python writer accepts animations `subtle_zoom/fade/slide/pop/glow` and transitions `fade/slide/cut`. Before this patch, **`anim-fade` and text-only `anim-subtle_zoom` were accepted but had no distinct matched CSS effects**, and `anim-glow` without an offer had no visible glow. Repaired the actual HyperFrames HTML/CSS compiler so all five modes act visibly on the glass layer, including text-only scenes. Client-to-compiler allowlists now import the single trusted renderer vocabulary; unexpected CSS/effects fail closed.
- Added offline tests for every approved enum and exact compiled stylesheet-keyframe selector, and rejects unsupported effect/preset injection. **Source-only parity, NOT actual decoded animation-frame QA**. Exact new-head four-job CI, coordinator-owned main integration and postmerge 4/4 required; F4-05 remains IN PROGRESS pending encoded visual/pixel review and UI/device QA. No paid inference, customer media or GPU.

## 2026-10-30 — F4-06 bounded four-channel audio-gain source contract (draft pending)
- Source-only addition to trusted `rg_video_v2` and internal `creative_reel_v1`: optional `audio_mix` with independently bounded **source video [0.20,1], music [0,1], narration [0.20,1], SFX [0,0.50]** linear channel gains. Values are finite, centi-unit precision, never booleans; unknown fields, missing track assets and unauthorized controls fail closed. No arbitrary gain curves, user HTML, filtergraphs or auto-billing.
- Compiled HyperFrames HTML uses existing `data-volume` semantics on each authorized original source, music, licensed voice and timed SFX track. Music under sound/narration remains capped at 0.12; original fixed gain defaults remain byte-semantically unchanged for old requests. This is a **trusted, reviewer-snapshot-only internal contract**; browser gain sliders remain OFF until coordinator binds approved immutable gain requests/tenant and verifies real AAC export.
- Added compiler/contract regressions for source, music, narration and SFX, ducking cap, invalid/missing/unapproved control negatives. Full four-job branch CI, reviewer approval and fresh main 4/4 required. **F4-06 IN PROGRESS**, not customer audio release or per-clip automation; paid GPU/model, PROD and WineShopPOS untouched.

## 2026-10-30 — F4-07 final audio-master original-source continuity
- Existing private AAC loudnorm-master source checked bytes only by `source.read_bytes()` before/after encode. A same-byte *atomic path/inode replacement* could silently pass while measuring pre-swap audio and publishing post-swap proof. New `feature4_audio_master._stable_source` checks the local source with no-follow regular FD SHA256 and stable dev/inode/size/mtime/lstat **before ffprobe**, after ffprobe, after encode and immediately before no-clobber output. Original bytes and object identity must remain equal; no public output on failure.
- Tests use actual local synthetic H264/AAC mastering and force `os.replace` with byte-identical but different-inode source after FFmpeg mastering. Fail closed with private scratch cleanup; empty/symlinked input negatives remain. The earlier append mutation negative still runs.
- This is source-only **F4-07 IN PROGRESS**: no new audio, no human voice/music rights acceptance, no loudness perceptual guarantee or hosted signed output. Exact new-head 4/4, coordinator main merge and fresh main 4/4 required. GPU/paid model/PROD/WineShopPOS unchanged.

## 2026-10-30 — F4-11 encoded stock endcard proof source identity (draft, unmerged)
- The existing 60s endcard test used a pre/post SHA256 computed by reopening the pathname, which could return **equal hashes for two different source file inodes** after a same-content atomic replacement between real FFmpeg frame samples. That permits pixel observations to refer to an object different from the original approved source even though bytes are equal.
- This new F4-only batch reuses the already-proven F4-11 no-follow local `_stable_source` verification: the same **dev/inode/size/mtime plus streaming SHA256** must survive three decoded endcard probes. Any swapped path raises `EndcardProofError` and **no quality receipt** is returned. Added a real synthetic 60s H264/AAC regression that performs byte-identical `os.replace` after first actual FFmpeg sampled frame, proving this rejection and preserving original bytes. Existing repeated-shots, legacy-endcard and in-place mutations retain their gates.
- **F4-11 remains IN PROGRESS** pending revised full-HD 60s native render, signed source/garment rights, visual/legibility review, and approved integration into main with fresh 4/4 CI. This is only a source integrity improvement; it does not validate actual consumer product or prevent a subsequent malicious local write after the final check. No GPU, paid media service, PROD or WineShopPOS.

## 2026-10-30 F4-12 multilingual spoken caption typography + anti-spoofing
- Source-only `feature4_caption_track.checked_caption_cues` now blocks explicit Unicode bidi overrides/isolates, hidden formatting marks/BOM/soft-hyphen and non-renderable-only cues; it preserves reviewed Arabic and Devanagari shaping (including necessary joiners). Identical server-reviewed wording/timing still drives HTML/SRT/VTT; the compiler never silently rewrites marketing copy.
- `professional.py` chooses a deterministic bounded **per-caption 9:16 font size** for <=45, 46–70 and 71–90 approved characters, with balanced wrapping. Previous long approved captions used the same giant font as short cues and could overflow their portrait caption region. Unit tests compile actual trusted HyperFrames source and verify precise text/time retention and short/long CSS size; SRT/VTT tests verify multilingual preservation and reject Unicode visual spoofing. No OCR, actual Chromium pixel or live voice timing evidence is claimed.
- F4-12 remains **IN PROGRESS** pending genuine rendered caption legibility and approved customer/reviewer full-HD 60s QA. Stack source draft on #835; exact-head four-job CI and coordinator-reviewed merge/fresh main 4/4 mandatory. No paid GPU/model/PROD/WineShopPOS.

## 2026-10-30 F4-08 actual timeline seek linked to authorized preview (new draft)
- Found UI semantic gap: OpenReel `FrameTimecodeInput` / one-frame keyboard jog / scene clip click updated **only the timeline's local playhead**. Parent `VideoStudio` storyboard source preview and signed existing rendered MP4 were not sought to the selected frame. That made timeline frame scrub appear to work without moving actual video.
- `TimelineStudioSurface.onPreviewSeek` now publishes only bounded 24/30fps frame-quantized timeline seconds; `VideoStudio` updates the **currently authenticated/same-shop media preview only**: signed render if existing submission is genuinely SUCCEEDED (never OWNER_REJECTED), else previously verified private source footage at `sourceWindow.start + (playhead - scene.start)` clamped inside the reviewed trim. Metadata-loaded races also seek. No authoring write, storage URL grant or approval inferred. Shop/approval/draft switches clear stale preview time, and old signed video remains hidden after any edit.
- Playwright DOM regression mounts real React Studio with **fake media clock** (no file loaded or cloud action), seeks to 6.5s using OpenReel timecode, clicks scene-2 center to 7.5s, checks actual signed video element currentTime was updated, confirms no extra render calls, then editing hides old signed media. Real full-duration FFmpeg-decoded frame accuracy, source media authenticity and device/latency QA remain unverified; **F4-08 IN PROGRESS**, not accepted DONE. New exact-head four-job CI + coordinator main integration/fresh main 4/4 required; GPU/paid inference/PROD/WineShopPOS off.


## 2026-10-30 — F4-02 60s QA receipt exact-path/inode read fence (new source batch)
- The 60s QA receipt previously reopened approved evidence twice (`_sha(path)` and `read_text(path)`), so provenance could change between what was hashed and the JSON that got parsed. `_sha` also used a path-open with only a prior is_symlink check, not an atomic original inode/path guard. A different file containing identical bytes could replace a source during hashing while the reported SHA remained equal.
- New `_stable_file` opens with O_NOFOLLOW, enforces bounded regular-file size before reading, hashes in bounded chunks, checks byte count and the same dev/inode/mtime/size on descriptor **and final pathname**, and returns optional JSON bytes from that exact same single read. `_record` parses only that locked read, never reopens. All existing 60s media/receipt approval/tenant disclaimers remain unchanged; no direct input/public upload.
- Regression tests simulate exact-byte `os.replace` during `_sha` AND `_record` digest updates, reject symlink, oversize and malformed JSON, retain hash compatibility. Technical *local source acceptance* only, not server-signed immutable storage, customer approval or a full successful 60s production export. **F4-02 IN PROGRESS** until exact-head 4/4 branch CI, reviewed main integration/postmerge CI, and final actual 60s proof. GPU/paid inference/PROD/WineShopPOS remain OFF/untouched.

## 2026-10-30 — F4-10 async shop/render-response UI race fence (draft)
- Source bug: `VideoStudio.submit` awaited the authenticated render callback, then **unconditionally** set `submitted=true`, `error` or `busy=false` even if the user had since switched shops, changed approved Feature2 direction, or edited the draft. Under a rapid shop change, completion of prior Shop A's request could make Shop B's existing signed artifact falsely look like the current submitted Reel; a stale denial could overwrite Shop B's active render state.
- Introduced monotonically increasing local render epoch, synchronous in-flight lock, and live-shop/approval context check. Shop/approval switches and draft edits/retimes/new projects invalidate pending UI callbacks and unlock a fresh editor submit. Only the matching current epoch AND same shop/direction may update submitted/error/busy. Starting a new request hides old signed video. Unmount invalidates callbacks. No request gets cancelled or billed again: backend idempotency, tenant JWT and ledger remain coordinator duties.
- Real mounted React Playwright browser harness simulates two synthetic shops, pending/deferred ACKs, late old-shop success, old-shop error arriving after new-shop request, and same-shop edit while pending. Asserts no stale signed video or error/busy contamination, and current approved draft still submits. Does **not** exercise real Azure JWT or signed URL expiration. F4-10 remains IN PROGRESS pending exact-head full 4/4, coordinator main merge/main 4/4 and manual mobile/security E2E. No GPU, paid AI, PROD or WineShopPOS.

- **F4-10 follow-up:** approval direction transitions must invalidate pending render even if the approved direction is removed and later restored to the original value. Fourth Playwright synthetic React race test exercises revoke→restore→old ACK with no stale signed preview. Branch CI superseded on each source update; use only latest exact SHA, never claim prior queued/green runs for latest branch. Still unmerged IN PROGRESS.
