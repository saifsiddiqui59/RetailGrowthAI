# Feature #4 F4-15 — verified encoder bytes, original object and upload boundary (2026-10-30)

**IN PROGRESS / Feature4 source-only.** New stacked `feat/feature4-output-integrity-fence-20261030` after #850. Never implies a production MP4 approval.

## Verified code-level defect
The previously trusted FFprobe `output_probe` carried only codec, width/height, FPS, duration and file length. The local worker verified those scalar values, but did **not** compare a SHA256 of the verified encoder output with the exact file later handed to the private media upload adapter. An equal-size post-probe media mutation could therefore be published using a truthful but obsolete profile receipt. Original staged sources also tracked only SHA/length across CPU; identical-byte atomic inode replacement could evade the cross-stage comparison.

## Source repair
- `render_adapter.py` verifies the original no-follow bounded regular MP4 scratch inode+bytes **before and after actual FFprobe**, before/after private copy, and the original final no-clobber hard-linked encoded path. Its private metadata proof now includes computed `sha256` for the actual emitted media; this is not a claim of ownership or commercial licensing.
- `feature4_worker_handoff.py` `_staged_fingerprint` now compares dev/inode/size/mtime **and** SHA across stages. It requires the renderer digest as lowercase 64-character SHA, recomputes the authorized final output's original bytes/inode at the worker boundary, and fences local original-output mutation during `media.upload` before calling coordinator's `complete_feature4_render`.
- An upload may have already staged a private object when local tampering is noticed: that object is an **orphan**, not a completed or signed customer Reel. Coordinator must reconcile or purge it. Stronger source checking never grants rights, cancels jobs, reclaims quota, or prevents external storage objects changing independently.
- Python real CPU H264/AAC synthetic 2s probe checks content hash and same-content new inode divergence; fake-service worker tests assert no completion for missing or forged hash, in-CPU original same-byte swaps and post-read upload mutations including byte-identical `os.replace`. We do not claim a real 60s approved garment render, remote checksum or hosted signed lease evidence.

## Pending acceptance
Exact-head four-job GitHub Actions CI (especially 267+ media tests) then coordinator review/merge in existing Feature4 parent chain, fresh main four-job CI, #650 deterministic Azure package and #249 Azure 503 recovery, and signed DEV operator-owned inputs with rights, full reel audio/visual/cost review. Original F4-15 remains IN PROGRESS until hosted atomic claims/cleanup are tested. No GPU, paid inference, PROD, WineShopPOS, cross-feature merge or user-facing sample.
