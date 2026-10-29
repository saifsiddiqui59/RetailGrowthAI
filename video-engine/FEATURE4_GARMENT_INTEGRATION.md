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
