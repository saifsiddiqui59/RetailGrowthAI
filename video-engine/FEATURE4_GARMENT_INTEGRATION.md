# Feature4 garment reference integration — F4-40 (2026-10-28)

Owner-directed internet-sourced *test* inputs, no paid GPU.

- **Feature3 image proxy:** Pexels Ron Lach boutique rack images #8306370 and #8387134; individual official source pages and SHA256 are included in each run's local provenance. These are independent garment PHOTOS, NOT retailer inventory, tenant-approved private images, generated fashion models or virtual try-on.
- **Feature5 motion proxy:** Pexels clips #8151871, #8249911 and #7626927 reused from the verified 15s edit; real people, NOT AI motion and NOT wearing sourced garments.
- **Feature2 proxy:** explicit editorial test copy and locally generated original 30-second music, NOT AI-generated narration, automatic trend discovery or rights-cleared external viral songs.
- **Feature7 editing proxy:** basic 7-scene Full-HD 30s cut sequence on a deterministic 1-second beat grid, not advanced OpenReel visual acceptance.

Source pages:
https://www.pexels.com/photo/clothes-hanged-on-clothes-hanger-inside-a-boutique-8306370/
https://www.pexels.com/photo/hanging-clothes-in-a-clothes-rack-inside-a-boutique-8387134/
https://www.pexels.com/license/

To compile: python3 video-engine/feature4_garment_integration.py --download --project /tmp/feature4-30s --provenance /tmp/feature4-30s-provenance.json
Render: node video-engine/hyperframes/render.mjs /tmp/feature4-30s /tmp/feature4-30s.mp4
All downloaded sources are temporary; source URLs are allowlisted; image and video media receive signature/mime/FFprobe or trusted image checks, size bounds, and SHA-256 evidence. Never paste stock into tenant-private production or commit downloaded media.

Pexels forbids implied model endorsements and has restrictions on AI model training/evaluation and dataset compilation. This usage is only testing the deterministic editor/transcode, not evaluating/fine-tuning generative models. Explicit endcard: STOCK GARMENT CONCEPT - NOT A RETAILER AD. Do not assert a stock model wears a stock garment.

Integration requests to other feature leads: #3 supply approved per-shop actual garment ID/asset with review/version and garment fidelity; #5 supply approved ready video ID and actual inference lineage; #2 supply reviewed timed script, music ID + third-party commercial rights, actual speech and timecodes; #7 supply authorized edit timeline and sound transitions. Current proxies do not fulfill those gates. The existing trusted v2 handoff remains disabled pending coordinator DB/JWT/RLS, transactional billing and Azure #249 HTTP reliability. 30s render stays showcase_eligible=false and commercial_release_eligible=false until owner reviews exact video. No migration, paid deployment, WineShopPOS or coordinator-owned docs modified.


## F4-42 — Real waveform-derived stock edit sync (2026-10-29)
The prior 30s sample's scene starts were declared on a synthetic list(range(30)) grid;
this was **not detected beat-sync**. F4-42 reuses existing bounded
`video-engine/beat_grid.py`: it writes an original deterministic 30s PCM
music bed with audible per-second rhythmic transients, then **measures actual
onset timestamps from that WAV**, and snaps the seven already-approved scene
cuts to closest detected beats, rejecting missing/non-monotonic/out-of-window
onsets. Full duration remains exactly 30s; no borrowed music or third-party
song source. The actual source waveform, detected beat-grid and scene starts
are recorded in the F4-40 provenance report and verified by PR media tests.

The same pure `snap_scene_cuts` helper accepts **separately authorized** local
music WAV and reviewed F2 scene text for future real music ingestion, but does
not independently grant licenses, discover trends or alter approval/copy.
Actual Feature2 song/media selection and rights review still required.
The private preview exporter also uses an atomic exclusive hard link on
completion to prevent a concurrent worker from overwriting an existing output
at the final rename; a negative race test covers this. No consumer routes,
JWT/RLS, cloud, GPU or WineShopPOS changes. An encoded MP4 is still stock QA,
not real retailer garment/model acceptance.


## F4-45–46 — Independent 60s storyboard and subtitles

F4-45 extends the existing 30s Pexels stock QA composer with an explicit
`--seconds 60` mode. This accepts only 30 or 60, uses **the same actual three
Pexels footage clips and two garment photo references**, creates a 12-scene
60-second 1080×1920/24fps composition, and measures original-percussion WAV
beat onsets with the existing detector before snapping cuts. The resulting
stock references are deliberately repeated; `reused_stock_video_clips=true`
is recorded in provenance. This does **not** assert new/inferred human model
motion, Feature3 garment fidelity, real model try-on or a professional-quality
retailer ad. 60s compiler unit tests run without internet with synthetic test
inputs, and the same source media rights are checked at the compiler. Rendering
a real 60s 1080p MP4 remains an explicit **opt-in CPU acceptance job** owing to
cost/time; a compiled plan is not mislabeled a rendered Full-HD sample.

