# Issue #249 — bounded DEV Y1 public-only signed read shadow activation

**SOURCE PREPARED ONLY. Not merged, deployed, activated, or accepted.** Original Flex gateway defect remains open. The isolated DEV Y1 Python 3.12 Function App already serves a read-only original campaign GET shadow with two GET functions and verified missing-JWT 401s, but the activation flag and real Supabase credentials have remained absent.

## Motivation and exact scope
- Next increment after the hosted Y1 20/20 health and 12/12 missing-bearer campaign denial: exercise the unchanged original `SupabaseJWTVerifier` + `HTTPAPI` + `TenantStore` with the **same real DEV Supabase project**, without giving Y1 an elevated service-role key or adding any write/timer/queue route.
- Connected DEV project `jeearzffnjbvghwjjjrf` was verified `ACTIVE_HEALTHY`. Only its public `https://jeearzffnjbvghwjjjrf.supabase.co` and active `sb_publishable_...` key are eligible for a temporary test; the publishable key is already present in this repository's earlier DEV synthetic-auth GitHub workflow and was verified against its current connected-project API. Never copy a `sb_secret_` or `service_role` key into Azure Functions app settings.
- The trial touches **only** the tagged isolated `rgai-dev-y1-p0249-d4e5ddbd`, never original `rgai-dev-functions-d4e5ddbd`, WineShopPOS, PROD, GPU, storage queues, media jobs or frontend routing.

## Protected implementation
- `ops/p0249_y1_public_shadow_trial_guard.py` enforces exact existing DEV subscription/region/tags/site/plan and unchanged FC1, exactly the two expected indexed HTTP functions, and checks that ALL THREE target app settings are initially **absent** before it writes a run-bound non-secret marker to disk.
- A deliberately explicit, owner-authorized, **manual `workflow_dispatch` only** (never on push/merge), main-only protected workflow `.github/workflows/p0249-dev-y1-public-shadow-bounded-once.yml` sets ONLY `RETAIL_SUPABASE_URL`, `RETAIL_SUPABASE_PUBLISHABLE_KEY`, and `RGAI_P0249_READONLY_SHADOW=true` in the isolated Y1. A configuration change restarts Azure Functions; the workflow allows a bounded reinitialization delay before its actual anonymous/malformed-token negative GETs. It never creates new cloud resources, grants roles, edits GitHub secrets, writes Supabase SQL, or changes original Flex.
- Both the test job's `EXIT` trap and **a separate independent OIDC cleanup job** recheck the run-bound marker and remove only keys that were absent before the test AND whose current values exactly match the trial. If a new actor alters a setting, cleanup stops rather than destroy their value. **An entire workflow cancellation or cloud outage can still prevent cleanup**; watch the run, verify restoration and use carefully scoped manual commands if needed.
- The 16-request GET-only negative/health sequence checks handler-marked HTTP401 for no/malformed JWT and handler-marked HTTP200 for health, plus 18-second response cap, with no JWTs in logs. The capability is NOT demonstrated until the verified actual Azure run is complete. The temporary flag is restored to OFF after the test.

## Not yet validated / gate
This temporary public-only activation test is **not a positive signed JWT** test and does **not** prove active two-shop membership/RLS, real customer authorization or complete API migration. Existing local source PR #934 exercises true original JWT/JWKS/HTTPAPI/TenantStore with locally simulated PostgREST only. A separate authorized hosted test with two disposable, nonprivileged signed DEV users and current real RLS remains necessary before a permanent API cutover. Do not copy a service-role key into Y1, point the frontend at Y1, expose queue/timer workers, or mark original #249 resolved.

`.github/workflows/**` changes and DEV configuration need an independent affected-lead/human security review even if source CI passes, per `AGENTS.md` and `docs/FEATURE_SELF_MERGE_POLICY_20261031.md`. Owner allowed a bounded DEV trial but this does not waive independent review. No changes were run in Azure while preparing this PR.

Microsoft docs: https://learn.microsoft.com/en-us/azure/azure-functions/functions-app-settings ; Supabase publishable key and per-user RLS: https://supabase.com/docs/guides/getting-started/api-keys .

## Additional real signed, disposable DEV users (reviewed trial only)

