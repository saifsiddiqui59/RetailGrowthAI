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
