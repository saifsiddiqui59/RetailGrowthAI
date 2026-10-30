# Feature #4 F4-11 — continuous black-hold scan handoff (2026-10-30)

**IN PROGRESS, not integrated DONE.** Branch `feat/feature4-continuous-black-qa-20261030` stacks on consolidated draft #779. This work is source-only, no real retailer media, paid model, GPU or production cloud.

## What changed
The existing 15/30/60 real H264/AAC sampled scene QA checked five interior points per shot and could miss an unwanted 0.8-second fully black hole BETWEEN points. New FFmpeg `blackdetect` performs one bounded **continuous full-timeline video decode** at a conservative 0.65s nearly-all-black threshold, rejecting >=threshold holds even if all five scene spot checks pass. The emitted v3 proof records the full scan, threshold and zero findings, while explicitly NOT certifying subthreshold flash absence, legibility, rights or human-quality approval. The 60s source-to-receipt verifier now requires v3 full-scan evidence and denies fabricated approval, missing fields, noninteger booleans, changed threshold or detected holds.

New 15s actual FFmpeg synthetic regression encodes a real 0.8s black hold hidden between previous five sample times. Existing encoded red/blue/green fixture verifies no false rejection, and 60s receipt negatives test fail-closed omission/forgery.

## Acceptance and remaining gates
Run full four-job exact-head branch CI, coordinator-reviewed integration to main and fresh main 4/4. Real **updated** 60s full-HD garment/motion/outro source and actual reviewer approval remain F4-01/F4-11/F4-12 separate gates. This technical control neither proves every isolated black frame nor transforms synthetic media into a commercial render.

Ownership: Feature4 files only. Do not modify workflows, shared coordinator docs, signed auth, Azure, WineShopPOS, or launch GPU.
