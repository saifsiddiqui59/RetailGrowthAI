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
