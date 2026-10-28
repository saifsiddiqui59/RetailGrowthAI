# Feature #4 — Offline work versus actual release gates (2026-10-28)

**PR #322 draft**, branch `feat/feature4-professional-video-studio`. No main merge, GPU billing, cloud/PROD deploy, or WineShopPOS writes. The user authorized realistic **mock** Feature2/3/5/7 inputs without waiting for sibling implementation. These do not become real tenant-approved media solely by appearing in tests.

| Proof | Current status / evidence | Must happen before commercial launch |
|---|---|---|
| Reuse actual upstream `MartinDelophy/ai-video-editor` | Imported MIT source modules, attribution; original upstream pinned CI #40501035304 pass; partial editor integration | Full timeline + preview UI/effects parity; upstream whole app not launched in network-restricted development |
| Scene editing/trim/split/undo/redo, snapping/ruler/zoom | Browser and pure editor tests run in 4-job GitHub CI | Human production usability, keyboard/a11y and real complex timelines |
| JS editor command → trusted Python renderer plan | `test_feature4_editor_to_render_contract.py`: exact approved caption/offer/CTA, F3/F5 mock source and private manifest | Real source durations/frames and final rendered edit-by-edit comparison |
| Licensed source audio/music/SFX | Existing engine renders authentic synthetic source sound, music duck and short SFX | Music rights and measured actual voice/audio clarity |
| Optional full-Reel narration | New fail-closed private audio, length check and deterministic HyperFrames track; **latest exact-head CI pending** | Real spoken VO, intelligibility and word-accurate caption sync, full output audio QA |
| Final H.264/AAC 1080×1920/30s MP4 | Actual full 30s synthetic CPU render and ffprobe from earlier source CI #40684322439 (4/4), renewed latest CI pending | Exact current-head codec and real garment footage signoff, production runtime SLA |
| Cross-shop/revocation/approval/idempotency | Negative tests for F2 intent, F3/F5 media grants, F7 edits, once-only outbox callbacks; v2 transport default OFF | Real JWT/RLS DB transaction, claim/lease/quota and hosted tenant-negative acceptance |
| Cinematic moving human in matching kurti | **NOT DEMONSTRATED**; existing 30s demo is synthetic/illustrated | Real F3 approved reference, actual F5 Wan clip and human garment/fabric/anatomy/flicker approval |
| Reproducible legal runtime | SHA256-guarded temporary npm lock / pinned upstream notice | Git-tracked lockfile, full libvips/Chromium/FFmpeg/commercial notices, Azure Node/CPU benchmark |
| Production publish | **NOT READY**; PR draft and Azure issue #249 unresolved | Coordinator integration, reliable hosted gateway, authenticated E2E and release approvals |

**Owner-ready definition:** Offline engineering can be called independently verified only after the latest exact-head 4/4 CI + browser/full-HD audio/video/tenant gates pass. The end-to-end retailer SaaS experience cannot be called complete without the right column's real source, infrastructure, and reviewer acceptance. Do not mark any outstanding part complete on simulated evidence.
