# Part 3 full integration source-qualification record — 2026-10-23

**Branch:** `feat/part3-integration`; **final draft PR:** #125 into main — Coordinator only. This qualification file is a source-only integration CI trigger and records exact PR evidence. No hosted deployment.

## Reviewed internal merges and CI evidence

| Internal PR | Scope | Exact check runs | Result |
|---|---|---|---|
| #109 | WAN 2.7 provider, async T2V/I2V, prompt/limits | Dedicated #39975248007 2/2; existing #39975248169 4/4 | PASS, merged to Part3 |
| #115 | FFmpeg-default premium chooser, no billing | Dedicated #39975257823 2/2; existing #39975257898 4/4 | PASS, merged to Part3 |
| #113 | premium job scaffold, zero-default shared-ledger SQL proposal | Dedicated #39975690745 2/2; existing #39975690715 4/4 | PASS after fixing isolated provider mock and unreviewed-migration conflict, merged to Part3 |
| #122 | no-redirect, bounded, verified private Wan MP4 output importer | Dedicated #39976479632 2/2; existing #39976479459 4/4 | PASS, merged to Part3 |
| #126 | vendor official output OSS hostname compatibility fix/regression | Dedicated #39977762809 2/2; existing #39977763357 4/4 | PASS, merged to Part3 |
| [#188](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/188) | worker-only Wan success URL, lease-fenced private completion + expiry guards | Dedicated [#40027754515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40027754515) 2/2; Part 1 [#40027754811](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40027754811) 4/4 | PASS, merged to Part3 as 7f31f0ba |
| [#189](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/189) | offline optional 30-second licensed Wan clip FFmpeg composition, default-free fallback | Dedicated [#40028636020](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40028636020) 2/2; Part 1 [#40028635956](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40028635956) 4/4 | PASS, merged to Part3 as 0680b887 |
| [#193](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/193) | REAL offline FFmpeg 30s synthetic composite: two independently encoded clips, licensed fixture audio, pixel verification | Dedicated [#40029556625](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029556625) 2/2; Part 1 [#40029556607](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029556607) 4/4 | PASS, merged as e0bda65 |
| [#194](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/194) | disabled JWT premium create/status/private download HTTP adapter | Dedicated [#40029862503](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029862503) 2/2; Part 1 [#40029862536](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029862536) 4/4 | PASS, merged as 4e8a830 |
| [#195](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/195) | explicitly APPROVED day mandatory before premium credit reservation, Python + staged SQL | Dedicated [#40030136015](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030136015) 2/2; Part 1 [#40030136005](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030136005) 4/4 | PASS, merged as 18b5794 |
| [#196](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/196) | disabled isolated premium UUID-only Azure queue, CAS outbox and poison source scaffold | Dedicated [#40030452145](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030452145) 2/2; Part 1 [#40030452191](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030452191) 4/4 | PASS, merged as 62fb30b |
| [#198](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/198) | exact lease-private output receipt + ffprobe local-only protocol guard | Dedicated [#40031597546](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597546) 2/2; Part 1 [#40031597516](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597516) 4/4 | PASS, merged as 62100f0 |

The twelve internal feature PRs merge only into `feat/part3-integration`; the final PR #125 is open as **DRAFT**, not merged into `main`.

## Default-safe integrated behavior

- Current Part 1 `RenderStatus` and FFmpeg 30s Reel remain unchanged. The new PremiumVideoPanel is mounted AFTER standard render and its activation props default to **false**, so the premium mode is visible as an unavailable alternative but cannot launch paid requests.
- Wan 2.7 T2V/I2V adapter is gated by disabled-by-default server flag, trusted Singapore Alibaba Workspace origin, valid server key, and nonzero explicit per-job USD ceiling. Provider submit is async and only returns safe task ID/status.
- Source-only server premium coordinator checks tenant JWT/RLS campaign/day membership, image rights, disallowed inputs, and idempotency; worker marks uncertain task creation UNKNOWN instead of blindly re-posting a billable request.
- The source-only proposed SQL in `azure-functions/campaign-api/part3_sql/` extends the EXISTING `shop_subscriptions`/`shop_usage_reservations` rather than adding a second billing system. Premium allocation defaults to 0. The proposal is **not** in executable `supabase/migrations/` and has **NOT** been applied to hosted DEV.
- Provider output private importer allows documented `dashscope-a717.oss-accelerate.aliyuncs.com` URLs and reviewed matching host shapes, but rejects arbitrary URL/redirects/local IP and invalid MP4 bytes/codecs/duration. Uploads use existing tenant-private storage and require a lease-token-checked completion callback. No external provider URL is returned to browser.

## Incomplete / release-blocking tasks

1. Coordinator rebase/merge review against newer Part1 main commits, especially shared React campaign UI, workflows and canonical docs. No Part2-owned files touched.
2. **Promote/add new DB migration only under explicit approval:** review staged SQL, authoritative migration history, negative foreign tenant and race/rollback/credit test evidence, stable dollar exchange/cost pricing; no hosted schema changes today.
3. Wire private premium create/status/download HTTP API, transactional premium outbox/queue trigger/poison/recovery, service-role CAS claim/lease/finalization RPCs and registered worker, so tasks progress end-to-end using UUID-only messages. None are live yet.
4. Implement safe full provider result retrieval and pass **only** valid signed provider data from the internal poller into importer. Confirm expiry handling and no duplicate provider charge on UNKNOWN. Add cancellation/cost reconciliation and restricted production error codes.
5. Compose multiple provider clips into 30-second campaign using current FFmpeg with explicit free fallback, optional provider substitution only after fresh price/rights approval, and independently licensed music.
6. Owner to approve paid commercial API workspace, data-region/rights and image consent, per-tenant monetary ceilings and one strictly bounded paid DEV smoke before enabling customer premium.
7. Real browser Auth with cross-tenant denials, provider clip MP4/ffprobe and signed download under approved fresh test identities. No live Wan invoice/task/media exists, no paid subscription or checkout activation.

**DO NOT** mistake mocked CI or draft final PR for feature launch. Retain `RETAIL_PREMIUM_VIDEO_ENABLED=false` and no positive premium allowance until the tasks and separate approvals are complete. No WineShopPOS or GenAI Galaxy mutation.

## 2026-10-24 continuation — new source-only milestones

- #188 implements `AlibabaWanProvider.poll_private` returning signed output only to the privileged importer and `PremiumPollCompletion` with an existing database lease/tenant/reservation *contract*, not a hosted implementation. It rejects expired/duplicate Alibaba `Expires`, wrong claim/task, unsafe URL, invalid MP4 and stale finalization. No provider URL enters a customer response.
- #189 adds `video-engine/premium_compose.py`, a no-shell FFmpeg/H.264/AAC 30-second join for 2-8 **already imported** licensed/rights-verified private Wan clips. It does not modify the existing standard image renderer; `select_render_mode` is strictly free-first. Music must pass existing local audio rights/codec validation; no royalty-free material is bundled.
- Tests on the exact PR heads are green as recorded above. Private-completion test uses mocked provider/storage DB; new compositor FFmpeg command is unit-tested with fake clip commands, with real rejection of spoofed invalid MP4; **no live provider video or actual 30-second Wan composite E2E was run**. This is not user-ready.
- Remaining **release blockers**: reviewed/applicable Supabase schema + atomic service-role RPCs, durable Azure premium queues/worker/poison/recovery, JWT-authenticated premium API/download, approved provider/region/rights/credit/rate policy, real signed frame/image consent, actual FFmpeg mixed stock + AI overlays/CTA, cancellation/provider reconciliation, real rendered composition/hosted E2E, final Coordinator merge. Keep all premium flags and allowances OFF. No external social publishing work or WineShopPOS changes.

## 2026-10-24 further source-only continuation (PRs #193–#196)

- #193 runs an actual **local/CI** FFmpeg composite from two independently generated 15-second synthetic 720p H264 clips and a locally generated test tone. Independent ffprobe confirms 30s H264/AAC; decoded red at 5s and blue at 25s proves correct order. It is NOT paid Wan output or production licensed soundtrack.
- #194 creates `premium_http.PremiumHTTPBoundary` for JWT-scoped create/status and lease-name-checked private signed download. Not registered in live Azure Functions. Existing Part1 v1 routes unchanged.
- #195 fixes a human approval vulnerability: Part1 day generated with `review_status='DRAFT'` can no longer reserve paid Wan credits. Source controller and un-applied proposed SQL require exactly `APPROVED`; actual Part1 authorized DRAFT->APPROVED workflow remains to be developed/reviewed.
- #196 source-only `retail-premium-video` queue adapter, CAS outbox dispatcher, poison fingerprinting and reconcile sequence; all disabled by default, **no Azure queue provisioned**. Real service-role SQL RPCs and registered queue/timer triggers still unimplemented.
- Final integrated verification after documentation commits must be checked separately, rather than assuming prior PR CI proves exact updated integration HEAD.
- Blocking end-to-end work: atomic reviewed/approved new migration, actual service-role repository/RPCs for claims/outbox/lease/finalize/credits, Azure premium function registration/queue/poison and safe UNKNOWN reconciliation; branding/CTA mixed-media timeline; real JWT/tenant hosted E2E, licensed provider output and protected secrets, owner vendor spend/legal/data-region approval and one bounded paid DEV test. Keep Part3 OFF and PR #125 DRAFT; never merge to main from Part3 Lead.

## 2026-10-24 latest verification and security fix

- Immediately preceding #198, the exact integrated branch head `f88138fe678973240bf99207ec5277140485f4c7` completed dedicated P3 CI [#40030842866](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030842866) **2/2** and standard CI [#40030842790](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030842790) **4/4**, **attempt 2**. The initial security job failed before SQL tests because GitHub runner port `54322` was occupied; a rerun passed with all Supabase SQL negative tests intact. Do not cite attempt 1 as a clean pass.
- [#198](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/198) adds a strict equality check for `{shop}/renders/{job}/{lease}.mp4` provider upload receipts (prevent same-prefix substitutions) and `ffprobe -protocol_whitelist file` for imported files. Regressions proved unsafe paths cannot reach database finalization, and file-only probing prevents remote protocol use. All 6 exact PR-head checks passed before self-merge.
- The merged branch head will change as this documentation lands; verify new exact HEAD CI separately. The live provider/DB/Azure/rights/cost release gates remain **UNMET** and premium flags remain off.

## 2026-10-24 — Cancellation workstream and exact PR evidence
- [#226](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/226) added a disabled-by-default source-only `PremiumCancelBoundary`, with independent offline Python tests ensuring only user-authorized QUEUED/pre-submit jobs can request an atomic release of the existing reservation. Revoked/foreign users, SUBMITTING/PENDING/UNKNOWN, forged receipts and lost cancel-vs-submit CAS races never receive cancellation success or assumed credits. Internally merged `bccd6e0` after [dedicated Part 3 #40076805919](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805919) **2/2** and [full standard #40076805911](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805911) **4/4**.
- This is **not** executable cancellation: no service-role transactional `cancel_unsubmitted_atomic` SQL RPC, HTTP route, hosted negative test or live credits were changed. See `azure-functions/campaign-api/PART3_CANCELLATION_HANDOFF.md`. Formal vendor/data/rights/pricing/DEV spend approvals, migration, queued worker, real end-to-end testing and Coordinator-only main integration remain outstanding. Provider flag OFF; PR #125 stays DRAFT.
