# Feature5 F5-02 — Execute original Feature2 branch WITHOUT source duplication

Date: 2026-10-30. **Actual GitHub PR #551 is still open/draft**, at reviewed checkpoint `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. Feature5 parent is #465; this is an **independent source probe**, not a license, signed retailer approval or production integration.

## Implementation (in existing draft PR #781)

- New `feature5_motion/f2_branch_export_probe.py` runs a **separate, clean local checkout at exactly #551 HEAD**, never checks out into the current branch, fetches code or copies F2 source.
- Requires Git top-level = supplied checkout path, pinned actual SHA, clean tracked tree, and the original exporter tracked in Git. Rejects substituted or stale/dirty source.
- Executes the real `node ai-agents/creative-director/export-feature4-feature5-fixture.js` at **15/30/60 seconds**, with only an intentionally sanitized local environment and 45-second timeout per original source export.
- Passes **actual stdout bytes**, not fabricated copies, through existing strict Feature5 `qualify_export_bytes`. Captures per-duration source SHA, shot count and only non-authorizing proof. Denies seven independent shot-continuity, original retailer-SKU, hash, reviewer approval, paid-motion or fake Feature3 input tampering cases on the 30-second original.
- Returns explicit `ORIGINAL_OFFLINE_BRANCH_ONLY_AWAITING_COORDINATOR_INTEGRATION` with `can_submit_provider=false`, `can_publish=false`, `gpu_started=false`, `feature2_merged_to_main_proven=false`. This runner **does not** write PRs, paid workers, hosted databases or model outputs.
- `tests/ai/test_feature5_f2_branch_export_probe.py` tests CLI, pinned-revision, clean source, three durations and seven deny cases using **synthetic subprocess replacements**. It is **NOT proof that the real source was run** in GitHub Actions, which does not have PR #551 integrated.

## Operator/coordinator manual verification when original F2 is available

With the *existing cloned* RetailGrowthAI repo and reviewed F2 commit already fetched (no network needed during this validation):

```bash
git worktree add --detach ../RetailGrowthAI-F2-551 f38bf815cad7d77b7cadd9aa8bff55759e86947c
python -m feature5_motion.f2_branch_export_probe --feature2-root ../RetailGrowthAI-F2-551
```

Run from the **Feature5 PR #781** Python environment so its validator is the real source under test. Use Git Bash/uv as in `AGENTS.md`. Do not alter the F2 worktree while running. The command must fail closed on drift. The source exporter uses only editorial fixtures, not original retailer-approved footage, and this runner performs no network access itself. If Node is unavailable or original F2 commit not present locally, record a precise blocker instead of treating a synthetic fixture as a real export.

**F5-02 IN PROGRESS** until real original 15/30/60 stdout, negative cases and coordinator-ratified original integration all have supporting evidence. Coordinator owns actual F2 #551 integration, original #465 and #781 merges, canonical status and a fresh 4/4 postmerge main run.

Original F5 task ledger unchanged **0 DONE / 3 IN PROGRESS / 19 BLOCKED / 22**. GPU OFF, no paid inference, SQL/PROD changes, source media claims, WineShopPOS or customer sample generation.
