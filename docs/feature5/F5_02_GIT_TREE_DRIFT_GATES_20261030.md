# F5-02 — Clean, provenance-stable original Feature2 15/30/60 source probe

Date: 2026-10-30. Works only on an existing separate Feature2 #551 checkout at exact reviewed commit `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. Never merges Feature2, touches external services or runs an AI model.

## Security gates

- Require original F2 exporter tracked by Git, exact tree root and pinned HEAD, **zero edited or untracked paths**. Merely using `--untracked-files=no` could allow an untracked JavaScript dependency to alter the original output without changing the commit hash.
- Reverify exact source commit and clean tree after each of three actual Node CLI invocations, then once again before emitting any evidence. A Node subprocess that writes/imports a new untracked file fails closed.
- Existing strict F5 source boundary checks actual original 15/30/60 stdout, SHA/segment counts, seven independently altered direction/hash/retailer SKU/F4/rights/paid-origin denial cases, all without granting a runtime invocation.
- `tests/ai/test_feature5_f2_branch_export_probe.py`: synthetic subprocess tests confirm three durations and **five clean-tree checks**, untracked shadow modules and mid-export source modification denial; these **do not run real Feature2**. False-positive sample media, rights approvals, provider budget or production state remain forbidden.

## Still required to close F5-02

Coordinator/operator: use an isolated clean `git worktree add --detach ../RetailGrowthAI-F2-551 f38bf815cad7d77b7cadd9aa8bff55759e86947c` with the commit already present locally, then from F5 environment run `python -m feature5_motion.f2_branch_export_probe --feature2-root ../RetailGrowthAI-F2-551`. Record real Node stdout receipts for all three durations, required negative cases and trust flags. Coordinator must separately integrate F2 original #551 and F5 PR #781 -> #465 -> main; verify **fresh** four-job CI on integrated main. No original F2 export was executed in this CPU-only test change.

Original F5 ledger: 0 DONE / 3 IN PROGRESS / 19 BLOCKED / 22 total. No GPU, paid inference, model download, cloud/PROD writes or WineShopPOS.
