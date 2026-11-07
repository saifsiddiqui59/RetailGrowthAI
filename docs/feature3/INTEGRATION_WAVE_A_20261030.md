# Feature #3 — Wave A integration proposal (2026-10-30)

**Status: NOT MERGED, NOT PRODUCTION / NOT 33-package DONE.** This feature-owned review branch composes the exact Git blob contents of 17 independently prepared Feature #3 pull requests into one candidate tree based on main `a75f9df62451dbc701633782a9baf1b16e32c8c8`. It does not execute cherry-picks on main, change shared task status, provision hosted resources, or authorize any media/GPU inference.

## Included source PRs
#683 generated private Blob decode cleanup; #687 GPU-OFF queue peek status; #689 bounded private PNG browser stream; #699 full outbox batch prepublication validation; #703 current GPU claim lease expiry and rights revision parity; #706 opaque operator reconciliation failures; #708 approved model catalog rights; #721 registered private-source row/license URL; #722 scoped model upload receipt; #727 generated output evidence PNG restrictions; #728 private binary PNG HTTP framing; #729 approved model library reuse-rights; #730 worker input lease fence; #738 scoped signed image link final-render gate; #752 private source transport encoding denial; #760 Unicode queue-envelope denial; #761 unique dispatch tokens.

Only **55 distinct changed paths** across these 17 PRs; verified zero overlapping changed paths before composing the Git tree. Preserves each PR's exact changed blobs with no manual inferred merge edits. Individual exact-head CI was 4/4 as verified before this proposal; **combined-branch CI is still required** because cross-file interactions can fail.

## Coordinator review / acceptance
1. Inspect this combined branch and its full 17 PR source diffs; independently check secure no-GPU behavior and authoritative tenant/media rights, original upload and output integrity, one-shot financial/queue ACK behavior.
2. Require complete **four-job CI on the exact combined branch head**, including Python, frontend+mock browser, disposable Supabase and FFmpeg. If conflicts or failures emerge, repair the integration branch without bypassing tests; treat new head as unverified until CI passes.
3. **Coordinator only** merges the approved integration PR into main. Verify fresh postmerge main 4/4 CI, append project state/next task/work log/decisions and reviewed task-progress event. Decide whether to close original 17 PRs as superseded *with exact merged-source proof*; their original PRs remain open until coordinator acts.
4. Defer overlapping PRs **#693** (overlaps #703 rights plan), **#744** (overlaps #687 queue intake), **#768** (overlaps #683 Blob scope) and **#709** (overlaps #683 history UI). Reconcile each against the integrated branch using current tests, then a second combined check. The newer #778/#790/#791/#798/#802 are separately owned and not silently included.

**Still not released:** 0/33 fully hosted accepted. #471/#325 signed live private PNG route and real signed JWT/tenant negatives, #249 Azure 503, #627 real Testing Chat worker evidence, F3-LICENSED-MEDIA approved commercial originals, F5-GPU-AUTHORIZATION and PART3-WAN22-CONTRACT are unresolved. Fixture receipts do not certify licensed photos, VTON, live media or paid outputs.

**Safety:** GPU/paid provider OFF. No Azure queue send, live SQL migration, Supabase DEV/PROD mutation, PROD release, public media, real customer approval or WineShopPOS change made by composing this branch.
