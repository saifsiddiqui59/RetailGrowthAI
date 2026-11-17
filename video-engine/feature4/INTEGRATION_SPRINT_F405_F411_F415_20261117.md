# Feature4 integration sprint — F4-05 / F4-11 / F4-15 (2026-11-17)

Original task IDs are unchanged. This is **Feature4 parent source-in-progress**, not main/hosted accepted DONE.

- Live parent PR [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) retains newer footage transition, per-download lease/authorization checks, signed private-media guard contracts and all previously existing regressions.
- Surviving stacked [#828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828) is the source of the originally consolidated code/test and handoff material from closed-unmerged draft #822/#824/#827. No wholesale stale-parent merge was attempted.
- **F4-11:** source original MP4 SHA/device/inode/size/mtime identity checking, no-follow regular-file validation before and after actual motion-frame decode, finite scene/threshold validation; original source/test exact Git blobs from #828 copied into the latest parent in commits `e0bc41b4`, `70762243`.
- **F4-15:** ported approved local staged-media SHA/inode/symlink integrity helper, verifies every staged original after render before private upload. Kept existing parent's **additional per-asset current-lease/rights checks** and bundle recheck. Added three negative tests for same-content inode swap, staged-size policy, and renderer tampering while preserving prior per-download-lease revocation tests. Commits `e69cb722`, `f486099a`.
- **F4-05:** reused actual renderer effect allowlists from professional.py in editor contract; preserved **newer footage-layer transition behavior** missing in older #828 version and its regression tests. Added source parity/effect rejection tests from old #828 to current test suite, without removing existing tests. Commits `c1b415cb`, `da8870a0`, `31be150d`.
- Exact-original handoff documents for these three workstreams are preserved alongside this checkpoint. The old #828 full source blobs should NOT be copied wholesale over this newer combined source.
- CI: exact final parent head 4/4 not yet verified at this checkpoint. One earlier Actions attempt was cancelled on a newer push. Do not represent it as passed; recheck new latest head, then inspect any failed job/test.
- Next: verify final parent PR four jobs, repair owned code failures, compare #828's remaining docs/source/task history and retire #828 only if preservation and task traceability are confirmed; separately require fresh main code integration and review for original F4 task DONE.
- GPU OFF, paid provider OFF, no Azure/SQL/DEV/PROD changes or WineShopPOS modifications.

## Additional preserved F4-15 preflight (same source batch)
- Parent additionally checks the active claim **before** `load_feature4_bundle` (`0e634f8d`), retaining its independent post-bundle and per-download rights/lease rechecks and its stable staged original hashes. Added source-original stale-claim negative test (`25d60c99`). This restores the #828 preflight without regressing more recent protection.
- The exact-final-parent CI must be checked after this latest documentation commit; older cancelled-in-flight runs do not qualify.

## Source reconciliation: originals #690 / #731 / #792 (2026-11-17)
- #690 head `211312a68061bf5fe605f0e9e44653db4dd2cfcf`: current parent F4-15 staged no-follow SHA+inode/path postrender validation and original negative tests supersede original patch. Original stronger handoff and this checkpoint preserve traceability. PR closure = dedup, NOT original task DONE.
- #731 head `fdf615bdd09cad80e4129bf6d8527e0112eadd47`: prior streaming double-SHA of encoded media is superseded by stable-source inode/size/mtime + SHA before/after sampling. Ported original after-second-decode mutation regression, in addition to current same-content atomic swap checks. F4-11 IN PROGRESS.
- #792 head `47db93529edfd50b9ea7b68a610bbc805545ab49`: current parent already retains post-bundle and per-download lease/rights checks, but old source had unique F4-13 storage-key guards. Ported rejects for dot-only segments, trailing slash, ASCII control chars and original negatives. F4-13/F4-15 remain IN PROGRESS, no hosted acceptance.
- Source-only batch. Require exact-head four-job CI and eventual main integration/independent review for DONE. GPU/paid/cloud/PROD/WineShopPOS OFF.

## F4-13 original #803 auxiliary rights release gate integration (2026-11-17)
- Original stale DRAFT #803 head `73f0549e84ff9fba91ad57bb027829689149398f` contributes fail-closed current same-tenant rights verification for **every** composed asset (not only product/motion): images, videos, logos, audio, commercial use and provenance, synthetic fixture rejection, duplicate/malformed lineage IDs, and canonical output asset ID.
- Reconciled unchanged original code/test Git blobs `0fa57285f` and `a875fd90` into current parent #322; these strictly strengthen existing release checks while retaining all preexisting current parent behavior, + saved original source handoff `FEATURE4_F4_13_AUX_MEDIA_RIGHTS_HANDOFF_20261030.md` exact blob `05100d3c`.
- Even a successful source-only gate is **not** actual authenticated DB identity, real human media review or commercial release authorization; F4-13/F4-31 remain IN PROGRESS pending exact-head CI, main integration, real tenant entitlement/rights and human editorial sign-off. GPU, paid model, cloud/PROD/WineShopPOS unchanged.
