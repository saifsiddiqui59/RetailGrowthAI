# Issue #249 — Part 1 CI runner reliability (2026-11-19)

## Source change (PR #1027)

- Replaced unreliable Ubuntu `apt-get update` during FFmpeg provisioning and Playwright `install --with-deps` setup with a **real** version-matched `mcr.microsoft.com/playwright:v1.56.1-noble` CI job and SHA256-pinned full-filter FFmpeg 8.1 GPL Linux x64 binary.
- Exact independent FFmpeg build: `ffmpeg-n8.1.3-36-ge22a4510c9-linux64-gpl-8.1.tar.xz` from immutable GitHub release `autobuild-2026-11-18-12-39`, expected SHA256 `fce424851b0a982bdd4ac4e96f0e7b32cf29de999e54500676d41ad175ed0c79`. This third-party binary is **CI-only**, never copied into customer or production downloads. It supplies required `libx264`, AAC and `drawtext`. The earlier npm static binary had no `drawtext` and failed genuine caption tests; it was removed.
- The full source suite still executes real `video-engine/ci.sh` with **1,051** media unit tests, an actual 30-second 1080×1920 synthetic H.264/AAC render, exact ffprobe stream checks, sampled content/xfade/audio assertions and CPU benchmark. Nothing is skipped to obtain green CI. Existing separately skipped media tests are unchanged.
- FFmpeg 8.1 exposed a genuine color-range mismatch in JPEG-derived composition: encoded `yuvj420p` instead of the required `yuv420p`. The renderer now converts frame pixels to TV/limited range via `scale=in_range=auto:out_range=tv` and signals `-color_range tv`, while the strict probe still REJECTS `yuvj420p` and reports only safe codec/geometry metadata on failures.
- Real mobile Playwright navigation now scrolls the offscreen Subscription link in a long drawer into view before asserting it is visible in the viewport, clickable and reaches the correct subscription page. No mocked browser or route test bypass.
- The isolated Supabase security job also avoids unconditional Ubuntu apt-mirror access: pin the GitHub-hosted Ubuntu 24.04 runner, verify its preinstalled PostgreSQL 16 `psql` exists, and **fail closed** if it does not. Every tenant RLS/private storage/feature-budget SQL test remains mandatory; CI regression checks now enforce those commands.

## Exact-head source CI evidence

- Earlier runs #44483223193 and #44485310540 caught real `drawtext` and color-range failures after apt independence, and the previous mobile viewport assumption; all were fixed in source rather than ignored.
- [Actions run #44486001496](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44486001496), source head `6466880519fa7c072986c7624f3a43fd7499acba`: **COMPLETED SUCCESS 4/4** — Python/uv, Supabase isolated tenancy, React/Playwright browser and FFmpeg/renderer. This confirms offline CI reproducibility for that exact source head only. Subsequent documentation commits must have their own fresh exact-head CI.
- Shared workflow, renderer and browser changes still require **independent affected-lead/human review** and a fresh accepted main integration per `docs/FEATURE_SELF_MERGE_POLICY_20261031.md`. CI passes are not independent approvals.

## Unfinished Issue #249 gates

- Original Flex DEV pre-handler/markerless HTTP 503 issue remains OPEN. Separate classic Y1 DEV still hosts only two approved GETs; no five-route deployment or production cutover.
- Stage and review #968 → #995 → #1025 before any manual protected Y1 release; do not bypass DEV environment protection, rollback verification, positive hosted signed two-shop JWT/RLS, original POST/PATCH/private media, measured p95/p99, or rights/billing/queue acceptance.
- No Azure, cloud SQL, app settings, GPU, paid model, PROD or WineShopPOS mutation in this PR.
