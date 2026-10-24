# Part 2 decisions — 2026-10-23

1. **Separated secrets:** public `social_accounts` has display metadata only; OAuth access/refresh ciphertext, verification state and claim tokens live in `retail_private`. Authenticated browser users have RLS-limited SELECT on public metadata, no INSERT/UPDATE to publish on their own.
2. **Approval-first:** approved-content SHA-256 binds an exact reviewed caption/media/version. Edits invalidate approval. Draft status is never a publish instruction.
3. **Idempotent external writes:** one local logical job and reserved publishing unit, unique shop/account/idempotency key; ambiguous provider calls become RECONCILE, not automatic retry.
4. **Version-aware official integrations:** Instagram Reels require container creation, processing state and separate media publish; Facebook API scope is Page feed only for initial adapter; LinkedIn REST Posts text only initially; YouTube API resumable session initializes PRIVATE by default. No claim that an initialized upload is an uploaded Short.
5. **No silent scope upgrades:** provider privileges require app review and user-granted permissions. The live-dispatch worker remains disabled until explicit approval, media provenance, quota and remote receipts are tested.
6. **Pending-only migration:** P2 social schema is staged under `supabase/part2/pending`, not `supabase/migrations`, to preserve Part 1's pinned migration CI and prevent unapproved hosted application. Review collision/timestamp and disposable SQL negative tests before moving into canonical migration sequence.
7. **Part 1 preservation:** P2 plans do not alter P1 campaign/render usage or renewal/billing. A separate owner-approved publish quota is needed. No Postiz or Razorpay.

## 2026-10-23 — P1 platform admin vs Part 2 OAuth authorization
- P1 Platform Super Admin is for platform operations, **not automatic permission to connect accounts or publish another shop's content**. Social connect, approve and schedule require specific shop membership/OWNER or delegated EDITOR role and fresh explicit reviewed content approval; backend must perform current RLS/role lookup on every action. Preserve P1 `platform_admin` policies and separate subscription quota.
- The 12th **P1** migration `20261023181000_p1_platform_admin.sql` is now canonical; the two later timestamped **P2** pending SQL files must be reconciled/reviewed in migration order before any separately authorized hosted P2 application.

## 2026-10-23 — YouTube connected-channel verification decision

- Consent requests `youtube.upload` for Shorts/video upload and `youtube.readonly` only to verify the linked channel via authorized `channels.list?mine=true`. If the user declines either required scope, does not grant an offline refresh token, or returns zero/multiple ambiguous channels, fail closed rather than guess or silently re-request privileges.
- Keep Google OAuth client secret and all token transport **server-side**; the authorization URL includes only public client ID, exact approved redirect, state and PKCE challenge. Keep provider transport injected/disabled until explicit installation approval. Store resulting access/refresh credentials encrypted through existing tenant-scoped vault/RPC, never in browser storage or provider debug logs.

## 2026-10-23 — Parallel implementation decisions

