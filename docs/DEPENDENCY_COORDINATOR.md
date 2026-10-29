# RetailGrowthAI — Cross-feature dependency coordinator

## Source of truth

`coordination/dependencies.json` is the shared **machine-readable seed** for cross-feature handoffs, NOT a claim that Feature #2's entire 38-task backlog or Feature #3's 33 work packages have been enumerated. Each node has an immutable ID, owner, feature, kind, acceptance criterion, dependency IDs, level and independently verifiable completion gate.

Handoff levels are deliberately distinct:
- `fixture`: immutable source/test input; **never** proof of approved retailer or AI output.
- `integration`: versioned source merged into the expected branch and contract; still not hosted acceptance.
- `production`: current human rights, actual provider results and other formal approval; no implicit upgrade from fixture.

GitHub merged PRs are checked against actual GitHub PR metadata, not by reading README claims. A `manual` completion gate remains pending until a reviewer adds `approved_by` and `evidence_url` with `approved=true` in a reviewed coordinator PR. Failure to query GitHub fails closed. PR #465 targets a stacked feature branch: merging that PR alone **does not** prove the source reached `main`; the acceptance criterion requires coordinator follow-up.

## Automated workflow

`.github/workflows/retailgrowthai-dependency-coordinator.yml`:
1. On PR change, runs **read-only** DAG and mock-GitHub negative tests.
2. On hourly schedule, manual dispatch or relevant `main` push, resolves live GitHub PR evidence and builds JSON/Markdown reports.
3. **Only on trusted main**, creates up to three GitHub Issues per run for currently READY, task-kind nodes not previously queued. Existing issues are detected by an immutable body marker, including closed ones. The workflow does **not** reopen or overwrite them.
4. Leaves other work pending and records exact prerequisites without stopping ready tasks.

The job uses `contents:read`, `issues:write` for the trusted coordinator job only. No cloud credentials, service secrets, bypassed approvals or agent executor. The scheduler *queues assignments*; it **does not autonomously write code**, call a paid coding model, merge PRs, modify WineShopPOS, run GPU, change DEV/PROD or consume Azure queues. A human or separately configured approved coding-agent executor must pick up ready issues.

The workflow can be invoked manually from Actions after the PR is reviewed and merged. The hourly schedule is subject to GitHub schedule delays and repository policy; it is not a realtime daemon.

## Local / CI usage

```bash
python scripts/coordination/resolve_dependencies.py --validate-only
python -m pytest -q tests/contracts/test_dependency_coordinator.py
GITHUB_TOKEN=... python scripts/coordination/resolve_dependencies.py --report-dir coordination-reports
```

Only the protected GitHub Actions job should use `--sync-issues`; it writes issues, not application state. Results in `coordination-reports/status.json` distinguish `done`, `ready`, `in_progress`, `blocked`, `approval_required`, and `stalled`.

## Adding the full work backlog

The coordinator must map each of Feature #2's 38 assigned task IDs (and other feature task IDs) to actual owner-maintained ledgers before calling the registry complete. Never invent IDs, mark code-only tests as commercial acceptance, or count PR number as overall product percentage. Add independent work with `depends_on: []` or a real existing handoff, and use `manual: false` for human-gated proof. Feature leads keep working on all independent tasks even if their production gates remain blocked. They submit contracts through their owned handoff files; only coordinator edits this registry and canonical shared documentation.

## Current known integration gates

- Feature3 OpenVTO fixture and original-byte handoffs PR #609/#630 are merged. Feature4/5/7 may use them for tests without asserting garment-on-model or commercial rights.
- Feature2 Creative Director PR #551, Feature4 editor PR #322 and Feature7 semantic editing PR #513 are separate draft source integrations.
- Feature5 PR #465 is stacked; Part3 PR #125 has a Wan2.7 vs native Wan2.2 704x1280 / 121-frame contract incompatibility. Ratify before hosted use.
- Genuine Feature3 garments/models need independently reviewed license and likeness; actual Wan inference requires separate explicit authorization; GPU remains OFF.
- Azure issue #249 reliability and hosted tenant/rights E2E remain distinct release gates.

## 2026-10-29 — Import of ALL active numbered feature work
- `coordination/feature_tasks.json` is the full **159-row feature-task inventory**, distinct from the original 16 typed **handoff dependency nodes** in `coordination/dependencies.json`: #2 38, #3 33, #4 31, #5 22, #7 35; #1 source is closed. All rows pin exact owner source/ref SHA and original task ID/acceptance. F5's external dependency strings are kept, not converted into fabricated integration proof. F7 narrative addenda included.
- The existing ready-Issue dispatcher remains scoped to typed handoff tasks; feature-owned PR #551/#322/#465/#513 are not duplicated. `status.json` now includes `feature_inventory` summary, and Markdown report includes per-feature counts. Source-ready state is not integrated DONE; no automatic new agent execution.
- Operating guidelines and new-chat starter: `docs/FEATURE_CHAT_OPERATIONS.md` and `coordination/execution_policy.json`. The workflow rechecks dependency status after **successful main CI**, plus the hourly scheduled backup. Maximum 10 worktrees and two silent transient retries only take effect once a permitted executor actually implements them.
