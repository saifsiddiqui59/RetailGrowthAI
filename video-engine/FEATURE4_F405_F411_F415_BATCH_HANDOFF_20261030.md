# Feature4 F4-05 / F4-11 / F4-15 source consolidation — 2026-10-30

**IN PROGRESS — one reviewable source batch, never production acceptance.**

This branch `feat/feature4-f405-f411-f415-integration-20261030` copies the exact nonoverlapping, feature-owned source and tests from sibling drafts **#822, #824 and #827** onto the same already-green Feature4 F4-14 draft #816 base commit `d01e3c716b4f651809d645684c921c6f0413c343`, with one atomic source commit. This avoids three independent coordinator merge trains. Existing PRs are independent trace evidence; they **must not** be double merged/cherry-picked after this batch is integrated. The canonical F4-05 ledger notes, F4-15 staging handoff and F4-11 motion handoff were preserved verbatim.

| Work ID | Source work included (not task acceptance) | Original evidence |
| --- | --- | --- |
| F4-05 | Renderer-supported CSS for all five allowed animations; one authoritative allowlist; reject unapproved CSS/effects | draft #822 |
| F4-11 | Moving-pixel original-byte+inode fence before/after real FFmpeg frame probing; deny swapped or altered media and unsafe/time-crossing parameters | draft #827 |
| F4-15 | Lease-current preflight before download and before CPU; no-follow staged SHA path-inode and byte cap; local race/oversize negatives | draft #824 |

## Verification policy

1. This combined branch requires its **own four-job exact-head CI success** (Python, Supabase tenant tests, frontend/Playwright, FFmpeg actual synthetic H264/AAC). Earlier individual passes cannot substitute for integrated source tests.
2. Coordinator reconciles stacked parent **#322 → #779 → #808 → #816 → this combined batch**, including #650 protected Functions ZIP packaging and main conflicts, then verifies **fresh main 4/4**.
3. F4-05 actual decoded effects + owner visual review, F4-11 revised native Full-HD real 60s and commercial quality, F4-15 hosted worker lease/rights/CAS still pending. Fixture tests are technical-only and cannot satisfy cross-feature approvals.
4. Record accepted subtasks separately from feature source progress; report **0/31 integrated DONE** while unmerged, do not claim actual producer AI motion, original garment rights, signed DEV E2E or commercial authorization.

No GPU, paid model, cloud deployment, production resource, WineShopPOS, approvals or user-visible video sample is created by this consolidation.
