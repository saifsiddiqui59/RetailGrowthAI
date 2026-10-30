# Feature #5 — F5-02 actual original Feature2 exporter on CI

**PR #781 source-only handoff, 2026-10-30.** Original F2 PR [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) remains DRAFT and unmerged at exactly `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. Running an exporter from a different checkout is not the same as integrating it into main.

## CI verification strategy

The new Feature5-owned `tests/ai/test_feature5_original_f2_branch_ci.py` **automatically executes only on a GitHub Actions push for `refs/heads/feat/feature5-*`**, not normal offline developer runs or unrelated feature branches. It performs a bounded `git init`, `git fetch --depth=1` using only the same public GitHub repository's advertised `refs/pull/551/head`, and `git checkout --detach FETCH_HEAD` into a disposable directory. There are no writes to the working source tree, Feature2 branch, PR status, external services, hosted databases or uploaded media.

A mandatory SHA gate compares the fetched original Git HEAD against the independently reviewed 40-character commit. An advanced F2 PR or inaccessible original source **fails CI**, not silently reclassifies synthetic output as a real producer. Only after verifying that SHA does the existing `feature5_motion.f2_branch_export_probe` use the actual **unmodified Node exporter** at **15/30/60 seconds**, re-check Git cleanliness after each invocation, and validate true stdout with Feature5's strict consumer. Seven independent mutations of original reference, shot continuity, SKU, prompt hash and false approvals must all be denied.

A successful test appends a short, non-sensitive GitHub Actions step summary with the reviewed SHA, three raw stdout SHA256 values, 3/6/12 segments and seven tamper denials. This is machine-readable source-continuity evidence only: flags explicitly assert **no customer approval, GPU, provider/publishing authority, or model-rendered clip**. Test should only be called executed when the exact current head four-job Actions run genuinely passes, and the Step Summary is actually inspected.

## Still blocked / next acceptance gate

The original F2 producer must still be ratified and merged by the coordinator. Feature5 must then consume source from the integrated Git checkout, run the original integrated test on new main, and document fresh **4/4 main** CI. The standalone PR #551 source-validation cannot authorize any Wan2.2 job, license or garment first frame; original **F5-02 IN PROGRESS** even if these tests succeed. Feature5 parent remains #465, consolidated source PR remains #781, coordinator only merges after review. No GPU/A100, paid model, Azure/Supabase/PROD changes, customer media or WineShopPOS.

Original release ledger unchanged: **0 integrated DONE, 3 IN PROGRESS, 19 BLOCKED / 22 total**.
