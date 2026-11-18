# Feature4 F4-04 original #745/#773 trace — 2026-11-17

- Original #745 HEAD `bd9088ebe8c401441e0a27e66f85e648ed8d24d7`: 3/17-second intra-clip moving-source encoded probes and frozen negative cases.
- Original #773 HEAD `31dd9d72e8b059eaa92005a596cad7aa7acdac6c`: 5/13/15/21-second near-cut decoded scene-family comparisons, rejecting early/missing/delayed segments.
- Both distinct QA requirements and regression tests have been ported to surviving #779 F4-04 split/reorder path. Duplicate-operation remains independently 4-frame and unchanged. Source SHA is verified **after all** the extra decoded frames, and the original stricter exact grayscale length/type test from #723 remains active.
- The positive proof reports separate motion/boundary metrics and explicitly `commercial_release_eligible=false`. No hosted video/human product signoff/actual frame-exact trim proof. Original task F4-04 remains IN PROGRESS, not main/hosted DONE. Full exact-head CI / video integration with current parent #322 pending. No paid GPU/Azure/PROD/WineShopPOS changes.

## Original #745 tracker notes
> ## 2026-10-30 — F4-04 frozen-clip regression (source-only, awaiting CI)
> - Dedicated source branch `feat/feature4-encoded-edit-motion-qa-20261030` adds two actual FFmpeg decoded interior video samples at 3s and 17s to the existing 2/7/16/24s encoded parity gate. The QA now fails closed if either supposed moving clip is frozen, even when four different scene-family images could otherwise pass. Adds negative unit tests for first/second/both frozen clips and explicit technical-only deltas in the SHA-linked receipt.
> - No new render, network fetch, GPU, model inference, cloud deployment or sample publication is required. Existing 30s media CI already exercises this validator. Exact-head CI and review remain necessary; do **not** mark integrated DONE. Coordinator owns main merge, shared task-status events and postmerge 4/4 checks. Separate issue #650 Python ZIP member guard remains coordinator-owned; do not bypass it.

## Original #773 tracker notes
> ## 2026-10-30 — F4-04 encoded near-cut parity (separate reviewed staging branch)
> - The existing 30s/540p FFmpeg-decoded edited output proof now samples 5, 13, 15 and 21 seconds in addition to 2, 7, 16 and 24 seconds. It rejects late product-photo entry, early photo exit, late trimmed-video entry and late offer entry, using conservative relative luma scene-family checks. It still **does not** establish exact trim frame, fade duration, product identity or commercial visual approval.
> - Regression tests add four boundary-mutation cases and preserve source SHA, symlink, replay, scene-order, duration and immutable-media negatives. The existing synthetic illustrated fixture remains OWNER_REJECTED; no new user-facing sample was made.
