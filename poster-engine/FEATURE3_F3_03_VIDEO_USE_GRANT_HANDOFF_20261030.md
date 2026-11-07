# Feature #3 F3-03 / F3-13 — canonical model video-use grants

**Status:** SOURCE PROPOSED; not integrated DONE. **Date:** 2026-10-30.

## Finding and scoped fix

The existing `fashion_reference_v1._model_approval` used Python membership against an untyped `approved_uses` value. A string such as `"video_reference"` or mapping with that key could satisfy the check without being a genuine PostgreSQL text[] approval grant. Require an explicit nonempty 1–3 element list, exact allowed strings, unique entries and `video_reference` membership before any private model handoff. Preserve the existing rights, model, original-byte and GPU-OFF checks.

Added offline Pillow-backed negative tests for strings, maps, tuples, sets, empty/null, duplicate/unknown/non-string values and overlong arrays, plus legitimate explicit lists. Test media and model approvals are **synthetic fixtures**, not customer-licensed or commercial rights evidence. No model inference, GPU, paid API, hosted SQL, PROD, or WineShopPOS changes.

## Review and completion gates

- Original tasks: F3-03 (trusted source rights/byte verifier) and F3-13 (rights regression).
- Source files: `poster-engine/fashion_reference_v1.py`, `tests/media/test_feature3_fashion_reference.py`.
- Test target: `python -m unittest discover -s tests/media -p test_feature3_fashion_reference.py`; CI: all four required exact-head PR checks, followed by coordinator-approved merge and fresh main 4/4.
- Local checkout test not run because repository network/DNS unavailable; **do not claim tests passed** until CI evidence is inspected.
- Blockers: **F3-LICENSED-MEDIA**, Feature3 + independent rights reviewer, requires actual customer-owned model/garment, current likeness/commercial approval and signed grants; acceptance is human-reviewed immutable original provenance. **#471/#325**, Feature3/coordinator, requires mounted authenticated private output/rights route and signed multi-tenant DEV negative tests. **#249**, Azure lead, requires stable 503-free signed DEV gateway. These are external acceptance gates, not reasons to bypass source regression.
- The coordinator alone merges or updates `coordination/task_progress.json`, `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md` and `docs/WORK_LOG.md`. No package is newly integrated DONE from this branch.

## Coordinator task-status proposal

`F3-03` and `F3-13`: retain **IN PROGRESS / source partial** until PR review, exact-head CI, integration, fresh main CI and hosted rights acceptance. Do not add a `DONE` event. `F3-17` remains BLOCKED on F3-LICENSED-MEDIA.
