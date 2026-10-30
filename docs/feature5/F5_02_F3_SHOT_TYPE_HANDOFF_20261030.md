# Feature #5 F5-02 — Feature2 shot-type safety handoff (2026-10-30)

**Status: SOURCE PATCH / PR REVIEW ONLY; not integrated DONE.**

This isolated, GPU-OFF source change strengthens the existing Feature3 consumer packet adapter for Feature2 editorial shots. The previous code accepted `False` or `0.0` as the first `start_second` because Python equality treats them as zero, and an unhashable `camera` could escape as a `TypeError` rather than the declared `WanCompatibilityError` denial. The adapter now requires exact `int` offsets and exact `str` cameras before membership validation. Existing versioned packet fields and approved camera choices are unchanged.

Evidence: `feature5_motion/cross_feature_packet_gate.py` and `tests/ai/test_feature5_f2_f3_shot_type_boundary.py` on this branch. Tests use only synthetic Feature3/F2 contract fixtures, not customer images, signed Auth, actual F2 Node stdout, Wan inference or commercial approval. Review the exact branch-head CI before integration.

**Original task:** `F5-02` remains IN PROGRESS. Actual 15/30/60-second Node stdout from Feature2 PR #551, cross-branch contract integration, coordinator acceptance and fresh four-job postmerge main CI are still required. Dependency owner: Feature2/Coordinator; required output: merged original MIT Creative Director exporter and versioned source receipts; acceptance: genuine original stdout for all three durations with negative tamper tests and no provider grant.

No GPU, Azure model calls, hosted DB writes, PROD, WineShopPOS or paid infrastructure used. Only coordinator may merge and update `coordination/task_progress.json` or canonical shared docs. This handoff proposes no DONE event.
