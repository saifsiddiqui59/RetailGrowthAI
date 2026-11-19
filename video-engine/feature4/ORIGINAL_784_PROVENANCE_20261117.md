# Feature4 F4-10 #784 original cancelled-drag preservation — 2026-11-17

Original head `55832723c784bc08694ea73d4a9cd6ba72452c65` (stale DRAFT). Source-only guard clears `dragFrom` on `dragend`, rejects unrelated/external drops, invalid old indices and locked approvedDirection, preventing a cancelled clip drag from silently reordering the next render. Original Playwright browser DragEvent regression was ported with the existing newer fixture and guard. Newer bounded playhead seek and pointer-resize tenant fencing were *not* overwritten.

> ## 2026-10-30 — F4-10 cancelled native drag safety (review pending)
> - Dedicated stacked branch `fix/feature4-cancelled-drag-reorder-20261030-run3` against draft PR #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f` proposes clearing clip drag state on `dragend`, rejecting unrelated/external drops, and rejecting synthetic drag start while an approved direction is locked. Previously a cancelled drag left `dragFrom.current` stale and a later drop could unexpectedly reorder the draft.
> - Added Playwright negative regression using actual browser `DragEvent` and render-submission ordering; **tests/CI not yet verified at this checkpoint**. No approval, production media, live deployment, paid GPU or shared coordinator files touched.
> - This is a F4-10 mobile/browser safety subtask, **not** full task completion. Await exact-head CI and coordinator review; retain 0 integrated DONE unless accepted on main with 4/4.

Not main/hosted DONE. Original F4-10 remains IN PROGRESS; #779 must be reconciled into current #322 with exact-head four-job CI, real signed DEV identity and review. GPU/paid/cloud/PROD/WineShopPOS OFF.
