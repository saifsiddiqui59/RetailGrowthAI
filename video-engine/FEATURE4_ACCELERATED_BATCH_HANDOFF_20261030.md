# Feature4 accelerated source batch handoff — 2026-10-30

**IN PROGRESS — source-only proposed single-review bundle.** One coherent Git commit combines **five** previously green but unmerged, nonoverlapping Feature4 draft-PR batches (#686, #690, #695, #701, #705) into `feat/feature4-batched-source-handoff-20261030`, based exactly on existing Feature4 parent SHA `e32a8da61a6272666d757b6c51b0ec2576d7602f`. CI must validate this combined tree. Do **not** mark DONE merely because an individual draft had 4/4.

| Original draft | Tasks advanced (not closed) | Exact branch push CI |
| --- | --- | --- |
| #686 | F4-04 mock 30s actual encoded duplicated-replay parity | #40955296326, 4/4 |
| #690 | F4-13/F4-15 staged private input SHA and worker mutation denial | #40955734381, 4/4 |
| #695 | F4-14 immutable 30s local CPU benchmark SHA receipt | #40961371565, 4/4 after import repair |
| #701 | F4-10 React timeline stale-drag cross-tenant/approval denial | #40961280016, 4/4 |
| #705 | F4-03 exact-head actual 15/30/60 MP4 evidence verifier | #40966895351, 4/4 |

## Throughput changes for the next batches

- Instead of five separate coordinator integration/merge trains, review this **one combined draft** with original source commits and exact proofs attached, and run normal four-job CI once at the final combined head.
- New work on independent F4-01/F4-02/F4-05/F4-07/F4-11/F4-12 can proceed on separate nonoverlapping source branches, but must not overwrite these same files. **Global maximum 10 is a concurrency ceiling, not 10 agents currently running**; there is no installed coding executor or atomic claims.
- Do targeted security/parity tests when touched, especially source-media rights, SHA/tenant/approval/race invariants; batch slower full FFmpeg/Playwright/Supabase 4-job CI at meaningful review boundaries. Do **not** defer all testing until task end or disable protected workflows. GitHub default branch-push CI still automatically triggers on pushes; batching files in one tree/commit minimizes redundant runs without changing coordinator-owned workflows.
- Reuse verified versioned F2 creative, F3 private rights metadata, F5 bounded motion receipt, F7 edit instructions and deterministic approved mock fixtures only as **technical interface test inputs**. Never represent these as actual human-approved music, garment-matched Wan video, real voice, or released retailer media.
- Keep details and task IDs in the original ledger plus feature handoff. Coordinator alone reviews, reconciles main, merges, issues accepted status receipts and checks **fresh** main 4/4.

## Unresolved exact release dependencies

- F4-03 needs **three actual 15/30/60 same-code encoded outputs**, not just the checker; F4-10 manual mobile/a11y; F4-14 full three-length CPU/RSS budgets; F4-13/F4-15 hosted signed worker and rights need separate acceptance.
- F4-16/17: Feature2 independently approved script, audio licensing and real spoken-word timed cues; F4-18: Feature3 actual rights-authorized product/model originals; F4-19: Feature5 authorized real model motion (GPU remains OFF); F4-20: Feature7 human-reviewed edit instruction; F4-21: complete source/owner integration and signoff.
- F4-22/#650 is coordinator-owned Functions ZIP package; F4-23 coordinator review/main integration; F4-24..28 coordinator signed auth/lease/output/worker integration; F4-29/#249 Azure HTTP 503 owner; F4-30 coordinator signed DEV E2E; F4-31 owner commercial content approval.

**No GPU, charged model/coding executor, PROD, hosted SQL, WineShopPOS, user-facing samples or unreviewed owner approval.**
