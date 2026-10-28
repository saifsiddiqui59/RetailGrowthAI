# Issue #249 — Separate worker-only Python imports from HTTP indexing (2026-10-28)

**Status:** SOURCE-ONLY RISK REDUCTION; NOT AN AZURE HTTP FIX. The original Flex backend failed the actual matched-route DEV 20-sample run [#40691854364](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40691854364): 9/20 genuine ~61-second unmarked HTTP503, while the existing Free SWA Node preview returned 20/20 marked expected 401. Python's actual cause remains unknown. Do not reclassify this as a cold-start diagnosis.

## Narrow safe change

The original `azure-functions/campaign-api/function_app.py` eagerly imported planning, recovery, poison, notification, poster worker-only modules **and authenticated HTTP/storage/Feature3 API modules** while Azure Functions indexed the HTTP routes, including when the scheduled notification and poster options were disabled. This candidate retains only `json`, `os`, `azure.functions` and sanitized request diagnostics at module import time; tenant/queue/API modules load when the authenticated request or their respective workers run. The source change keeps existing route decorators, settings checks, signed JWT/RLS HTTP boundary, queue trigger names, durable job semantics, limits and error paths intact, and moves those imports into the specific queue/timer functions that actually invoke them:

- `HTTPAPI`, tenant/JWT, queue, poster and Feature3 API/store imports only on a dispatched HTTP request; no authorization rule is skipped.
- `planning_worker` and `AdminStore` only on a planning queue message.
- `recovery_runtime` only during recovery or poison execution; unused `dispatch_outbox` top-level import removed.
- `notification_store` and `notification_worker` only **after** the opt-in notification flag is true.
- `poster_admin`/`poster_queue` only inside enabled poster worker/timer handlers.

A new `tests/infra/test_p0_249_lazy_worker_imports.py` parses/compiles the exact Functions source, requires the four-module lightweight indexing allowlist, rejects worker-only top-level imports or leak into HTTP auth handlers, requires the original registered trigger decorators and checks fail-closed disabled-feature gates before imports. It is **source-level** regression verification; CI must separately run the existing Python and FFmpeg integration suites. This change does not remove large FFmpeg/ffprobe binaries from the deployed ZIP, split HTTP and worker scale groups, or change host/Flex memory/instance settings. Benefits to startup time are **not measured**.

## Owner/coordinator handoff

1. Verify full four-job PR CI on **exact final head**. Merge only through the integration coordinator after current-main conflict review; check separate postmerge four-job CI. This branch contains no workflow edit or hosted setting change.
2. If source is accepted, obtain **separate scoped DEV deployment approval** (existing app only). Review deployed ZIP identity and rollback; do not alter any Azure hosting plan, paid units, tenant schema or customer origin without independent authorization.
3. Run identical protected 20+20 anonymous fixed campaign GETs on original Flex and existing Free SWA Node, including warm/concurrent/post-300s-idle, plus preferably longer repeated sampling. Measure application marker, 503 count, TLS/TTFB and descriptive all-completed p95. Never claim p99 at n=20; do not retry POST/PATCH.
4. Investigate host/worker **causal** platform ingress and startup evidence over the actual failed 2026-10-28 12:57–13:10 UTC test window. Prior detector table counts and minute-bucket traces cannot identify 503 source. If unavailable, state platform telemetry blocker rather than mark repaired.
5. Separately gated signed OWNER/EDITOR/VIEWER/foreign/revoked two-shop real licensed private poster→30s queued H.264/AAC MP4→signed download/cleanup is outstanding. No GPU, social/publishing, PROD or WineShopPOS work is included.

**GitHub Issue status discrepancy:** the live GitHub issue was found `closed` on 2026-10-28 (owner event 12:55:24Z), even though the last verified 9/20 HTTP503 evidence and required closure acceptance are unresolved. Do not interpret administrative closure as a passed reliability test; coordinate issue state with owner rather than silently asserting OPEN.
