# Feature #4 F4-02 — 60s receipt render-stage identity fence (2026-10-30)

**Task:** F4-02, hash-linked final 60s quality receipt. **Status:** SOURCE PATCH PROPOSED, NOT INTEGRATED DONE.

## Change
- The minute receipt rejects reuse of one filesystem path or hardlinked inode for original, mastered, preview, or captioned MP4 stages before probing media.
- It rejects byte-identical original/master/preview hashes, and captioned output identical to its uncaptioned preview. A copied file is not proof of mastering, re-encoding, or actual burned captions.
- Offline negative unit regressions cover path alias, hardlink alias, captioned path alias, and no-op hashes.

## Evidence and acceptance
- Source base: Feature #4 draft PR #322 at `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
- Proposed branch: `feat/feature4-minute-receipt-stage-fence-20261030`, stacked on #322.
- Targeted command: `python -m unittest discover -s tests/media -p test_feature4_minute_quality_receipt.py -v`.
- Exact-head four-job PR CI: **pending** until inspected; no test success claimed here.
- F4-02 stays IN PROGRESS until revised real 60s source/master/preview/captioned chain, immutable SHA evidence, actual encoded visibility/endcard/caption QA, coordinator integration, and fresh main 4/4 CI.
- Commercial product/garment, human review, tenant authorization, signed release and genuine Wan inference are **not** established by these tests.
- Related dependencies: F4-EDITOR-SOURCE (Feature4 coordinator merge #322); F3-LICENSED-MEDIA (Feature3 approved rights); F5-REAL-WAN-MOTION (Feature5 GPU/approval); F2-CREATIVE-SOURCE (Feature2 reviewed creative); F7-SEMANTIC-SOURCE (Feature7 reviewed edits). Fixture-level source testing does not require these live outputs.

## Coordinator receipt
Review this branch as a draft PR into `feat/feature4-professional-video-studio`, then integrate in the correct stacked order. Propose F4-02 **IN PROGRESS / source hardened** in `coordination/task_progress.json` after review; do not mark DONE before accepted merge and fresh main four-job CI. Coordinator alone owns canonical docs.
