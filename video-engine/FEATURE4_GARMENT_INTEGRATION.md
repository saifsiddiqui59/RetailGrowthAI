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