Within the **same bounded temporary flag activation window**, `tests/e2e/p0249_y1_signed_auth_shadow_once.py` uses the already-existing protected DEV GitHub Actions `RETAIL_SUPABASE_SERVICE_ROLE_KEY` **only inside the runner** to create two isolated disposable email-confirmed Auth users. It signs in via the ordinary publishable-key password-grant endpoint and forwards each resulting genuine Supabase-issued JWT **only to the exact existing Y1 GET shadow**. For users with no membership/campaign, the unchanged original server-side JWKS verifier and PostgREST TenantStore should return **handler-marked HTTP404**, not 401/503; a forged signature must return handler-marked 401. The script checks a genuine asymmetric JWKS is available before account creation, never prints passwords/JWT/service key, creates no shop/campaign/membership or media, and invokes the existing exact-prefix Auth Admin cleanup in `finally` (also on partially failed create via its helper). If cleanup is uncertain, the run fails and reports manual cleanup as necessary. **An abruptly killed runner could still leave an inert disposable account**, so the protected operator must review the execution and cleanup record.

These 2 real signed Auth users are **not** the later **two distinct active shops** needed for positive RLS authorization parity; do not mark hosted two-shop acceptance from this step. The service-role credential is never written to Y1 app settings, source code, stdout or artifacts. User authorization to use synthetic DEV test accounts does not bypass the independent review for the privileged GitHub workflow.

## 2026-11-15 — automatic-activation risk removed (source-only)

Security review of PR #939 identified that its earlier `push` condition could activate the temporary appsettings merely because a merge commit had a matching title. The workflow is now **strictly manual**: only an intentional `workflow_dispatch` on `main` with `YES-Y1-DEV-PUBLIC-SHADOW-BOUNDED` can reach the protected DEV preflight, and the three-setting rollback gate remains unchanged. An offline regression rejects any workflow push trigger or commit-message activation logic. This change itself **does not execute** the trial or prove hosted JWT/RLS parity. Independent review and exact-head CI are still required before merging/dispatching the privileged workflow.

## 2026-11-15 — genuine signed Auth helper supports modern opaque secret keys

The original disposable Auth helper used `Authorization: Bearer <key>` for both legacy JWT `service_role` and modern opaque `sb_secret_` credentials. Current Supabase guidance requires `apikey` (not a bearer token) for opaque secret keys. The helper now sends **only `apikey`** with `sb_secret_`, retains `apikey` plus Bearer for a correctly shaped legacy JWT, and rejects invalid key classes. The existing exact-prefix user-create/sign-in/cleanup workflow benefits from this fix; added offline regressions for both credential types. The privileged key remains only in the protected test runner, never in Y1 appsettings, source, logs or artifacts. **Not a live Auth trial or authorization to enable Y1.** See [Supabase API-key migration](https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys).

## 2026-11-15 — bounded cleanup and two-shop seed safety findings

- After an uncertain Admin-create acknowledgement, the source helper now looks up the exact `rgai-p0249-jwt-*` disposable email over a **maximum of 10 paginated 100-user pages** (instead of first page only), denies ambiguous/invalid pagination, and deletes only the exact returned UUID. Tests cover an account on page two and fail-closed invalid pagination. If the bound is exhausted, the workflow fails for operator review rather than falsely logging successful cleanup.
- Verified **read-only** against current RetailGrowthAI DEV PostgreSQL catalog: `public.campaigns` has an `AFTER INSERT` `campaign_job_outbox` trigger and a `BEFORE INSERT` subscription reservation trigger; `shops` also bootstraps membership and trial subscription. Therefore **do not casually insert live two-shop campaigns** for Y1 positive JWT/RLS tests: doing so can queue work and reserve usage. The current protected #939 trial deliberately creates only disposable Auth identities, no shops/campaigns. Positive two-shop GET200 and cross-shop 404 need a separately reviewed no-worker fixture strategy with exact cleanup, not a skipped or falsely asserted acceptance check.

## 2026-11-17 — fail-closed exact synthetic Auth identity on cleanup

Code in the **existing** trial PR #939 now rejects a mismatched Admin-create response `email` before it attempts sign-in. For both normal deletion (known returned ID) and uncertain-create-ACK recovery (bounded exact-email pagination), the cleanup helper requires a marker ending with precisely **16 lowercase hex digits** generated for this one run. Before sending **any** privileged DELETE, it independently GETs `/auth/v1/admin/users/{user_id}` and verifies **both** the canonical returned UUID and `email == marker + "@example.invalid"`; any mismatch fails closed for manual review without issuing DELETE. Offline tests cover known-ID valid cleanup, wrong email, wrong ID, missing ID, malformed marker, mismatched creation identity, and two-page uncertain-ACK lookup.

