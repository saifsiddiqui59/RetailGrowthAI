# Feature4 F4-14 15/30/60 CPU evidence matrix — 2026-10-30

**IN PROGRESS.** This is a source-only contract improvement, not completion of F4-14.

The new `video-engine/feature4_cpu_matrix.py` checks exactly three **existing actual private MP4s** and three existing separate HyperFrames CPU receipts generated from the **same declared Git checkout**. It calls F4-03's real ffprobe and immutable original-byte SHA checks, then rejects incorrect source SHA, mismatched receipt sha/length/duration, missing stats, invalid timing/RSS sampling, rights-claim escalation, cloud/GPU or commercial approval flags. Source receipts are bounded, no-follow JSON and report output is fresh/private. Returns an honest local observed envelope with max wall time and sampled RSS; it does not set a spending budget or cloud capacity.

F4-14's original `benchmark_render.py` now includes `source_commit_claim` directly in the local receipt, but that SHA is **not CI-signed provenance**. A technical matrix never becomes an approved cloud memory budget or a commercial video. Three actual 15/30/60 same-head encoded files **and** genuine associated measured reports are still required. Tests use synthetic bytes with a **mocked** ffprobe and explicitly cannot establish actual 15/30/60 encoding, producer rights, or performance budgets.

**Dependency gates:** F4-03 same-head encoded media; F4-01 genuine updated 60s native render; F4-22 coordinator package issue #650; F4-29 Azure HTTP 503 #249; F4-30 hosted DEV E2E. Coordinator reviews/merges after exact-head 4/4 and verifies fresh main 4/4. Do not merge stacked drafts separately or mark F4-14 DONE before scope acceptance.

No GPU, charged models, cloud deployments, SQL, WineShopPOS, user-facing samples or approval bypass.
