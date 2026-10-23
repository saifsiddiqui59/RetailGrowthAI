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

## 2026-10-23 — YouTube OAuth provider adapter (#138, source only)

- [PR #138](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/138) was independently reviewed, [all four CI jobs succeeded](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39983761518) on exact head `586b3028`, and it was internally squash-merged **only** into `feat/part2-integration` as `14036a19`.
- New `social_youtube_oauth.py` implements an injected-transport Google server OAuth adapter: exact HTTPS callback, CSRF state and S256 PKCE challenge, least-necessary `youtube.upload` plus `youtube.readonly` scopes to identify the owner's sole channel using `channels.list?mine=true`, refresh-token requirement, token expiry validation and sanitized failures. Mock tests deny invalid grants, ambiguous account identity, bad callback and unsafe transport output.
- **Not live:** No wired Azure OAuth routes, installed Google OAuth client, upload worker, account connection, hosted migration, hosted runtime flag or posted YouTube Short. This is strictly one required provider-adapter foundation. Real OAuth app verification and user consent remain pending.

## 2026-10-23 — Parallel OAuth, UI and publishing-quota milestone (#140–#145)

- Source-only **owner-authenticated OAuth HTTP routes** now exist as `/api/social/oauth/{start,complete,disconnect}`, with strict request shapes, fresh user JWT and OWNER membership checked against shop RLS, one-use SQL callback state, encrypted credential persistence and fixed-target YouTube backend transport. `function_app.py` routes remain **disabled by default** via both `RETAIL_PART2_SOCIAL_ENABLED` and `RETAIL_PART2_OAUTH_ENABLED`. [#140](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/140), [4/4 CI](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39989608921).
- **LinkedIn member OAuth** PKCE, grant/member checks and error redaction added as a separate **unwired** adapter. [#141](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/141), [4/4 CI](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39988964813). Company Page posting requires separate verified author rights.
- **Browser OAuth** connect/callback/disconnect flow uses same-session authenticated POST, session-only non-secret shop/provider context, immediate provider code/state URL scrubbing and allowlisted consent hosts. Only YouTube connection button is offered when *both* frontend flags are on. [#143](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/143), [4/4 CI](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39990395289).
- **Publish quota** source is staged at `supabase/part2/pending/20261023190200_p2_social_quota_reservation.sql`, with DB-atomic per-subscription row lock and unique job ledger. Plan allowances begin **EMPTY**; there is no assumed paid/trial publishing quota, and no P1 campaign/render quota mutation. Negative SQL runs in disposable CI. [#144](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/144), [4/4 CI](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39989971227).
- **Meta Page / Instagram Professional account discovery** adapter verifies granted permissions, one Page with content publishing role, and Page-linked IG account. Multiple Page selection and personal IG are denied, not silently chosen. This adapter is **not wired or approved for a live Meta app**. [#145](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/145), [4/4 CI](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39990623743).
- All five PRs are internally squash-merged **only** into `feat/part2-integration`. Final Part 2-to-main PR is **not ready**. A separate staged publish due/claim/receipt SQL workstream [#146](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/146) remains subject to its exact-head CI and review before any merge.
- **Not complete:** backend provider registration/refresh/revoke, reviewed live app approvals, subscription policy approval, durable live worker/queue connections and actual four-platform media publishing, approval/schedule/cancel UI and end-to-end hosted testing. NO real publishing, P2 hosted SQL, Azure deployment, WineShopPOS or GenAI Galaxy mutation.


## 2026-10-23 — Final checked authoring / durable dispatch source milestone
- [#146](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/146) staged service-role due UUID scan, durable claim/fence/SENDING-before-network receipt and reconcile SQL. [Actions 39991169444](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39991169444) 4/4; merged as `4edcaf07`.
- [#148](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/148) updated four Part2 canonical handoff docs; [Actions 39991591524](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39991591524) 4/4; merged as `4bf22cbf`.
- [#150](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/150) staged `20261023190400_p2_social_authoring.sql`: shop OWNER/EDITOR authorization, idempotent draft create, exact field/revision CAS + reviewed campaign day, same-transaction quota-reserved approval and unsent-only cancellation. **Video media approvals deliberately denied** pending verified rights and probes. Disposable SQL fixture validates real approval, replay/idempotency, second-job quota exhaustion and cancel. [Actions 39992777775](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39992777775) 4/4, merged `ae101b4b`.
- [#152](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/152) guarded `POST /api/social/jobs/{create,approve,cancel}` verifies JWT, live shop role and RLS-selected campaign day/media, timezone-safe wall clock, server-fetched approved hash; service-only PostgREST RPC with no raw error leakage. Independent backend flag `RETAIL_PART2_AUTHORING_ENABLED` defaults OFF; [Actions 39993259311](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39993259311) 4/4, merged `b08f2264`.
- **Integration does NOT imply end-to-end live publishing.** All five P2 SQL sources remain in `supabase/part2/pending` and were never applied hosted. No verified production app grants, actual Instagram/Facebook/LinkedIn/YouTube publishing, independent publication quota plan amounts, live Azure queue/timer/poison workers or media license preflight release. Latest main observed `a1bac624` (newer P1 login/dashboard), requiring later safe review before final coordinator PR.


## 2026-10-23 — Continuation after source-only authoring and database milestones
- [#155](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/155): independently reviewed React `SocialAuthoringPanel.jsx` binds connected Facebook/LinkedIn text accounts to real reviewed campaign day IDs. It shows exact draft/revision, explicitly requires acknowledgement before approval, and allows cancellation only via the authenticated backend; business OWNER/EDITOR role controls visibility while backend enforces authority. `social_read_api.py` now exposes safe RLS-scoped `days` and safe job fields, no provider ciphertext. [4/4 CI](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40006746696); merged as `6094f0ae` to Part2 only.
- [#156](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/156): source-only `social_due_queue.py` reads validated due job UUIDs through private Supabase RPC over HTTPS with redirects refused and bounded response, then enqueues only UUIDs through the separate `retail-social-publish` Azure queue client without provisioning or activating any trigger. Duplicates are safe only with SQL claim/attempt fencing. [4/4 CI](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40007124547); merged as `5b6ebef0`.
- [#158](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/158) proposes disabled-by-default, independently tested Facebook Page text and LinkedIn member text transport with strict URL, provider scope and remote receipt checks. Do **not** mark merged/live until exact CI has passed.
- Still incomplete: owner-approved social publishing quotas, hosted P2 migrations, backend worker credentials/refresh/revocation, Azure due/queue/poison triggers, real Meta/LinkedIn/YouTube app approvals, full Instagram Reel/YouTube Shorts media upload rights/receipts, end-to-end browser security/performance and final reconciliation of `main` `1c59f981`. No customer content was published. All feature flags remain off.


## 2026-10-23 — Verified follow-up: text posting source #158
PR [#158](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/158) completed **4/4** on [Actions #40007522818](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40007522818) and was internally squash-merged into feat/part2-integration as `80805066`. This supersedes any earlier note calling #158 pending. It implements source-only, opt-in Facebook Page text and LinkedIn member text request/receipt checks with uncertainty handled as RECONCILE. **Not yet activated:** real provider publishing, worker connection, hosted P2 migrations, approved OAuth apps, video uploads and independent publishing quotas. Next task is the secure credential loader and server-authoritative job-context worker with test-only provider calls.


## 2026-10-23 — Private dispatch-context milestone after #159
- [PR #161](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/161) stages **sixth** pending-only P2 migration `20261023190500_p2_social_claim_context.sql` with service-only active claim token+2-minute lease gate, approval role/campaign day/subscription and unique ledger matching, connected Facebook/LinkedIn text provider scope and a valid encrypted credential. Returns only AES-GCM ciphertext, never a plaintext token. SQL disposable negative tests verify wrong claim rejection and private ciphertext shape. [Actions 40009962103](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40009962103) **4/4 PASS**, merged to Part2 only as `ff6a5d25`.
- [PR #162](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/162) adds `social_worker_repository.py`: service-only fixed RPC allowlist, no redirects, matching shop/provider/account ciphertext AAD, configured AES-GCM key version/expiry, exact digest/role/account/quota fields for pure approval checks and fail-closed release switch `RETAIL_PART2_PUBLISH_WORKER_ENABLED`. Also patches `social_dispatch.py` to filter private secrets from policy kwargs and **require confirmed SENDING persistence** before any outbound provider call. Offline tests cover successful mock dispatch, changed content, AAD mismatch, wrong tenant, near-expired credential and denied claim barrier. [Actions 40010400504](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40010400504) **4/4 PASS**, merged as `59d1b1ec`.
- **Still not live or complete:** no registered Azure due timer/queue consumer, approved hosted P2 SQL, plan quotas, actual provider credential refresh/revoke, provider OAuth app production grants, Instagram/YouTube video upload/media rights or real social posting. Existing source transports/worker are not an authorized launch.


## 2026-10-23 — Verified OAuth provider registration and private RPC redirect defenses
- #171 fixed one Python exception-class import mismatch in test only, passed 4/4 push CI #40018201041 and was internally merged `a973ed20`; integration head 4/4 #40018611305.
- #172 confidential social authoring RPC redirects and nonstandard ports denied, 4/4 #40018540917, internally merged `819c1947`; post-merge integration 4/4 #40019076415.
- #174 confidential OAuth state/credential RPC redirects and oversized responses denied, 4/4 #40018759345, internally merged `652289ac`. Its post-merge integration run must be verified separately.
- #175 **4/4 passed** #40019171343 and was internally merged `362ffd0b` with a tenth staged-only P2 migration, authenticated `/jobs/revise`, draft editor and stale-approval/foreign-role negatives. Post-merge Part2 [run #40019649987](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019649987) **4/4 PASS**. Real posting and cloud activation remain OFF. Full source/limitations: [checkpoint](CHECKPOINT_2026_10_23.md).

- #178 read-only social metadata now refuses redirects/oversized responses to protect retailer JWT; [CI #40019859294](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019859294) 4/4 and merged `b78cd4d0`. #180 browser mocked end-to-end social review/quotas is an **open PR**, not yet integrated. Both remain source-only; no hosted activation.

- #183 RLS audit/status metadata server-side sanitization, 4/4 [#40020774826](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40020774826), merged `1c0a37bb` (postmerge 4/4 #40021207444). #184 retailer per-shop publishing warnings, 4/4 [#40021069025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40021069025), merged `8dc0d848` (postmerge 4/4 #40021468128). #180 initial Playwright failures traced to an invalid `client.accessToken()` accessor; fixed social workspace and OAuth callback to use the exported `client.getAccessToken()` method, then [run #40022253485](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40022253485) 4/4 passed and merged `870b6334`. Recheck integration after merge. No live provider/network posts enabled.
