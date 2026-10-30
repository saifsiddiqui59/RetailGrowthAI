# F4-09 — Bounded adapted editor history (source-only)

Feature #4 owner branch: `feat/feature4-history-bounds-20261030-run3`, based on draft Feature #4 PR #322 at `e32a8da61a6272666d757b6c51b0ec2576d7602f`.

This narrowly improves the already adopted MIT Timeline Studio undo/redo history without importing unsupported upstream masks, 3D effects, keyframes or cloud renderers. Snapshot history is capped at 50 entries even if a caller supplies NaN, infinity or a huge limit. The existing upstream branching behavior is preserved: any pushed edit, including a same-reference edit, clears redo. A first CI failure exposed the existing test contract; the branch was corrected without weakening that test. Existing caller-side shop-change reset and server-side rights approval remain unchanged.

Targeted regression: `node --test tests/frontend/feature4-history-bounds.test.mjs` from repository root. This uses no media generation, external APIs, GPU or paid services. Four-job PR CI and coordinator acceptance are separate; this is **not** a completed F4-09 product capability or integrated DONE. Other advanced editor controls stay disabled. No hosted Supabase login, owner visual approval or commercial output is asserted.

Only the coordinator may merge into the parent Feature #4 branch and later into `main`; retain F4-09 as IN PROGRESS until the accepted integration and fresh main CI pass.
