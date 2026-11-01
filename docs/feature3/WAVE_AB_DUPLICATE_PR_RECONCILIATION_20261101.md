# Feature #3 — Wave A/B duplicate PR reconciliation (2026-11-01)

**Scope:** Feature3-owned source and GitHub bookkeeping only. No new media, hosted SQL, GPU, paid inference, PROD, WineShopPOS, or claim of 33-package production acceptance.

## Verified source baseline

- Current `main` at inspection: `456b1757d7df2f0cc28a5ef6c8ba203b18380948`.
- Reviewed Wave A integration: [PR #811](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/811), merged at `c14d099db61b8df14fa1907b8046fc3b3bd51090`.
- Reviewed Wave B integration: [PR #813](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/813), merged at `7404b46e2aeda2707dd7793a4bae36295390d039`.
- Current-main [Part 1 CI #41178167285](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41178167285) ran against **exact** `456b1757d7df2f0cc28a5ef6c8ba203b18380948`; inspected four successful jobs: frontend, Supabase isolated auth/RLS, Python/uv, FFmpeg.
- The workflow success proves source/contract checks only; it is **not** licensed retail-model approval, real GPU output, Azure route deployment or hosted end-to-end acceptance.

## Stale standalone PRs closed without duplicate integration

Each of the following open standalone PRs targeted `main`. We independently fetched **all three changed paths** from the exact PR branch and current main, compared Git blob SHA for each, and found every path identical. Explanatory comments were added before closing, without changing merged source.

| Closed PR | Original head | Consolidated source | Exact paths checked |
| --- | --- | --- | --- |
| [#790](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/790) | `a76d85bd53a573d87854a7c583bff66815a78510` | Wave B #813 | `feature3-context.mjs`, `feature3-context.test.mjs`, approved-copy handoff |
| [#791](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/791) | `ed1686b2a8f817e06777cd189c8fe71e2741f41f` | Wave B #813 | `Feature3SecureDraftWorkspace.jsx`, `feature3-workspace-scope.test.mjs`, provider-state handoff |
| [#761](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/761) | `be5580330e6cfbb0e4411b0bdb7bde5c8db90f32` | Wave A #811 | `feature3_gpu_outbox_service.py`, `test_feature3_gpu_outbox_recovery.py`, outbox handoff |

## Test-lineage reconciliation and remaining open PRs

- [#760](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/760) was **also closed as superseded by Wave A #811**, but its three changed files are **not all blob-identical**. GPU envelope module and handoff are exact matches. Its 120-line original queue-envelope test is preserved as a complete **ordered line subsequence** of current main's 122-line test. Main adds only two lines to the mocked dispatch ACK (`outbox.confirm_dispatch.return_value=True` and its explanatory comment); no original assertion was removed. This stronger, explicitly qualified source/test inclusion proof—not a false identical-blob claim—was recorded in the PR comment before closure.
- Other outstanding Wave A/B constituent PRs were not included in this limited audit. Do not mass-close them without evidence.

## Next owner actions / release limits

1. #760's historical test source was reconciled and closed with explicit proof of all original test lines retained in order; continue reviewing any **other** stale Wave A/B child PRs individually rather than re-merging their source.
2. Continue an independent source-only F3 package acceptance task where still eligible; do not redo merged Wave A/B work.
3. Existing host blockers remain: [#325](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/325) / [#471](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/471) signed private PNG route and rights callback; F3-LICENSED-MEDIA independent approval; [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) Azure reliability; [#627](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/627) genuine worker traces; F5 GPU authorization.
4. Do not increment product `DONE`: Feature #3 tracker still shows **0/33 fully hosted accepted** (1 source-integrated, 11 source-partial, 21 blocked/dependent). The separately recorded F3-01 source milestone is not a hosted output.

This is a **docs-only reviewed handoff**; do not append unverified coordinator task-status events.

## Parallel continuation audit — additional exact-source duplicate cleanup
- Independently verified all three changed-file Git blob SHAs on current main for [#738](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/738) (signed-link render fence), [#752](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/752) (private-source encoding), and [#802](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/802) (approved video-use grant). Each source+test+handoff blob matched exact PR head. Explanatory comments added, and each standalone PR closed as **unmerged superseded** by merged Wave A #811 or Wave B #813. No source/test was lost, no new hosted DONE.
- [#744](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/744) remains open: two changed paths match exactly but `feature3_gpuoff_queue_intake.py` has further changes on main (public `require_gpu_off`, source snapshot). Do **not** close without function-level semantic reconciliation.
- Independent **F3-10/F3-13** generated-Blob cleanup retry patch proposed in [PR #859](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/859), with scoped regression tests. This patch is separate from and not absorbed by Wave A/B; code review, exact-head CI and fresh postmerge main CI required, hosted acceptance unchanged.

## Continued source-integration verification — original Wave B/A stacked items
- [#798](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/798): four changed blobs exactly match main; source+tests+handoff. Closed unmerged superseded after evidence comment.
- [#843](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/843): private PNG chunk-integrity source and tests **both exact blob matches** to main. Main's Wave B `docs/feature3/RUN_CHECKPOINT.md` independently records their import; the older standalone checkpoint text is not identical. Closed source superseded with qualified evidence.
- [#834](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/834): typed attempt guards remain in main (split into two equivalent clauses); main has separate boolean-attempt denial plus float/string negative cases. Wave B run checkpoint records its reconciliation; older standalone module/test/docs blobs not identical, so closure based on **semantic code + test coverage**, not identical SHA.
- [#768](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/768): original fail-closed replacement source preserved, with main adding a separate decoder-failure method; all original test lines remain in main and handoff blob is identical. Closed source superseded after code and assertion-level review.
- [#744](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/744): original twice-current GPU-OFF check preserved, refactored into a public method used around empty-peek inspection; main adds a private snapshot hash and tighter status typing. Exact test+handoff blobs, changed module semantics reviewed. Closed source superseded with qualified receipt.
- **All five closures remain source bookkeeping only**, not new merged product work and not paid/hosted acceptance. See individual PR comments for checks and latest main 4/4 baseline. Continue reviewing unrelated outstanding PRs individually; do not infer equivalence from PR number alone.

## F3-10/F3-13 private history reconciliation — #812
- Independently inspected all seven changed paths on [PR #812](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/812). Three original handoff blobs match main exactly. Current main has newer private-history/API-identity and preview-revocation source and revised tests (not exact blob matches). Reviewed behavior: strict allowlisted four-field public generated-history presentation, internal API identity fence and rejection of extraneous URLs/approval flags; original model preview revoke-before-splice ownership; updated forged-state/rotation/retry negative tests. Older source's rejection of internal `api` would break legitimate current-session rendering, so DO NOT overwrite with historical original. PR #812 closed as **semantic superseded** by Wave B #813 with evidence comment, not incorrectly marked exact source match. Package remains not hosted-accepted.

## Final source-duplicate receipt — #729
- [#729](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/729), Feature3 F3-03/F3-11/F3-12/F3-13 model-library rights/use fence: independently checked **all three changed blobs** (model library module, test, scoped handoff) and matched each SHA exactly against current main. Closed unmerged superseded by Wave A #811 with evidence comment. Not a new hosted acceptance.


## 2026-11-01 — Additional duplicate-safe PR closures (#693, #722, #727, #728)

Rechecked exact changed files from current `main` (`456b1757d7df2f0cc28a5ef6c8ba203b18380948`) and the original PR heads. Each was closed **unmerged** after an evidence comment; no source, migrations, cloud resources or payment paths were changed by these closures.

| Closed original PR | Original task IDs | Verified disposition | Main still required |
| --- | --- | --- | --- |
| [#693](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/693) | F3-03/F3-12/F3-13 | Semantic supersession: model `approved_uses` is a strict bounded unique known-use list requiring `poster` on main; the main source additionally tightens current rights revision, hash and claimed lease. Scoped handoff blob exact; source/test newer, not identical | Actual independently reviewed per-image rights; signed private consumer QA |
| [#722](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/722) | F3-11/F3-13 | Semantic supersession: `verifyPrivateModelOriginalUploadReceipt` on main checks exact shop/model/SHA-named path, safe byte bounds and never-approved flags **before** registration; handoff blob exact. Main adds session-rotation fences not in the old PR | Signed DEV model upload, licensed customer originals, reviewer approval |
| [#727](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/727) | F3-06/F3-07/F3-13 | **Exact three-blob source duplicate** (module, test, handoff all SHA-identical to current main); no need to reapply | Deployed approved evidence RPC, immutable real source/output and independent finance review |
| [#728](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/728) | F3-08/F3-13 | Semantic supersession: handoff blob exact; original test lines preserved in newer main; original PNG header/trailer check replaced by stronger `_valid_png_chunks` CRC/chunk-boundary validation | Approved mounted authenticated no-URL binary route and signed two-tenant DEV denials |

These are **four closed duplicate PRs, not four completed hosted tasks**. Preserve existing accepted task record: `coordination/task_progress.json` has F3-01 `source_integrated`; full Feature3 hosted acceptance remains **0/33**. Independent private-media/security, DB, licence and hosted approval gates still apply. Separate active tested PRs [#859](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/859), [#861](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/861), [#862](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/862), [#863](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/863), [#864](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/864) must **not** be closed or marked SOURCE_INTEGRATED merely for passing source CI. The separate shared coordinator receipt PR #860 still needs independent review.
