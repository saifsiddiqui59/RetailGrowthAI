# Feature4 #808/#816 historical source notes — preserved on #779 (2026-11-17)

**ARCHIVE ONLY — does not merge source into main, run a live 60s render, or accept tasks.** Original #808 F4-11 continuous black-hold and #816 F4-14 CPU three-profile evidence are source-in-progress drafts stacked on obsolete parent refs. Their core code/test source is preserved unchanged in surviving OPEN source consolidation PR #779: #808 5/5 code/test/handoff paths identical Git blobs (its tracker differs); #816 4/4 code/test/profile handoff paths identical Git blobs (tracker and CPU benchmark handoff differ). This archive preserves missing historical lines without reverting newer source or claiming quality/commercial acceptance.

### Original #808: `video-engine/FEATURE4_31_TASK_PARALLEL_TRACKER_20261029.md`
- Original head: `81023702673f48730d85e4b33fae26936e8b30cd`
- Original Git blob: `39a9ecf11255579b6a7447238f59ec15e4e2351a`
- Surviving tracker Git blob before archive: `30a6b8b2fb0973cf13bad4766b0133b4069a8549`
- Unretained original lines (3, quoted verbatim):

> ## 2026-10-30 — F4-11 independent continuous full-video black hold QA (draft #808)
> - After consolidated source batch draft #779, F4-11 adds one FFmpeg continuous decode scan of the actual encoded 15/30/60s video, denying near-black holds of at least 0.65s that all five sampled interior frames can miss. The v3 60s SHA-linked source receipt requires this scan and explicitly disclaims shorter flashes, lettering/garment identity/rights and human approval; exact test-only 15s synthetic black-gap regression encodes a real 0.8s hidden hold. PR #808 is **draft, not merged**, dependency unchanged.
> - First exact-head media CI #41052416541 caught an over-escaped raw regular expression while all other jobs passed; corrected parser and negative regression test in this follow-up source repair. Main integration/actual updated 60s technical and human acceptance still pending; F4-11 remains IN PROGRESS.

### Original #816: `video-engine/FEATURE4_31_TASK_PARALLEL_TRACKER_20261029.md`
- Original head: `d01e3c716b4f651809d645684c921c6f0413c343`
- Original Git blob: `c8bfbf92538923e11dfe27174240fdfc230cdaa7`
- Surviving tracker Git blob before archive: `30a6b8b2fb0973cf13bad4766b0133b4069a8549`
- Unretained original lines (7, quoted verbatim):

> ## 2026-10-30 — F4-11 independent continuous full-video black hold QA (draft #808)
> - After consolidated source batch draft #779, F4-11 adds one FFmpeg continuous decode scan of the actual encoded 15/30/60s video, denying near-black holds of at least 0.65s that all five sampled interior frames can miss. The v3 60s SHA-linked source receipt requires this scan and explicitly disclaims shorter flashes, lettering/garment identity/rights and human approval; exact test-only 15s synthetic black-gap regression encodes a real 0.8s hidden hold. PR #808 is **draft, not merged**, dependency unchanged.
> - First exact-head media CI #41052416541 caught an over-escaped raw regular expression while all other jobs passed; corrected parser and negative regression test in this follow-up source repair. Main integration/actual updated 60s technical and human acceptance still pending; F4-11 remains IN PROGRESS.
> ## 2026-10-30 F4-14 three-length CPU evidence aggregator (NEW source, CI pending)
> Draft stack on F4-11 #808, based on exact 4/4 head `81023702673f48730d85e4b33fae26936e8b30cd`. The new `feature4_cpu_matrix.py` requires three **real** 15/30/60 original 1080×1920/24fps H264/AAC MP4 files and their corresponding independently measured `benchmark_render.py` receipts. It reuses F4-03's stable hash / actual ffprobe verification, rejects swapped media, wrong duration, forged benchmark SHA/bytes, missing or altered Git checkout claim, false Azure/cloud/commercial flags, non-finite/missing timing/RSS data, path traversal and symlinked JSON. No media render is executed by this aggregator; unit tests use explicit fake probe, not real GPU/quality evidence.
> `benchmark_render.py` now embeds a **declared local Git SHA**, not an independently signed Actions attestation. The matrix aggregates source-only 15/30/60 sampled CPU/RSS observations and marks `cloud_budget_accepted=false`, `code_commit_attested_by_ci=false`, `human_visual_approval=false`. It **does not** claim a matrix actually ran: required three same-code real encoded outputs and measured reports do not yet exist together. F4-14 remains IN PROGRESS; later opt-in full 60s CPU run is required, never automatically trigger repeated lengthy GPU/CPU or public samples.
> CI and coordinator review/main merge/fresh main 4/4 must be verified before an accepted source task. No Azure Functions/PROD, priced AI, SQL, WineShopPOS.

### Original #816: `video-engine/FEATURE4_CPU_BENCHMARK_HANDOFF_20261029.md`
- Original head: `d01e3c716b4f651809d645684c921c6f0413c343`
- Original Git blob: `c171b0fbd341c6610b165c42fd7007dd1e0c85eb`
- Surviving tracker Git blob before archive: `6e4040b0977b579dce4bd25a8fcc242bad729548`
- Unretained original lines (4, quoted verbatim):

> ## 2026-10-30 F4-14 three-length CPU evidence aggregator (NEW source, CI pending)
> Draft stack on F4-11 #808, based on exact 4/4 head `81023702673f48730d85e4b33fae26936e8b30cd`. The new `feature4_cpu_matrix.py` requires three **real** 15/30/60 original 1080×1920/24fps H264/AAC MP4 files and their corresponding independently measured `benchmark_render.py` receipts. It reuses F4-03's stable hash / actual ffprobe verification, rejects swapped media, wrong duration, forged benchmark SHA/bytes, missing or altered Git checkout claim, false Azure/cloud/commercial flags, non-finite/missing timing/RSS data, path traversal and symlinked JSON. No media render is executed by this aggregator; unit tests use explicit fake probe, not real GPU/quality evidence.
> `benchmark_render.py` now embeds a **declared local Git SHA**, not an independently signed Actions attestation. The matrix aggregates source-only 15/30/60 sampled CPU/RSS observations and marks `cloud_budget_accepted=false`, `code_commit_attested_by_ci=false`, `human_visual_approval=false`. It **does not** claim a matrix actually ran: required three same-code real encoded outputs and measured reports do not yet exist together. F4-14 remains IN PROGRESS; later opt-in full 60s CPU run is required, never automatically trigger repeated lengthy GPU/CPU or public samples.
> CI and coordinator review/main merge/fresh main 4/4 must be verified before an accepted source task. No Azure Functions/PROD, priced AI, SQL, WineShopPOS.

## Next
- Independently test and reconcile #779 into the current F4 parent #322, preserving its newer lease/rights/security implementation and F4-05/11/15 work.
- Do NOT close #808/#816 until original source/negative tests, these preserved notes, review/CI and surviving references are checked; do not mark original F4-11/F4-14 DONE by PR closure.
- Paid AI, GPU, Azure/SQL/PROD and WineShopPOS remain untouched.
