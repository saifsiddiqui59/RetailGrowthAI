# Feature4 stacked draft reconciliation — 2026-11-15

This is an Integration Sprint bookkeeping checkpoint, **not release acceptance**. The source of truth is the GitHub PRs and exact commit blobs; feature #4 development still lives in #322 and owned source branches. No source code was merged, no tests run in this cleanup, and no GPU/provider/DEV/PROD/WineShopPOS mutation was made.

## Exact Git-blob duplicate findings

| Closed PR | Verified exact head | Changed files | Surviving source PR | Verification |
|---|---|---:|---|---|
| #822 (F4-05 effect parity) | `1ba7949c2666691a6442e007053bd1a2c58512d3` | 5 | #828 `ca103ce851c567d67198040a5a41738ea98e8395` | All 5/5 changed paths have identical Git blob SHA in #828 |
| #824 (F4-15 lease/staged inode) | `3dd468202a781f331391ff1172ba4f5cbc60384b` | 3 | #828 (same head) | All 3/3 changed paths have identical Git blob SHA in #828 |
| #827 (F4-11 encoded motion identity) | `b1a5058c853b8087788982311c12f2576323877d` | 3 | #828 (same head) | All 3/3 changed paths have identical Git blob SHA in #828 |

All three PR objects were closed **UNMERGED** with durable per-PR evidence comments. At the original 2026-11-15 checkpoint, surviving #828 was OPEN and targeted the F4 CPU profile branch; its exact original 11 source/test/handoff blobs were preserved. **Live recheck on 2026-11-17: #828 is CLOSED UNMERGED**; the current #322 F4 parent contains reconciled source and an additional original-tracker provenance archive, but this is still not main integration. Closing child PRs did **not** add their code to main or mark F4-05/F4-11/F4-15 DONE.

## Older drafts reviewed and deliberately kept open

- #735 — duplicate-encoded QA: candidate `feature4_edited_export_qa.py` has different SHA from both current #322 and older batch #779; unique mock decoder function present in #735 but absent in #322.
- #745 — encoded motion probe: changed QA logic not in #322, needs controlled additive port/testing.
- #753 — full-minute contiguous visibility receipt: unique requirement absent from #322 version, keep source/test.
- #773 — near-cut boundary probes: unique QA logic absent from #322 version.
- #784 — cancelled drag fencing: JSX differs from #322 and older #779; needs current UI event reconciliation.
- #799 — original-stage receipt identity: source/test/handoff differ or are absent on #779.
- #803 — auxiliary media rights denial: source/test/handoff differ or are absent on #779.
- #808 — 60s continuous black-scan receipt: changed paths identified; **full semantic dedup NOT proven**.
- #822 and #824 — included in the ten-first review set; closed as above.
- #827 — additionally inspected and closed, bringing the reviewed set to eleven unique PRs.

Current original [F4 parent #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) is still DRAFT and cannot be treated as main-integrated. Avoid wholesale merging old ancestors or silently replacing newer security/tenant contracts. Existing [batch #779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) while historical [consolidation #828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828) was closed unmerged after reconciliation into the *still-open* F4 parent. Neither state means DONE.

## Follow-up / bounded acceptance

1. Feature4 owner checks the already-reconciled #828 source and retained unique older changes against the **latest** #322 and newest main, preserving all surviving negative tests and original provenance without reopening #828. Preserve current tests and the new missing protections.
2. Run targeted CPU/FFmpeg/UI negative tests, then verify required exact-final-head 4/4 CI on eligible main-targeted PRs. Review sensitive rights, storage/auth, and cross-feature paths independently.
3. After safe non-draft PR merge, separately verify fresh exact-main 4/4 before any original task DONE receipt. Only then update canonical completion counters.
4. Do not restore old branches merely to reduce the open count. GPU OFF, paid AI OFF, no cloud deployment, PROD or WineShopPOS modifications.

Reference: PR comments on #822, #824, #827 and the preserved parent #828.

## Live CI and review recheck — 2026-11-17

- Parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) currently has source head `b9525a9ea3d5e5aee351edf89a3c011c2314ed2e`, still **DRAFT** with zero independent reviews. Earlier exact source commit `c2bc9ff9b47c46c9186a72b9faa86e894bebb1cd` failed FFmpeg job in [run #44011387138](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44011387138) because the inode-swap regression mock exhausted its frame `side_effect` and raised `StopIteration`. The later parent commit adds a 4-line correction in `video-engine/feature4_edited_export_qa.py`, but its [run #44012074650](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44012074650) had three successful jobs and **cancelled** FFmpeg rendering near the existing job time budget: **not 4/4 accepted**.
- Separate [#967](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/967) proposes a 15→25-minute FFmpeg workflow cap and passed exact-head [run #44000894199](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44000894199) **4/4**. It remains OPEN and requires independent shared-workflow review; a green workflow-change PR does not retroactively pass #322's media job.
- [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) remains OPEN/DRAFT and historically stacked; current #322 holds newer reconciled versions of shared source. **Do not merge #779 wholesale, mark F4 task DONE or retire it solely on this bookkeeping evidence**; require full source/negative-test parity and safe review.
- This docs PR [#966](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/966) previously passed exact-head [run #44011542854](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44011542854) 4/4, **before this follow-up docs correction**. Recheck final exact-head four-job CI and independent canonical-doc review before any merge. No GPU, paid models, hosted mutation, PROD or WineShopPOS actions.