F4-46 adds `feature4_subtitles.py`: deterministic private SRT and WebVTT
export of *already approved* millisecond-precise Feature2 caption cues.
Strict cue validation refuses overlaps, unescaped subtitle control text,
out-of-bounds and unreviewed/malformed timecodes. Pair writing is exclusive
(`O_EXCL`, mode 0600), rolls back if the second file cannot be created,
never overwrites an existing or symlink target and returns SHA-256 evidence.
This is **not** transcription, semantic speech alignment, an API route, public
hosting, a signed download or third-party caption rights approval. Tenant
authorization, transcript freeze, actual voiceover identity, sidecar private
registration, expiring signed URLs and end-user access are coordinator-owned.

These independent features require no feature3/5 GPU input or public API,
no cloud change, no shared schema, no WineShopPOS changes. They stay within
draft Feature4 PR #322 pending exact-head CI and an actual minute-long
render/human acceptance.


## F4-48 — Separate actual 60s Full-HD acceptance run
`bash video-engine/feature4_stock_minute_acceptance.sh /absolute/new-private-output-directory`
runs the same stock rights-checked acquisition, 12-scene 60s compiler,
1080×1920/24fps HyperFrames renderer, actual decoded actor-motion QA,
lossless video packet-preserving AAC loudness mastering, and 540×960
faststart MP4 preview exporter. It refuses existing output directories,
uses an output with mode 0700, and logs exact source/preview hashes.
This is **separate from the normal 15-minute PR media CI** to avoid
invalidating unrelated tests by resource exhaustion. It requires real
Node22, Chromium and Pexels connectivity; no GPU or cloud credentials.
The unit test only verifies Bash syntax and safe invalid-input behavior;
the script MUST be executed on a configured CPU runner before making a
'full-minute Full-HD render passed' claim. Stock clips repeat and are
not AI motion or actual retailer garments; the owner visual gate remains.