- **No active OAuth by default.** Both server flags `RETAIL_PART2_SOCIAL_ENABLED=true` and `RETAIL_PART2_OAUTH_ENABLED=true`, active published P2 SQL, private 32-byte AES-256 key/version and reviewed official app secrets are required before backend code can link a real account. The frontend independently gates `VITE_PART2_SOCIAL_ENABLED` and `VITE_PART2_SOCIAL_OAUTH_ENABLED`, but cannot authorize anything itself. OAuth callback is authenticated POST from the SPA for the **same shop OWNER** that began the DB one-time state, not unauthenticated server GET.
- **Browser OAuth hygiene.** Do not persist OAuth codes/tokens; only shop/provider intent may use short-lived tab session storage. Remove code/state from browser history before authenticated callback. Allowlist exact official consent hosts/path.
- **Conservative social quotas, separate from Part 1.** A `retail_private.social_publish_plan_limits` table begins empty, making posting unavailable until owner approves explicit caps. Reserve via service-only per-subscription transaction lock + distinct publish-job PK. An unapproved cap, expired plan, wrong tenant/role or revoked social account denies a reservation.
- **Meta identity is Page-bound.** Standard Facebook Login with server-held secret and DB-CSRF state; one verified authorized Page, content-creation tasks, permission check, and Page-linked IG Professional account identity. More than one Page currently denies rather than silently connecting the wrong one. Live business login mode and token lifespan/refresh remain separate app-specific verification steps. This module does not prove Meta app approval.
- **Provider adapters are not platform app installations.** LinkedIn member OAuth requires explicit OpenID, profile and `w_member_social` permission; current adapter demands scope confirmation and is not registered in deployed OAuth builder. LinkedIn organization posting is not inferred from member authentication. Meta Page/IG modules are likewise unwired. Never assume other shops' platform account control from P1 super-admin privilege.
- **Claim-before-send and reconciliation.** [#146](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/146) stages a service-only one-active-attempt claim protocol and durable pre-network `SENDING` marker; external ambiguous create-post responses MUST NOT be auto-retried. Pending DB SQL is not a running Azure Queue worker.


## 2026-10-23 — Source-only social authoring and CAS release gate
- New `p2_create_social_draft` requires backend-minted UUID, exact active shop role, account/provider and campaign day tenant match, idempotency and future schedule; only creates DRAFT. `p2_approve_social_job` checks exact stored revision/caption/timezone/schedule/media snapshot and campaign day review, stores backend-derived SHA-256 and calls `p2_reserve_social_publish_quota` inside one database transaction. Empty plan caps fail the approval and roll it back.
- No unreviewed video approved: Instagram/YouTube blocked in source SQL until provenance, rights and FFprobe metadata are server-authoritative. Initial Facebook/LinkedIn authoring text-only. `p2_cancel_social_job` only cancels unsent states; never falsely cancels a possibly-sent SENDING attempt or refunds already reserved quota without policy.
- Azure HTTP `/api/social/jobs/{create,approve,cancel}` requires live JWT, shop OWNER/EDITOR, and `RETAIL_PART2_SOCIAL_ENABLED` plus `RETAIL_PART2_AUTHORING_ENABLED`; server service-role RPC never accessible to user JWT. Secrets remain server-only and no actual outbound publishing is activated.


## 2026-10-23 — Social reviewer UX and UUID due-dispatch isolation
- New user-visible social post drafts/approvals exist only behind dedicated UI+API rollout switches; the customer can preview the exact caption, account, date/time and revision, must acknowledge review and cannot directly call Facebook/LinkedIn/Instagram/YouTube from the browser. The server computes approved content digest and enforces role/quota DB CAS.
- Publishing queues contain ONLY canonical UUIDs. Social due scanning does not assume exactly-once Azure delivery; multiple sends are reconciled through private DB CAS claim and durable `SENDING` transition. The adapter does not create a queue or attach a timer/trigger before separate worker/provider approval. Provider token transport remains server-only.
- Initial reviewable social draft form supports LinkedIn member and Facebook Page TEXT only; video providers remain blocked until authoritative rights, media probe, app grants, upload and remote-receipt workflows are complete. Empty publish-plan caps prevent accidental posting even if UI is accidentally visible.


## 2026-10-23 — Context/read secrets and pre-network commit barrier
The P2 worker is denied credentials unless the DB grants a single valid active attempt/claim token and confirms the same shop/account/provider, current OWNER/EDITOR approval, connected account, subscription period and quota ledger. The private SQL RPC can return only AES-GCM ciphertext to service_role, not any browser or public schema; application decrypt uses exact shop/provider/account AAD and known key version with expiry greater than 90 seconds. Current code allows TEXT Facebook/LinkedIn only; video remains denied. Keep `RETAIL_PART2_PUBLISH_WORKER_ENABLED` OFF and do not attach a hosted Azure queue trigger. Social dispatch does NOT proceed to external provider post unless `p2_mark_social_inflight` confirms true, ensuring duplicate messages cannot bypass the durable pre-send fence. Ambiguous provider completion requires reconciliation before retry.


## 2026-10-23 — Confidential RPC transport and immutable draft review
- OAuth and social authoring service-role PostgREST requests must use explicit no-redirect HTTPS clients, allow only canonical Supabase origin on standard TLS port, reject changed response URLs and fail closed with sanitized errors. OAuth RPC responses must be bounded to 64KiB. Regression evidence: #172 and #174, both four-job green before internal merging.
- A draft caption or scheduled time change is a **new revision** requiring a fresh explicit human review; any stale approval digest/revision must fail. Editing must be DB-atomic under live OWNER/EDITOR shop membership and only for DRAFT status with no receipt, attempts or quota reservation. Never mutate a possibly outbound/approved job in place. PR #175 completed 4/4 CI and was merged internally; its staged SQL remains unapplied and frontend/backend release switches remain OFF.

- The same strict no-redirect and exact-origin requirement applies to browser user-JWT based RLS social read proxies, not only service-role writes; #178 adds verified negative tests and bounded responses before the frontend can see metadata. Source-only, rollout remains OFF.

- Retailer delivery health must be derived from RLS-scoped server reads, show only per-shop aggregates and allowlisted status/error codes, clearly distinguish stored provider receipts from actual social engagement, and warn that `RECONCILE` outbound jobs must never be blindly retried. Never expose raw provider errors, bearer tokens or foreign-tenant rows. Implementation #183+#184 are source-only, each four-job green.

## 2026-10-24 — Deliberately inert platform publishing showcase
The social preview gallery uses four offline fixtures: LinkedIn and Facebook text (current initial publishing transport scope), Instagram Reels and YouTube Shorts candidate video **placeholders** (future platform-specific upload transport scope). It imports no publishing API, requires no account, has no live media URL, and is never used as a trusted approval or provider receipt. Only existing verified Part 1 media can be connected when rights and grants pass future backend approval. Banners/poster creation is not duplicated by this Part 2 workstream. All actual OAuth/publish gates remain server-owned and disabled in hosted DEV.

- 2026-10-24 — Media privacy boundary for the clothing example: Preserve the supplied product photograph outside the public RetailGrowthAI repository. The Part 2 test uses description-derived text and three color swatches only, never trademark claims, purported discounts, or invented product availability. Real image-to-campaign inference remains a protected Part 1 task, not a static fixture pretending to be AI.

## 2026-10-24 — Explicit isolated media outbound transport
- Keep Instagram/YouTube transport a separately injected, default-disabled component, not a new auto-registered worker or unreviewed external call. Enforce exact Meta/Google HTTPS paths and standard TLS port before carrying bearer tokens; refuse 30x redirects, bound remote responses and avoid credential-bearing error messages.
- Accept HTTP 308 *only* for YouTube status-only resumable probes; never resume byte upload or re-POST a possibly created remote object from an uncertain acknowledgement.
- Keep the staged Part2 SQL media approval deny-by-default until verified tenant rights/probe/state persistence and approved customer/platform permissions exist. No WineShopPOS or Part 1 runtime modification.

- 2026-10-24 — Credentialed service-role due scanning uses one project HTTPS origin on standard TLS port 443; never follow redirects or admit parser-normalized control characters/nonstandard port authorities. Treat malformed origins as configuration failure before any request.

## 2026-10-24 — AAC audio is mandatory for the initial reviewed MP4 profile
- Initial P2 Instagram Reel/YouTube Shorts media gate only accepts server-attested H.264 video with AAC audio, yuv420p, 1080x1920 and 29–31s duration; missing audio or other audio codecs fail closed at registration and lookup.
- The staged record is **not itself** provider certification; do not enable video approval/publishing until actual stored source byte digest, real FFprobe execution, tenant rights/license evidence and lease-safe provider receipts are bound by trusted backend code. No existing hosted DB migration is rewritten.

## 2026-10-24 — Service-owned byte and FFprobe preflight, separate from rights approval
- The media profile for initial 30-second Reel/Shorts eligibility must derive from backend-owned private bytes and a real bounded FFprobe subprocess; never accept client-supplied codec/length JSON or source SHA as verification. Require a previously established trusted storage receipt hash and check file stability around probe. Reject additional unsupported tracks and out-of-root paths.
- This preparatory module is not callable from authenticated API or an active publish worker, and cannot self-attest commercial rights. An independent explicit license review and job-bound transaction must remain required before enabling any Instagram/YouTube approval.
