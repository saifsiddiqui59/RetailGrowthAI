# Feature #4 durable run checkpoint — 2026-10-30

## Current task and source change

- Task: **F4-08** (accurate frame scrub/playback), partial source hardening only; NOT complete, NOT integrated.
- Parent: draft PR #322, `feat/feature4-professional-video-studio`, observed SHA `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
- Owned stacked PR: **#838** `feat/feature4-f4-08-finite-frame-seek-20261030` targeting the parent branch.
- Code head before this checkpoint: `15eef682fcb5003e5c00021ba671eded449ba10c`.
- Files: `frontend/src/features/video/frame-seek.mjs` (finite/bounded/24-30fps normalization), `frontend/src/features/video/TimelineStudioSurface.jsx` (uses safe helper and refuses nonfinite incoming positions), `tests/frontend/feature4-frame-seek.test.mjs` (two negative/positive node:test cases).
- Local targeted verification: Node v22.16.0, `node --test` on an equivalent isolated copy of the new pure helper/test: **2 passed, 0 failed**. This is NOT an exact-checkout run and is not proof of the entire frontend or full PR CI.
- GitHub exact-head CI: **not verified yet**; inspect PR #838 after this checkpoint push and require 4/4 before coordinator review. Do not merge or mark DONE.
- Still missing for F4-08 acceptance: real decoded-preview visual parity and device/browser verification; no customer media or production release claims.
- Cross-feature blockers: none for this finite-seek guard. Global coordinator integration/hosted gates remain outside this task.
- **NEXT independent task**: F4-06 (multi-track independent audio levels). First inspect existing renderer semantics and other open F4 PRs to avoid duplicating work. If that is too broad, proceed with another small unblocked owned test or hardening task.
- Keep GPU OFF; no paid model, PROD, Azure deployment, unapproved SQL or WineShopPOS edits. Do not alter shared canonical status. Coordinator reviews task evidence and integration separately.

## Continuation — second run (2026-10-30)

- Resumed the verified existing F4-08 stacked PR #838 rather than duplicating the task or modifying main. F4-06 multi-track gain automation remains unsupported by current renderer and is deferred pending actual renderer semantics; do **not** enable gain sliders as fake controls.
- Source commits: `2664ee2d0b9448aced0281dae3b7ad89a200be1c` (validated scene midpoint helper), `61d848267e7ba36ba0b4378ec53c2b1290b320cf` (caption and scene clicks now frame-normalized), `2e177eb1b1d49de4a9422ced7ea3378e497dc174` (positive/negative tests).
- Files: `frontend/src/features/video/frame-seek.mjs`, `frontend/src/features/video/TimelineStudioSurface.jsx`, `tests/frontend/feature4-frame-seek.test.mjs`. Scene/caption click paths no longer bypass finite frame normalization; malformed scene spans fail closed.
- Targeted verification: Node v22.16.0, `node --test /tmp/f4seek/tests/frontend/feature4-frame-seek.test.mjs` on an **isolated source-equivalent copy**, **4 passed / 0 failed**. NOT an exact GitHub checkout, browser test, decoded-video parity, or complete 4-job CI.
- Full exact-head CI: pending inspection after checkpoint commit. Do not claim PR-ready, integrated or accepted F4-08. Parent #322 and stacked #838 remain draft/unmerged as observed.
- Remaining F4-08: real decoded-preview parity and browser/device verification. NEXT independent eligible: **F4-07** offline audio fade/ducking negative-path test after checking existing audio renderer and related branches; if already covered, select another F4-owned source test. Do not bypass licensed voice/music approvals.
