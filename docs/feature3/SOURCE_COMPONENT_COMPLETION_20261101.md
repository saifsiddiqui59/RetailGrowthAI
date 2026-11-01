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

## Original task-status report visibility
- `scripts/coordination/task_status.py` also reads the reviewed Feature3 source overlay and adds `source_components_integrated` (14), `source_components_task_count` (11) and per-original-task `completed_source_prs` to the report. **This is a separate source metric**, never extra `verified_done`, never an accepted hosted package, and never an invented project task ID.
- `tests/contracts/test_task_status.py` exercises a 14-source/11-original-F3-ID report with **zero unreviewed DONE events**, plus negative forged-hosted, foreign ID and duplicate-PR receipts. Current existing F3-01 trusted DONE event stays untouched.
- Revisions require independent shared-coordination review, final-head CI and fresh postmerge main CI; do not self-approve or treat this unmerged PR as live scheduler behavior.

## Additional original F3 work claimed as active source, NOT merged (2026-11-01)
- [PR #861](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/861): F3-07/F3-13 strict one-shot integer prepaid lease and immutable private media SQL commit ACK; final-head [Part 1 CI #41301202397](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41301202397) 4/4 passed, **TESTED_PR_REVIEW_REQUIRED**.
- [PR #862](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/862): F3-02/F3-13 reject transient boolean/float rights revisions at a private worker final-byte read, full mocked rights-regression tests; final-head [Part 1 CI #41301483566](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41301483566) 4/4 passed, **TESTED_PR_REVIEW_REQUIRED**.
- [PR #859](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/859): F3-10/F3-13 local private Blob cleanup, final-head CI #41292509625 passed, also awaiting independent review.
- Machine overlay now marks these THREE **active source PRs**, not source-integrated or hosted DONE. Advisory scheduler prevents assigning an identical original F3 implementation while a checked source PR is open, and status report exposes the active PR IDs alongside the 14 already-integrated code slices. If review rejects a PR, revise the same PR/receipt rather than spawning a duplicate branch.
- Verify latest exact-head CI and independent reviewer before any main merge; postmerge fresh main 4/4 mandatory. Original completed hosted packages remain **0/33**, F3-01 remains the only accepted source-integrated task-level DONE.

## F3-08/F3-13 separate current-asset boundary — tested PR #863
- [PR #863](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/863) (source-only original F3-08/F3-13) independently validates the generated media row's exact asset ID, shop ID, private bucket, GENERATED source and SHA-addressed PNG before AND after authenticated private Storage read. Misbound/public/uploaded rows denied in direct and composed no-URL adapter tests. Final head `1ee6d23a334ca82a18d9f7348ee45cce6eb27916` [Part 1 CI #41303756765](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41303756765) succeeded **4/4**, **TESTED_PR_REVIEW_REQUIRED**.
- Machine receipts now track **4 open and separately source-tested PRs (#859/#861/#862/#863)**, keyed by the original F3 package IDs. They are **NOT** among the already-integrated fourteen source components and do not increase task-level DONE or hosted completion. Advisory scheduler excludes exact duplicate implementation from new slots, and review owner must update this record if an active PR is closed/reworked.
- Retain independent security reviewer, exact-final-head CI, main merge and fresh main 4/4 before changing pending source to integrated; Feature3 hosted **0/33**. No GPU, paid provider, customer sample, PROD, hosted SQL or WineShopPOS.

## F3-12/F3-13 — strict approved model reuse candidate #864 (2026-11-01)
- New independent [PR #864](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/864) verifies **known commercial per-image license, bounded unique approved-use subset and valid CC-BY attribution** before the server model-use callback/private media lookup; invalid catalog rows cannot interrupt valid shop selections. Exact head `7eea1aacb2e09b306dbc29dd5cfb9eb4f830286a`, [Part 1 CI #41304611915](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41304611915) **4/4 PASS**, including direct/library and catalog negative test cases. No real model, licensed image, hosted JWT or GPU exercised.
- The original task-management source ledger now records **14 already-integrated Wave A/B components + 5 unmerged tested active PRs (#859/#861/#862/#863/#864)**. These are distinct source components, **not five newly completed hosted tasks**. The advisory scheduler must not assign duplicate implementation while the existing PR has an owner; independent model rights/security review and current-main/postmerge CI remain mandatory.

## 2026-11-01 — F3-12 existing PR #864 expanded and retested
- Same PR #864 additionally validates signed `Feature3V2Store.list_models`: read actual DB `synthetic_adult`, enforce exact current tenant/scope, approved model status, per-image license, SHA, bounded unique uses and private media boolean receipt. Adds `tests/api/test_feature3_model_catalog_current_rights.py` with forged metadata, invalid adult status, unauthorized media and valid catalog-dedupe regressions. No new task ID or duplicate PR.
- New **exact final PR head** `c2c283b79e50bb1c4c34ca4c871ec8bfb2806f18` [Part 1 CI #41306835412](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41306835412) passed **4/4** (Python/uv, FFmpeg, frontend contracts, isolated Supabase auth/RLS). Earlier CI #41304611915 refers only to the older code head. #864 remains `TESTED_PR_REVIEW_REQUIRED`, not integrated nor hosted complete.

## Feature3 F3-12 original PR #864 final type-guard verification (2026-11-01)
- F3-12/F3-13 same source PR #864 additionally validates malformed/unhashable candidate model license/scope/source kind/pose type with controlled `ModelLibraryDenied` prior to Storage/registration. Final exact PR HEAD `75356855b33d0ab25a07094c8ec85c0fc1fd9761`, [Part 1 CI #41307545461](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41307545461) passed **4/4** (Python/uv, FFmpeg, Frontend, isolated Supabase), superseding prior #864 head and CI IDs. This remains **TESTED_PR_REVIEW_REQUIRED**, not merged or hosted DONE. Independent licensing/API reviewer and fresh postmerge main CI remain gates.

