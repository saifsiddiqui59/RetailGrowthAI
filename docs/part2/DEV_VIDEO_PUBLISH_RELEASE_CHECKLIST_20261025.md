# RetailGrowthAI Part 2 — DEV Social Publishing Release Evidence Checklist

**State as of 2026-10-25:** `BLOCKED / OUTBOUND OFF`. This is an operator checklist, **not** permission to publish, apply migrations, create cloud resources or change subscriptions.

## Verified source and connected DEV evidence

- Part 2 working branch: `feat/part2-integration`. Internal #297, #299, #301 and #303 were previously merged. Subsequent YouTube 308 → SHA+claim one-shot recovery and strict partial Content-Range were merged before #310. #310 adds disabled read-only remote receipt observation with negative provider tests.
- P2 SQL source: **20 unhosted migrations**, in order `20261023190000` through `20261023191900`, all under `supabase/part2/pending/`. Do NOT copy/apply them to hosted DEV until Coordinator review.
- Independent read-only connected Supabase audit (RetailGrowthAI project `jeearzffnjbvghwjjjrf`, 2026-10-25): `public.render_jobs` present; `public.social_publish_jobs` ABSENT; `retail_private.social_video_uploads` ABSENT. Migration history returned P1 only. WineShopPOS projects were not accessed.
- P1's signed actual Azure FFmpeg 30-second synthetic output and private download are separately verified in [run #40136464084](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40136464084). **This does not prove** P1's Part 2 trusted finalized SHA writer callback or commercially licensed source footage.
- P1 Azure Functions HTTP ingress P0 [issue #249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) is unresolved; no reliable full signed-in retailer → API → poster → Reel acceptance is certified. Requiring a real preflight is mandatory before any live E2E.
- There has been **no authenticated consented Meta or YouTube test-account publication** and no proven social application-scoped provider token/reconciliation in hosted DEV.
- Current Part 2 video factory has six independent server release switches and no default provider transport; the existing deployed text-only worker must not be silently reused.

## Evidence gates (all mandatory, no implied completion)

| Gate | Owner | Required evidence | Current outcome |
| --- | --- | --- | --- |
| G0 — Source parity | Part 2 lead | Exact current Part2 integration SHA, no divergent Part1/Part3 contracts, four successful CI jobs, branch PR reviewed | Source CI only; final main merge reserved for Coordinator |
| G1 — Finalized source media | Part 1 owner + Coordinator | Trusted Part1 FFmpeg successful output callback computes and registers SHA-256 of ORIGINAL private MP4, FFprobe H.264/AAC, immutable path and byte length; current actual output verified twice | **BLOCKED** — adapter exists but callback not installed |
| G2 — Commercial rights | Authorized reviewer | Evidence of rights to stock video, music, images, brand and planned channels; independently reviewed license, restrictions, expiry beyond schedule, verified record tied to exact SHA/revision | **BLOCKED** — no approved real source set |
| G3 — Database migration | DEV operator + Coordinator | Written approved migration plan and target project ID; 20 ordered staged P2 migrations reviewed for P1 collision, RLS/SECURITY DEFINER grants and rollback; backup and disposable negative tests | **BLOCKED** — P2 tables absent on hosted |
| G4 — Publish entitlement | Product owner + DEV operator | Approved per-plan caps configured in source-of-truth P2 publishing allowance; explicit subscription period and quota reservation/refund assertions | **BLOCKED** — no authorized hosted plan caps |
| G5 — Provider identity | OAuth app owner | Approved official Meta/Google application, verified redirect URLs, scopes, app review/live modes, authorized business/Page↔Instagram and channel identity, user consent, encrypted token/refresh rotation and revocation checks | **BLOCKED** — no verified grants/test accounts |
| G6 — Remote transport | Part 2 lead + operator | Meta container READY/FINISHED then distinct media_publish, independent remote media-ID receipt check; Google resumable 308 offset, one-shot CAS, remote video ID and owner-channel private-processing check | **OFFLINE ONLY** — read-only mock observations are not posting |
| G7 — Azure recovery | DEV operator | Explicit cost-reviewed existing/new Functions registration, queue + due timer + poison, safe max retries/leases/outbox, no browser secrets, health alerts and deployment rollback | **BLOCKED** — video worker unregistered |
| G8 — Signed-in canary | Product owner + QA | Consented dedicated test shop/accounts, stable P1 HTTP preflight, approved original upload, 7-day campaign, actual 30s Reel, test Meta+YouTube publish receipts, remote read and RLS negative check, cleanup | **BLOCKED** — G1–G7 and P1 #249 |
| G9 — Main and production | Final Coordinator only | Latest main/Part3 compatibility, exact 4/4 PR + post-merge CI, approved hosted release and budget, independent go/no-go record | **NOT AUTHORIZED** |

## Safe rollout order

1. Preserve `RETAIL_PART2_SOCIAL_ENABLED`, `RETAIL_PART2_PUBLISH_WORKER_ENABLED`, `RETAIL_PART2_OUTBOUND_PUBLISH_ENABLED`, `RETAIL_PART2_VIDEO_ENABLED`, `RETAIL_PART2_VIDEO_WORKER_ENABLED`, `RETAIL_PART2_VIDEO_PROVIDER_ENABLED` as **OFF**. No public publishing route or unreviewed Azure blueprint registration.
2. Final Coordinator first reconciles full Part2 source (including 20 P2 SQL files and post-#310 code) with *current* P1 main and parallel Part3; preserve P1 login, tenant RLS, JWT, subscription ledger, media bucket, FFmpeg fallback and existing static web frontend. Never merge Part2 to main from a worker chat.
3. Obtain separate signed owner approval for DEV SQL G3, APP permissions G5, quota G4, cost G7 and live test accounts G8. The user’s source-development approval does **not** authorize actual third-party posts, production or new paid resources.
4. Take reviewed migration snapshot/backup and apply **only** the exact ordered approved P2 migrations on verified RetailGrowthAI DEV. Inspect migration history and `to_regclass` before AND after. Preserve private `retail_private` schema and negative cross-shop/anonymous/VIEWER tests. Stop on unexpected privilege exposure.
5. Install Part1 trusted original-output finalized SHA receipt on the Part1 owner's branch; verify actual immutable original MP4 bytes, FFprobe and commercial-rights evidence. Reject stale approvals, mutable/cross-tenant source paths and expired rights.
6. Enable official OAuth only for explicitly consented isolated test accounts: prove current Meta Page and IG Professional account identity; prove Google channel via `channels.list?mine=true` and allowed `youtube.upload`/`youtube.readonly`. Encrypt and bind session/token vault by shop/provider/account; test refresh, revoke and wrong-account denial.
7. Configure finite publish limits for the test plan. Prove exactly one quota unit reservation per logical reviewed publish job, same-day revision pin and no refund on an ambiguous potentially sent request. Never charge/refund twice on duplicate queue delivery.
8. Deploy approval-gated video worker only after G1–G6. Run one bounded, disposable, manually reviewed canary **per provider**. Validate original source SHA, account and lease after every outbound action. Never interpret a Meta FINISHED/PUBLISHED *container* as independent final media_publish receipt; inspect final media ID and owner/account separately.
9. For YouTube: start PRIVATE, store encrypted resumable session, persist intent BEFORE binary PUT. After uncertain timeout, send only Google status-only probe; handle 308 next-byte, record one-shot recovery CAS before remaining bytes. On 404/5xx or conflicting 308, STOP/RECONCILE; do not initialize a second session automatically. Verify returned known video ID and channel/processing with read-only `videos.list` when granted, then confirm durable receipt; private processed does **not** imply public Shorts launch.
10. Exercise failure matrix, evidence snapshots, cleanup and operator go/no-go. Only Final Coordinator may authorize next stage and later merge/release.

## Mandatory negative and recovery matrix

| Scenario | Required observation |
| --- | --- |
| Cross-shop ID, different account or invalid lease | No provider request, no media read/write and no new quota reservation |
| Revoked OWNER, Instagram grant, Google channel/scope or expired OAuth | Fail closed prior to any new remote call; uncertain prior writes remain reconciliation |
| Concurrent timers, duplicate queue message or same idempotency key | One durable job/intent, no duplicate provider POST/PUT |
| Edit after approval, changed MP4 bytes, SHA, license expiry, revoked media | Denied before immutable export/upload; old provider intent is not reused |
| Meta container processing, ERROR/EXPIRED, delayed FINISHED | No early media_publish; manual/approved retry only if provably never sent |
| Meta media_publish timeout, response lost or duplicate webhook | Do not rerun media_publish from container status alone; require remote final account-bound receipt |
| Google session created, binary PUT timed out with 308 | Query exact encrypted session with zero bytes; one-shot claim CAS; send exact remainder once |
| Google returned 404, 429, 5xx, invalid offset or quota exceeded | No session reset or blind resend; bounded operator reconciliation with original provider state |
| Stored known Google video ID found but wrong channel or public visibility | Reject remote receipt assurance; never mark internally safe/published |
| Poison message, DB timeout, worker cold start or lost write ACK | Persist private error/poison evidence before ack; no automatic repeat of ambiguous writes |
| Authenticated current-user attack on private RPCs or upload-state tables | Service-only role and RLS deny; no ciphertext, session URI or access token in responses |
| Monthly/daily spend threshold or revoked release switch | Stop new dispatch; preserve existing uncertain records and reconcile safely |

## Required proof artifacts, privacy and rollback

Evidence record for each canary: timestamp UTC; exact source/integration/main SHA and CI run IDs; approved RetailGrowthAI DEV project/app resources (no secrets); written permissions and licensed-asset rights/expiry; plan quota approval; anonymized test shop/account IDs; channel-specific app-grant and review evidence; media hash and FFprobe summary; private DB approval/upload/attempt/reconcile transitions; redacted provider status and **durable** unique remote receipt; monitor/queue result; exact test data deletion and rollback audit.

Never commit OAuth client secrets, service-role keys, AES ciphertext, signed media URLs, private customer content, token-bearing upload Location or raw provider error bodies. Scrub logs and GitHub Actions artifacts.

**Emergency stop:** disable outbound VIDEO/SOCIAL registration switches; suspend *new* due dispatch but retain existing provider claim/receipt records, poison evidence and encrypted sessions for operator review. A potentially completed remote post is **not** safe to retry or automatically refund. Do not delete external posts or revoke customer account permission without separately authorized operator action. Reverse hosted schema only under reviewed backup/migration rollback plan that preserves audit and uncertain receipts. Leave WineShopPOS and PROD untouched.

**Release authority:** Only explicit owner + Final Coordinator DEV rollout record can change these statuses. Source CI, mock video gallery, read-only provider observations or successful P1 worker output cannot replace genuine hosted provider acceptance.