**JWT lifecycle caveat:** Supabase user deletion does **not** cryptographically revoke previously issued JWT access tokens. The two disposable users never receive shop memberships, campaign records or privileged roles; tested JWTs are never logged/persisted. Full signed two-shop authorization, runtime session-revocation guarantees and any live commercial API acceptance still require separate review/tests. The shadow stays disabled; no hosted Auth creation, Azure appsettings modification, deployment or cutover has been performed as part of this code fix. A reviewer must approve this protected DEV trial workflow and ensure the existing independent rollback executes successfully before claiming real hosted validation.

## 2026-11-17 — two genuine signed Auth users after 240-second idle (source-only)

The existing protected manual-only #939 test now requires that both disposable Auth users pass the **original Y1 campaign GET 404 with handler marker** three times immediately, reject a modified-signature JWT 401, then survive a strict **240-second no-test-traffic idle** before each valid signed token must again return handler-marked 404 in under 18 seconds. JWT `exp` must be at least 360 seconds ahead at issuance to distinguish an ordinary expiry from an ingress/RLS regression. Only after both users are independently cleaned up by exact Admin UUID/email verification will the test print its final `P0249_Y1_REAL_SUPABASE_SIGNED_USERS=2_OF_2_AFTER_IDLE_ACCEPTED_AND_CLEANED` receipt. Negative tests prove that the second post-idle signed read failure still initiates cleanup for **both** synthetic users. No shop, membership, campaign, media, storage, worker, queue or subscription is created by this Auth-only test.

This adds **hosted signed idle-validation criteria**, not successful live evidence. No manual protected dispatch or Azure mutation has occurred. The workflow remains bounded at 12 minutes for its temporary activation job, with independent 8-minute cleanup. Full positive own-shop GET200 / cross-shop denial, poster APIs and the original Flex gateway 503 remain separate unresolved acceptance gates.

## 2026-11-17 — independent two-user Auth reconciliation on worker failure

- Disposable Auth emails for slots 0 and 1 now derive from SHA-256 of the **specific GitHub Actions run ID + attempt + slot**, yielding `rgai-p0249-jwt-` plus exactly 16 lowercase hex digits; this is a recoverable **test fixture label, not a credential**. Both the original temporary trial and a separate protected `independent-restore` job compute the same two labels. Neither signed JWT, privileged key nor password is persisted or logged.
- Once Azure's three public Y1 settings have been rolled back (or rollback has failed), the independent protected restore job still runs `p0249_y1_signed_auth_shadow_once.py cleanup-only` with its own short-lived runner-only Admin credential. For **exactly those two deterministic labels**, original safe cleanup searches the bounded GoTrue inventory and independently verifies the UUID+email before deleting; missing identities are harmless no-ops, failed/ambiguous checks raise an error. Unit tests prove idempotent slot reconstruction, no unrelated marker, and independent cleanup of both slots even when one fails.
- **Caution:** A human-cancelled GitHub workflow or loss of the GitHub Actions control plane can prevent even an `always()` recovery job from running. Such cancellations require explicit operator follow-up of the exact original run ID and attempt using a trusted protected environment. A failed independent cleanup must **never** be interpreted as success or permission to deploy/cut over. This is source-only; no live Auth users were created, no protected workflow dispatched and no Y1 runtime settings changed here.

## 2026-11-20 — exact Y1 two-GET / five-GET signed-trial guard (SOURCE ONLY)

Once the separately reviewed five-GET ZIP is deployed, the existing protected signed
Auth-only canary can now accept **either** exactly the current two named Y1 functions
(`p0249_health`, `campaign_read`) **or** that exact two plus
`render_job_read`, `poster_job_read`, `poster_draft_read`. It rejects partial,
duplicate, renamed, unknown, POST, timer, and queue function-index inventories.
This does **not** deploy or enable those routes.

For a five-function index, the same 16 existing anonymous campaign/health checks
are supplemented by six handler-marked tests for the three additional GET routes:
missing Bearer must return 401, and a nonempty synthetic Bearer must return 503
while `RGAI_P0249_EXTRA_GET_SHADOW` is **absent**. The public-only Auth trial
continues to set/delete only the original three temporary settings. Its preflight
now sees and refuses any pre-existing extra-shadow setting, even `false`;
rollback refuses to modify a concurrently added/changed extra setting.
Independent protected Auth cleanup and existing 240-second signed-idle test remain.
These are preflight/negative gates, **not real hosted signed two-shop RLS
acceptance** or replacement for original POST/PATCH/private media APIs.

Code/tests committed on the existing #939 branch; exact-head four-job CI and
affected shared workflow/JWT review remain necessary. No Azure, Auth, database,
customer, GPU, PROD, WineShopPOS, or frontend cutover was executed here.
