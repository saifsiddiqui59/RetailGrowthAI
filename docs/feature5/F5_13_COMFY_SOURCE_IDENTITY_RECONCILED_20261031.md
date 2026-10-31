# F5-13 ComfyUI vendored source path identity — 2026-10-31

**Source-only / GPU OFF, NOT release-complete.** Original Feature5 task F5-13 has a reviewed CUDA OCI base, ComfyUI source/wheel SHA, ABI, distribution license and SBOM requirement. This patch validates a *provided local inventory* only and does not independently attest those external approvals.

## Reconciled source and tests

Old overlapping Feature5 drafts #755 and #772 both had exact-head 4/4 CI, but were based on older parent branches; no blind old-branch merge was performed. We implemented the relevant compatible source into consolidated Feature5 #781:

- `feature5_motion/infra/wan22_source_audit.py`: fail closed without OS O_NOFOLLOW and O_NONBLOCK; hash each reviewed local source file from a regular, single-link, stable descriptor and check its original path identity. Require matching device, inode, size, mode, hardlink count, mtime and ctime before/after byte read; refuse extras, missing approved names, source drift and symlinked paths. After the whole sequential audited tree, recheck all approved file and directory identities to deny a previously hashed file's same-byte replacement while later paths are read. Returns only a source-audit report, not executable approval.
- `tests/ai/test_feature5_wan22_source_audit.py`: original unit/CLI acceptance preserved plus four synthetic negative tests for external hardlink, same-byte file swap after hashing, same-length rewrite after hashing, and symlink swap between initial stat and secure open. No genuine vendor source, CUDA image, original checkpoint, user-media or model inference involved.

## Verify and ownership

1. Exact combined #781 HEAD all four CI jobs, with non-skipped Python regressions and existing FFmpeg actual private-media nested 4/4; do not claim tested until observed.
2. Coordinator reviews one consolidated PR #781 and shared historical `tests/media` addition, merges to parent Feature5 #465 only after checks. Old overlapping #755/#772 can be separately closed as superseded if exact source/CI reviewed, never merged blindly.
3. F5-13 requires independently reviewed genuine ComfyUI full source/weight distribution rights, wheelhouse and image digest, actual CPU/gated OCI SBOM legal/ABI evidence. F5-14 real 3 weight SHA + signed private mount remains outstanding. GPU OFF, no Azure service/model costs, no PROD or WineShopPOS changes.

Original 22 release tasks remain **0 integrated DONE / 3 IN PROGRESS / 19 BLOCKED**. Fixtures are not production media or commercial rights.