### F4-49 — two additional independently sourced stock clothing photos (60s only)
Pexels [Maria Orlova boutique rack #4947543](https://www.pexels.com/photo/collection-of-female-clothes-on-rack-in-boutique-4947543/)
and [Rachel Claire garment display #4857762](https://www.pexels.com/photo/stylish-clothes-hanging-on-rack-in-fashion-boutique-4857762/)
are separately attributed to their actual creators. The 60-second editorial
test now has **four distinct physical garment-reference photos** + three
verified real stock model clips. As before there is NO on-model garment
matching/retailer inventory claim, model endorsement or AI-generated motion.
These two additional media files are fetched from the fixed Pexels
`images.pexels.com` allowlist ONLY for `--seconds 60`; the passing 30s
Pexels fixture and its provenance are unchanged. In every minute run, the
compiler copies source SHA-256, creator and original rights URL into the
temporary private provenance and does not install product datasets. Offline
synthetic media tests enforce seven distinct sources and twelve 60s scenes.
The actual separate 60s runner must still execute and be visually reviewed.


### F4-50 — Actual real-stock editorial subtitle artifact integration
The existing PR-only `ci.sh` real 30-second Pexels output now writes
`feature4-stock-30s-editorial-titles.srt` and
`feature4-stock-30s-editorial-titles.vtt` using F4-46's real private
caption pair exporter. The 7 captions come from original **test editorial
scene headlines** and exact WAV-measured snapped cut starts in the
30-second source provenance, never inferred spoken syllable timecodes.
An explicit report `caption_kind=EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO`
and `speech_text_alignment_verified_here=false` is preserved.
Output is limited to public Pexels stock QA in short-retention GitHub
CI, not any tenant-private or unreviewed customer audio. Real approved
Feature2 voice clips, spoken transcription accuracy, signed private
caption downloads, hosted SRT/VTT registration and rights remain pending.


## F4-55 — Full-minute exact-file QA chain and decoded review frames
The native 60-second CPU validation command now produces a 12-frame
FFmpeg-decoded review JPEG and SHA-256-linked `feature4_stock_minute_qa_receipt_v1`
across its actual 1080p H264/AAC original, AAC-mastered video,
540p reviewer MP4, five true moving-scene measurements, contact JPEG, and
7 real Pexels source IDs/creators. It explicitly records stock reference
and motion proxies for Features #3/#5; there is NO Feature2 real spoken voice,
licensed chart song, Feature7 full OpenReel acceptance, owner visual
approval, signed URL, tenant cloud JWT or Azure DEV deployment proof.
Repeated-shot warning remains evidence, never a passed visual-quality gate.
The separate 60-second job must actually succeed and its artifacts be
inspected before calling the native minute export validated. Same private
output directory; never upload real retailer/private assets to GitHub.

## F4-56 — Native real-stock 60-second technical proof, 2026-10-29

The owner-directed one-time real full-minute CPU qualification passed on
source `010b0a6f1af1d244692d82649ddcdc2479dc408f`:
[branch run #40836967931](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40836967931)
and [PR run #40836973617](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40836973617)
each **4/4 GREEN**. The PR media job ran 467 tests, rendered an
ACTUAL native 60.000s 1080×1920/24fps H264/AAC Pexels-stock
HyperFrames Reel (42,396,491 bytes), verified five human-stock-motion
luma changes **9.74, 34.08, 6.60, 34.07, 10.24** at threshold 5,
mastered the AAC bed from mean -28.3 to -18.0 dB while preserving
H264 video packets, and emitted a 60.015s 540×960 H264/AAC
mobile review MP4 (3,187,684 bytes).
[Exact-source GitHub proof artifact #12881721743](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40836973617/artifacts/12881721743).

**QUALITY NOT ACCEPTED:** owner-facing decoded 12-frame review shows
obvious repeated fashion model and clothing-rack footage. Garment
reference photographs are NOT the outfits seen on those stock models.
AI-generated model motion, retailer product fidelity, real speech,
approved soundtrack licensing, Azure DEV integration and owner
commercial signoff remain **NOT VERIFIED**. No stock editorial/test
output may be published as a retailer ad. GPU and WineShopPOS untouched.

The one-time PR 60s test marker is removed, and default per-PR/branch
15s+30s CI is restored without disabling preexisting tests. The
`feature4_stock_minute_acceptance.sh` standalone full-minute acceptance
command remains for a dedicated qualified CPU run. F4-55 adds new
SHA-linked 60s QA receipt and actual review sheet to that command;
its positive end-to-end receipt requires a separate execution of the
updated script, not inferred from the earlier successful 60s MP4.


## F4-57 — reviewed SRT burn-in and immutable export inputs (2026-10-29)

- `feature4_subtitle_burnin.py` encodes the **actual** Feature2-reviewed, millisecond-timed SRT track onto a *new* private H.264/AAC reviewer MP4 via FFmpeg/libass, preserving original video/audio media and refusing unreviewed caption changes. The job's SRT path is intentionally restricted against FFmpeg filter-graph option injection; only a fresh file in a restrictive private local worker directory is accepted. It never synthesizes spoken narration or claims semantic alignment, user authorization, commercial rights, publishing, or a signed link. The real encoded test uses original silent-background test video plus an independent synthetic sine-wave AAC track; decoded pixels must appear during the reviewed cue window and disappear outside it. **Not a voice recognition test.**
- Existing `feature4_private_preview.py` and `feature4_audio_master.py` now pin source SHA-256 **before** FFmpeg and reject a changed private source before publishing the final reviewer or mastered artifact. New negative tests mutate the original source during real FFmpeg subprocess execution and require no output/partial file and no success receipt. This reduces stale-lease/provenance risk but does not replace current worker rights/lease checks.
- Source commits: `e84de046`, `cf944700`, `fd52db17`, `57a0d2db`, `ca2b795e`, `8a71094b`. **New exact-head push and PR CI must pass before marking source VERIFIED**. No Azure/DB/PROD/WineShopPOS changes or paid GPU.
- Coordinator integration gate: PR #322 on source head `88eeb1e2` had passing [push 4/4 #40839254492](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40839254492), while the [PR merged-base #40839260496](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40839260496) failed four **shared infrastructure** release-preflight Python tests because `scripts/deploy/package.py` enforces a 120-member ZIP ceiling. Feature4 does not own `scripts/deploy/**`; the coordinator must reconcile the true accepted ZIP source set without weakening count/duplicate or rollback validation. PR conversation handoff posted.
- **Still open:** no verified real Feature2 narrator speech/word alignment, final approved garment+model rights from Feature3, actual Feature5 on-brand walking motion, full Feature7 advanced edit parity, Azure #249 signed-host reliability and production human visual QA. Stock Pexels footage is a *technical editorial example*, not the specific retailer product on its model. Previously real 60s sample and contact sheet remain [PR Actions #40836973617 artifact #12881721743](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40836973617/artifacts/12881721743); this new subtitle code has not been retroactively applied to that asset.


## F4-58 — 60-second stock run produces independent editorial subtitle assets (2026-10-29)

- After the same real Pexels 60s project is beat-snapped and assembled, the source-only `feature4_garment_integration.py` provenance now records exactly twelve scene-matched, <=5.5s *editorial test title* cues. `tests/media/test_feature4_garment_integration.py` validates that SRT/VTT timing and starts match the actual generated sequence, not a hypothetical fixed 5-second grid.
- Updated existing standalone `video-engine/feature4_stock_minute_acceptance.sh` exports private SRT/VTT sidecars, then uses the new FFmpeg/libass burn-in to produce `feature4-stock-minute-captioned-review.mp4` (540x960) and a private SHA-linked proof next to the existing Full-HD original/master/preview/contact-review chain. The captioned proxy is a **new derivative**; original H.264 master and its previous checksum remain unchanged.
- This is not real Feature2 spoken narration, ASR, word-level timing or lyric/music licensing. The previously exported 60s artifact #12881721743 does **not** include these new sidecars. Run the revised command separately and inspect exact output/CI before claiming a tested captioned full minute. No public URL, paid provider, real retailer product identity or commercial rights are created.
- New source commits: `8aad56ce`, `d3fc6234`, `0fc8981b`, `b8bdf3cf`. Coordinator owns shared Azure packaging failures reported on PR #322. Keep PR draft, GPU OFF, WineShopPOS/PROD unchanged.


## F4-60 — Final native-minute QA requires captioned source lineage (2026-10-29)

- The existing 60s `feature4_stock_minute_acceptance.sh` now passes its newly emitted 540p captioned MP4, approved editorial SRT/VTT, and libass burn-in proof into the **same final** `feature4_minute_quality_receipt.py` verification used for original Full-HD, AAC master, proxy, moving stock scenes and contact sheet. All four captioned inputs must be present together; a partial set is rejected before any media read. Legacy technical receipts without captions explicitly say `captioned_editorial_review.status=NOT_RUN` and cannot be mistaken for caption acceptance.
- Validation independently SHA-links the bytes of captioned MP4 and sidecars, the immutable preview source, all 12 generated beat-snapped cue start times and exact reviewed cue text, H.264/AAC 540x960 duration, and **false** commercial/voice/tenant/public-URL approvals. New `tests/media/test_feature4_captioned_minute_receipt.py` includes tampering, stale source, changed captions/timing, fake approval and symlink denials. This proves technical provenance, not the semantic truth of a spoken transcript or the retailer's garment identity.
- Commits `5486bc13`, `f7310057`, `21e97966`, `eb6f4fa4`; exact-head CI must be checked. Existing real-stock captioned 60s **local** sample is preserved as a separate verified H.264/AAC file and SHA-linked QA JSON; it is NOT claimed to have been rendered via the new repository full-minute runner until that command is independently executed. Current known PR merged-base ZIP packaging failure still belongs to coordinator; maintain no test bypass or PROD/WineShopPOS/GPU changes.


## F4-61 — encoded stock scene visibility gate (2026-10-29)

- New `feature4_scene_visibility.py` consumes the existing immutable 60s rendered-scene windows (now exported in stock provenance). It decodes **actual H.264 MP4 frames** through FFmpeg twice inside each scene (30% and 70% of its span), measures grayscale mean and near-black pixel fraction, and rejects a scene when **both** interior samples are effectively blank. This distinguishes sustained missing content from brief transition fades. Strict negative fixtures use an actual 15s H.264/AAC file with a black opening scene; separate real red/blue/green decoded source passes.
- The full 60s CPU stock runner now invokes this before sound mastering/private caption derivatives, then links the signed-off-**false** 12-scene visibility JSON to the final technical evidence receipt, including immutable original SHA, twelve exact start/duration windows, finite sample timing/statistics and `unexpected_overlay_absence_verified=false`. New `tests/media/test_feature4_scene_visibility.py` and `tests/media/test_feature4_scene_visibility_receipt.py` exercise full encoded positive/negative media and forged-data rejection.
- **Evidence limit:** sparse samples cannot rule out subscene flicker, subtitle mistakes, unnatural faces, disputed rights or wrong garments. Previously downloaded real Pexels 60s master passed a separate local sampled luma inspection, but the revised repository full-minute runner and integrated receipt require their own exact-code CPU execution. Stock model/product fidelity and human editorial approval remain failed/unverified.
- Source commits `47907eba`, `ccd94f13`, `44e85cf7`, `896a7e03`, `393ce974`, `36d68a2a`, `febd4e2f`, `4ecf9bb0`; exact-head CI checks mandatory. PR #322 remains draft, branch-only; shared GitHub PR packaging count >120 and Azure issue #249 are independent coordinator/runtime gates. GPU paid services OFF; WineShopPOS untouched.
