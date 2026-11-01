# Feature #3 — source-component completion receipts and duplicate-safe scheduling

Effective 2026-11-01. This is a **reviewed-proposal-only** machine-readable progress overlay, not an AI coding executor or permission to change GitHub protections.

## What is marked complete
- The existing central `coordination/task_progress.json` **already marks F3-01 DONE** with `acceptance_scope=source_integrated`, merged PR #813 and verified fresh postmerge main CI #41131088666. Do not append a duplicate F3-01 event.
- `coordination/feature3_source_receipts.json` now records **14 separate, original source PR components as SOURCE_INTEGRATED**, backed by Wave A #811 and Wave B #813, current-main SHA `456b1757d7df2f0cc28a5ef6c8ba203b18380948`, and fresh main 4/4 CI #41178167285. Each receipt ties one of the original F3-xx task IDs to the reviewed closed PR and a precise `exact_blob` or `semantic_review` method. These are *source-component completion* receipts, **not fourteen new fully completed Feature3 tasks**.
- F3-10/F3-13 source candidate #859 remains `TESTED_PR_REVIEW_REQUIRED`, despite four successful PR jobs and targeted frontend tests; it is **not** SOURCE_INTEGRATED yet.
- Total hosted package acceptance remains **0/33**. Do not mark any of the other 32 original F3 task IDs `DONE` for production/hosted acceptance.

## How duplication is prevented
- The existing read-only `scripts/coordination/task_scheduler.py` accepts this reviewed overlay and places already-integrated F3 package components in `existing_source_or_review`, with a clear instruction not to reimplement merged components.
- It does not treat the component as hosted DONE; it preserves original `coordination/feature_tasks.json` snapshot (159 original tasks, unchanged), existing `coordination/task_progress.json` authoritative accepted events, and the separate owner-level release requirements.
- The scheduler remains **advisory only**. Human or authorized executor must examine unimplemented scope and current main/PR evidence before claiming *new* feature work. No automatic executor, session, cost, GPU, cloud SQL or queue action is introduced.
- Python contract tests prove source receipts suppress duplicate advisory assignments and reject forged hosted completion, foreign task IDs, duplicate component PRs and unsupported approval stages.

## Release / handoff gates
Feature #3 still needs independently approved genuine garment/model rights (F3-LICENSED-MEDIA), authenticated mounted private PNG delivery and current-output rights validation (historical #325/#471 handoffs), hosted issue #249 reliability tests, genuine #627 worker spans and signed two-tenant DEV role-denial E2E. Paid FLUX/GPU remains OFF.

The overlay must be independently reviewed before merging because `coordination/**`, `scripts/coordination/**` and `tests/contracts/**` are shared/coordinator-owned. A green branch workflow alone does not authorize self-merge of shared status/scheduler logic.
