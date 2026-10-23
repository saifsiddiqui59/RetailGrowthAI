# Part 2 — Social Integration & Automated Publishing

Date: 2026-10-23. Owner: Part 2 Development Lead. Integration branch: `feat/part2-integration`.
Baseline: `main` at `1ef7271004666c13a13cf627ed47460397799edc`; Part 1 subsequently continued independently.

## Verified existing reusable Part 1 functionality
- Supabase Auth, shop roles OWNER/EDITOR/VIEWER, RLS, private media, saved seven-day campaign drafts, render jobs.
- Azure Functions HTTP, durable DB outbox, Azure Storage Queue workers, 30-second licensed-media FFmpeg private renders.
- DEV trial/subscription campaign+render reservations are server-owned; **publishing has NO approved quota plan yet**.
- Existing app/API/frontend hosted for Part 1; Part 2 code has not been deployed to it.

## Implementation ledger (branch-owned, not production)
- `feat/p2-provider-adapters` PR #108: official request shapes for Facebook Page text, Instagram Reel container / status / publish, LinkedIn Posts text and YouTube private resumable INIT. Offline mocks; no outbound calls.
- `feat/p2-data-security` PR #110: prospective social account/job/audit and internal credential/OAuth-state/attempt/quota schema. **SQL in supabase/part2/pending/, deliberately not in live migration path**. No hosted DB changes.
- `feat/p2-publishing-runtime` PR #112: AES-GCM private token envelope, CSRF state/PKCE primitives, DST-safe scheduler, denied-on-ambiguity retry policy. Not wired to a provider/queue.
- `feat/p2-social-ui` PR #114: disabled-by-default `/social` account/scheduling preview and read-only authenticated API client. No OAuth buttons, job submission or publish claims.
- These are component foundations only. None of the 12 work areas is fully end-to-end finished.

## Release truth
No P2 connection to an actual provider, app review, hosted SQL, deployed Azure function, queue, remote post, live quota charge or E2E result. Never claim otherwise. No Postiz, Razorpay, WineShopPOS or GenAI Galaxy changes.

## Planned compatibility with Part 1
Do not alter `docs/INTERFACES_V1.md`, existing Part 1 endpoint payloads, frozen migration history, P1 campaign/render quota ledger or published deployment. Part 2 endpoints will be under `/api/social/*` and use existing Supabase verified JWT and shop membership, plus separate publish-specific quotas approved later. Tenant-owned storage/object IDs and exact approved content digest bind publishing jobs. A provider remote receipt never substitutes for durable job status reconciliation.

## 2026-10-23 — Verified internal implementation and main refresh (latest; supersedes initial ledger)

The following isolated Part 2 PRs were **internally squash-merged into `feat/part2-integration`**, not main:

