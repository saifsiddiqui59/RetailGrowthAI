# Original #723 F4-04 proof preservation — 2026-11-17

- Original head: `e71a4e401e6634120f3a4f5e85571b4f807b88f8`. Original change contains fail-closed exact 72x128 grayscale buffer length/type validation plus four negative malformed frame regressions, now ported to this surviving #779 source branch without changing existing split/reorder/duplicate semantics.
- Original #723 worker per-download authorization/lease protection was already recovered in newer CURRENT Feature4 parent #322, and per-download negative tests retained there. Do not restore the older #723 worker over newer staged SHA/inode rights checks.
- Historical original tracker notes preserved verbatim below; original PR/source remains available after any unmerged closure.
- This is source integration, **F4-04/F4-15 IN PROGRESS** not accepted main/hosted DONE; #779 still conflicts with newer #322 and cannot bulk merge. Exact-head 4/4 and safe source reconciliation are required.
- GPU/paid inference/PROD/WineShopPOS untouched.

> ## 2026-10-30 — F4-04 decoded frame integrity, stacked review PR #723
> 
> - Existing draft PR #322 at `e32a8da61a6272666d757b6c51b0ec2576d7602f` was verified as **DRAFT/UNMERGED**. The prior exact-head PR workflow #40937402426 failed; no green merged-base acceptance is claimed. Canonical `coordination/task_progress.json` has zero reviewed DONE events.
> - Feature4-owned stacked [PR #723](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/723) hardens `feature4_edited_export_qa._luma_delta`: strict 72x128 grayscale byte-length and type validation prevents silent `zip` truncation of malformed decoded frames. Added four negative cases (short, long, non-byte and empty frames) in `tests/media/test_feature4_edited_export_qa.py`.
> - **Status F4-04: IN PROGRESS / SOURCE CHANGE PROPOSED, NOT DONE.** No test result is asserted until exact-head CI or a reproducible targeted run finishes. Existing 30s fixture remains an illustrated MOCK technical regression, not commercial product/garment/voice approval. Duplicate-clip encoded parity, actual human visual review and full renderer equivalence remain open.
> - Coordinator task-status proposal (not an authoritative shared event): `{task_id: F4-04, proposed_status: IN_PROGRESS, evidence_pr: 723, source_only: true, accepted_integrated_done: false}`. Coordinator must review and write `coordination/task_progress.json` only after accepted integration and fresh main 4/4 CI.
