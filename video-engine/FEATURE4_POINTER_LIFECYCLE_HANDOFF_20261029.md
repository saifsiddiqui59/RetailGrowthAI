# Feature4 F4-10 timeline pointer lifecycle handoff — 2026-10-29

**Status:** IN PROGRESS, not integrated DONE. Branch: `feat/feature4-drag-tenant-fence-20261029` (separate from F4-04, F4-13/F4-15, F4-14 branches, all based on existing #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`).

## Exact source change

The existing modified MIT Timeline Studio caption-boundary resize registered a global pointer-up callback that could outlive the selected shop, approved-direction lock, or original draft. We now cancel an outstanding resize on draft/tenant/approval updates and unmount; require the original primary pointer ID and left button; remove listeners on pointercancel and completion; reject any completion if the live draft/approval differs from the pointer-down snapshot. This stops stale client edits and overlapping listeners, without claiming backend authorization: the trusted compiler still controls tenant/rights.

Actual React/Playwright fixture asserts no `onChange` after a synthetic tenant switch, an approval lock introduced during drag, or pointercancel then late release. Existing legal split/resize logic and no-freeform-FX contract are unchanged. Fixture is mocked, no hosted sign-in, actual customer media or real encoded-frame equivalence.

## Verification / release

Run existing Playwright timeline suite (and full four-job CI at batch boundary); coordinator reviews/merges to latest main with fresh postmerge 4/4 before counting any accepted task. F4-10 requires additional manual touch, accessibility and signed DEV acceptance and therefore remains IN PROGRESS after this source hardening.

No paid GPU/AI, PROD, hosted migrations, WineShopPOS or user-facing media.