| PR | Scope | Pre-merge four-job CI | Internal merge |
| --- | --- | --- | --- |
| [#108](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/108) | Official provider request builders | [39973096649](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39973096649) PASS 4/4 | `5598acc9` |
| [#110](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/110) | Pending tenant-safe social SQL | [39974189120](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39974189120) PASS 4/4 | `6d1ac524` |
| [#112](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/112) | OAuth vault, state/PKCE, DST scheduler | [39974594552](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39974594552) PASS 4/4 | `1f1eff99` |
| [#116](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/116) | Part 2 architecture/research docs | [39975095577](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39975095577) PASS 4/4 | `f4990f93` |
| [#114](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/114) | Social preview route/client/UI | [39975286482](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39975286482) PASS 4/4 | `d7bb2de8` |
| [#118](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/118) | Exact-content approvals/media preflight | [39975951078](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39975951078) PASS 4/4 | `e8d863ce` |
| [#119](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/119) | Default-off authenticated social read API | [39976295966](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39976295966) PASS 4/4 | `4c936f65` |
| [#123](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/123) | Replay-fenced dispatcher protocol | [39977246358](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39977246358) PASS 4/4 | `6815287a` |

Also reconciled current Part 1 `main` `302ee4adf47800ddf6d3e4b84372fe65a65d7fbe` into integration through genuine two-parent merge commit `55470665249ae4a7faf8ca587aaa8f76373afa8a`. The merge retained the modern P1 overview, Subscription page/metrics, tests and `/social` navigation, and verified all 290 paths in the generated tree. **Integration-head CI after this documentation must be checked independently.**

### Delivered vs remaining capabilities

| Area | Source status | Not yet done |
| --- | --- | --- |
| OAuth / disconnection | AES-GCM token vault, state & PKCE primitives | Real provider authorization/code exchange; atomic state consume, refresh, disconnect, token revocation |
| Instagram | Reels container/status/publish request shapes | Provider transport, media hosting/processing, account checks & App Review |
| Facebook | Page FEED text request shape | Actual Page OAuth/ownership verification; photo/video/Reels APIs |
| LinkedIn | Versioned REST text-post request | Actual approved access, organization/member token flow, media posting |
| YouTube | Private resumable session initialization | Video byte upload, processing reconciliation, Shorts classification, OAuth verification |
| Scheduling | IANA timezone, DST and retry primitives | Durable DB approved schedule transactions, queue/timer activation |
| Queue/reconciliation | Fenced pure dispatch protocol | DB claim RPC/lease/outbox/poison, remote provider lookup, queue trigger |
| Frontend | Disabled-by-default `/social`, account metadata, scheduling preview | Real OAuth controls, approvals, edit/cancel/unschedule interactions |
| Tokens/isolation | RLS SELECT-only prospective tables, ciphertext vault, secure read route | Disposable SQL RLS negative verification; live DEV grant validation |
| Media/content review | Exact approved digest and conservative FFmpeg media preflight | Revocation on every campaign edit, post-approval UI, provider-specific supported media |
| Quota | Isolated pending publishing ledger proposal, dispatch requires reservation | Subscription-based atomic publish quota units + defined owner-approved plan limits |
| Testing | Four-job CI for component PRs; Python+Node unit denials | Hosted migration, mocked full-browser publish journey, real provider/queue E2E |

**Not implemented:** real account connection, external publish, live scheduling, hosted SQL, actual publishing quota, provider access approval, Azure deployment. Final PR to main is **not ready**. No WineShopPOS / GenAI Galaxy / Postiz / Razorpay modifications.

## 2026-10-23 — Final source-hardening correction checkpoint

- Internal [PR #129](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/129), **4/4** [Actions #39978367904](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39978367904), merged `16490d1e`: exclude provider Authorization headers/signed media bodies and OAuth state/PKCE verifier from automatic object debug representations.
- Internal [PR #130](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/130), **4/4** [Actions #39978776724](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39978776724), merged `65f52a9c`: pending SQL adds provider/revision and same-shop/actual-provider account composite FK; prevents mismatched connected accounts and makes pure approval digest inputs persistable.
- Important: these are source changes only; the pending SQL was **not applied**. No actual OAuth connect or provider publishing flow is complete. The two flag-gated social routes remain disabled in hosted DEV. Complete local SQL negative tests, durable claim/quota integration and official app access before considering a final PR to main.

## 2026-10-23 — Additional OAuth lifecycle/persistence implementation (newest)

All PRs target `feat/part2-integration` and were self-reviewed and internally merged, never merged to main:

| PR | Verified 4/4 CI | Internal merge | Contents |
| --- | --- | --- | --- |
| [#131](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/131) | [39981003583](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39981003583) | `6dc76aed` | OWNER-bound OAuth start/callback/local disconnect, one-use state, scope and identity checks, encrypted tokens, mocked provider tests |
| [#133](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/133) | [39981284686](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39981284686) | `1f23312e` | Service-only OAuth RPC repository; HTTPS, fixed RPC allowlist, encrypted payloads, sanitized errors and negative tests |
| [#132](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/132) | [39982030923](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39982030923) | `537594ab` | **PENDING** atomic OAuth state issue/consume, transactional encrypted connect and disconnect SQL, cross-shop/grant/replay tests executed in **disposable** Supabase |

A separately confirmed integration commit `5c0f1c83` passed [Actions #39979248011](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39979248011) **4/4** before the new OAuth PRs; do not represent it as the final commit's CI.

**Integration gaps still block release:** adapter-level OAuth identity/code exchange must be implemented and verified for each platform, actual HTTP callback/routes must be connected to the service, credentials refresh and provider-side revocation must be implemented, and the staged SQL must be reviewed and separately approved before hosted application. P2 publishing queues, durable claim/reconciliation, plan publish quotas, full media upload/publish flows, approvals UI and hosted E2E are **not complete**. No live customer content posted or hosted changes made.

## 2026-10-23 — Latest Part 1 platform-admin reconciliation, VERIFIED

- Part 1 `main` moved to `33ee5769068a3c5abf13c5ece531b81353195911` via owner/team [PR #134](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/134). This introduces Platform Super Admin with the **existing** RetailGrowthAI auth, a new P1 source migration `20261023181000_p1_platform_admin.sql`, platform admin page and negative tests.
- The Part 2 lead created a genuine two-parent integration merge `0782967fb47da390bc3f3a291f35d4bd2cacc791`, parents `e5f516b39b9e871991efec45aacfc9b918548830` (Part 2) and `33ee5769068a3c5abf13c5ece531b81353195911` (P1 main). Reviewed overlap only `frontend/src/App.jsx` and `.github/workflows/frontend-bootstrap.yml`; preserved both P1 `/platform-admin` and P2 `/social`, P1 platform-admin SQL denial checks and P2 staged disposable social SQL checks; verified **all 306 paths** from both source trees remained.
- Combined post-merge [GitHub Actions #39983215884](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39983215884) **4/4 SUCCESS** on exact `0782967f`: Python/API, frontend/browser, FFmpeg and disposable Supabase security jobs all green.
- P1 platform admin is NOT a substitute for active shop OWNER approval to connect a social account or publish a customer post. New P1 migration is canonical in source; Part 2 proposed `20261023190000` and `20261023190100` files remain under `supabase/part2/pending` and were never applied to hosted Supabase.
- **No final Part2→main PR**, live OAuth/publishing, hosted P2 schema application or production permissions. The next work is remaining OAuth network/routes, publish orchestration/quota, approvals UI and end-to-end tests—not additional Part1 rebuilds.
