# Hosted DEV poster render gateway 503 — safe-canary follow-up (2026-10-24)

## Verified evidence
Owner-authorized [actual cloud run #40090505121](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40090505121) completed actual ROOT approval, retailer JWT shop creation, seven-day campaign, saved/reopened draft and cross-shop denies. Cleanup passed. It **failed** after a gateway-source HTTP 503 on `POST /api/poster-drafts/{id}/renders`, before proving worker SUCCEEDED, 1080x1350 private PNG, banner selection or MP4.

Supabase DEV migration `20261024180000` is present and service_role schema USAGE is true. No live poster rows remained after cleanup. Do not reapply this migration; the separate original dispatcher 403 is fixed.

## Change in this isolated PR
The test harness previously treated a gateway-source 502/503/504 on a poster *render creation* POST as a terminal RuntimeError. Now it classifies only that endpoint's pre-Function-marker 502/503/504 as an uncertain acknowledgement and invokes existing authenticated, tenant-RLS job reconciliation. The existing logic requires exact shop, poster, requester and revision before using a confirmed job, and never blindly retries an uncertain request. A server-produced 503, 500 or unrelated POST remains terminal.

Offline tests cover each gateway response, error provenance, forbidden retry types, and foreign/duplicate/revision-mismatch records. No live cloud run, permission change or browser secret is part of this PR.

## Remaining gates
1. Inspect GitHub CI for this exact head and preserve existing Python/FFmpeg/frontend/security checks.
2. Diagnose repeated Azure Functions/gateway HTTP 503 and ~60-second latency separately using sanitized Azure runtime logs, readiness/cold-start and backend call timings.
3. Only after reviewed source merge and explicit DEV operator authorization, execute one controlled protected test; require actual poster job insertion, worker success, signed 1080x1350 PNG, banner select, private 30-second MP4, cross-shop denials and cleanup.
4. Do not enable live social posting or SMTP, edit WineShopPOS, or claim this test passed end to end.
