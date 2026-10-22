# Architecture Decisions

- Use Git Bash and VS Code.
- Use an independent GitHub repository.
- Reuse selected WineShopPOS patterns.
- Never share WineShopPOS production data or secrets.
- Supabase for Auth, PostgreSQL and RLS.
- Azure Functions for application APIs.
- Azure AI Foundry for AI generation.
- LangGraph only where agent orchestration adds value.
- uv for Python and npm for JavaScript.
- Stock footage plus FFmpeg before premium AI video.
- Postiz excluded.
- Razorpay excluded.
- Platform integrations deferred to Part 2.
- Wan integration deferred to Part 3.
- Maintain strong tenant isolation from the beginning.

## 2026-10-22 — Architecture for parallel Part 1
- Keep four product parts, but parallelize four independent Part 1 coding workstreams under coordinator-owned contracts.
- Use Python + uv for campaign API and agent package, and npm/React for the frontend; borrow WineShopPOS security and UI patterns but never copy credentials or POS-specific tools.
- Protect contracts in docs/INTERFACES_V1.md and branch ownership in docs/PARALLEL_WORK.md. No worker chat merges to main.
- Use async campaign planning and video rendering; return job IDs and poll, rather than block browser HTTP calls while FFmpeg runs.
- Render initial 30-second 1080x1920 H.264/AAC Reel locally with FFmpeg; choose Azure video worker hosting only after benchmarking.
- Store uploaded content as private media with tenant authorization, track usage and rights metadata, and treat regulatory content as review-gated.
- This is an architecture decision and documentation update only, not an implemented/deployed feature.

## 2026-10-22 — Minimal coordinator frontend bootstrap
- Keep the shared v1 mock campaign as a normalized GET /api/campaigns response under frontend/src/features/campaigns/fixtures/ with exactly seven distinct sequential days and contiguous 30-second storyboards; UUIDs are synthetic, not real media references.
- Coordinator owns the root React Router shell and Vite dependencies. Feature D owns the eventual campaign UI within its designated directory; Feature A owns the auth implementation.
- Pin direct frontend dependency versions. Because npm registry access is not available in the coordinator sandbox, use GitHub Actions for independent install, contract and build verification; generate and review the lockfile before adopting npm ci. Do not mistake static validation for a successful Vite build.

## 2026-10-22 — GitHub Actions as iterative development test runner
- Use one existing workflow path (.github/workflows/frontend-bootstrap.yml) with frontend, Python/uv and FFmpeg CI jobs; avoid duplicating frontend runners.
- Trigger on main/feature branch pushes and main-targeted PRs. Use read-only workflow token, no secrets on PRs and no cloud provisioning. Cancel superseded runs to limit billed minutes.
- Require each workstream to record actual CI run evidence before requesting coordinator merge. ChatGPT may inspect failures and push fixes during an active chat, but GitHub Actions does not autonomously write fixes.
- Real 30-second renderer validation is owned by Workstream C; synthetic two-second FFmpeg check only confirms codecs and tool installation. See docs/CI_AUTOMATION.md.

## 2026-10-22 — Approved Part 1 CI integration (PR #1)
- Merge the read-only, secret-free three-job CI workflow; post-merge run #39745758948 passed all three checks. Workstream chats must provide passing PR-run evidence; the coordinator validates integration on main.
- A two-second synthetic video test only confirms FFmpeg H.264/AAC toolchain; separate 30-second renderer, RLS denial, and AI behavior tests are mandatory in workstream PRs. A green scaffold check is not production readiness.
- After coordinator documentation updates, fast-forward the four unchanged feature branches to the same latest main commit before parallel work. Preserve branch ownership and contracts.

## 2026-10-22 — Coordinator Auth route and reusable security gate
- Keep Workstream A schema/Auth implementation in PR #5; coordinator owns root router and shared CI changes in a separate stacked branch rather than breaking parallel file ownership.
- Wrap root app with Workstream A AuthProvider, mount AccountWorkspace only under `/account`, and continue labeling campaign data as mock. Live Auth depends on RetailGrowthAI-only VITE publishable settings; never ship service-role or secret keys.
- Add an independent read-only GitHub Actions security job: Node client tests plus disposable Supabase Postgres and migrations followed by negative SQL tests. No hosted Supabase database or credential is used in CI; do not weaken tests for green status.
- Dedicated RetailGrowthAI Supabase project `jeearzffnjbvghwjjjrf` is DEV/pilot only; production requires a separate project. No changes to WineShopPOS or existing voice projects.


## 2026-10-22 — Workstream integration and truthful runtime boundaries
- Integrate A PR #5 before stacked coordinator PR #6, then B PR #3, C PR #2, and D PR #4; reconcile the shared App.jsx router to retain both live-configurable AccountWorkspace and mock CampaignDashboard.
- The UI's natural-language campaign brief must remain preview-only until a real authenticated HTTP service and authorized tenant-specific media are wired. Never silently replace synthetic fixture IDs with trusted IDs or enable fake render/download controls.
- The Python CampaignService is a dependency-injected **non-deployed** API boundary, not a working Azure Function; the 30-second renderer is a tested offline CLI. A coordinator cross-component integration test validates v1 B planner -> C renderer manifest compatibility without pretending to run an online campaign.
- Four CI jobs run independently; a green CI run proves covered fixture, unit, synthetic render and disposable Supabase security checks, not browser E2E or production cloud auth. Never share WineShopPOS secrets/resources.

## 2026-10-22 — API security boundary
- Prefer project-pinned asymmetric Supabase JWKS verification, exact issuer/audience and RLS access via the end-user bearer token; reject missing secrets/unsigned or HS256 JWT without a verified migration plan.
- Keep API POST returning 503 until a persistent, acknowledged queue exists. Never present an in-memory queue or unqueued write as accepted.

- Pin FFmpeg CI runner to `ubuntu-24.04` after the rolling runner introduced FFmpeg 8 with unverified pixel-format behavior. Keep all smoke, codec, duration and content assertions enabled; verify compatibility before upgrading.

- Durable planning uses existing Supabase campaigns as atomic idempotent claim state plus Azure Storage Queue for persisted deliveries. Worker uses service role only server-side, never trusts message/asset rights and never self-provisions cloud resources.

- Signed MP4 URLs are minted only from tenant-authorized private storage via the end-user JWT (60-second expiry). Render job POST needs verified membership and licensed asset IDs; server-derived idempotency key prevents duplicate requests for identical day/reel.

- Keep renderer as bounded server-only Queue trigger consuming opaque job IDs; regenerate trusted manifest using tenant-authenticated DB rows and private media paths. Persist deterministic output key and never allow arbitrary browser-provided FFmpeg paths. Quota/lease sizing must be benchmarked before cloud deployment.

- Frontend must never send synthetic fixture asset IDs; authenticated live mode selects previously authorized per-shop media via RLS. API calls refresh the Supabase access token, reject redirects and gate signed downloads to the configured private storage origin. Unsaved edits remain local and cannot be rendered as saved server drafts.

- The campaign status column remains server-owned. Privileged cleanup is narrowly filtered by campaign, tenant, owner and status. Use opaque sb_secret_ keys only in apikey; reject unverified existing rendered objects rather than treating 409 as upload success.


## 2026-10-22 — Live UI request consistency
- The campaign request shown to a signed-in user must exactly match the authorized payload sent to the API. Only selected business/asset UUIDs from the RLS-backed UI may appear; never substitute sample fixture IDs in live requests. Missing or duplicate media blocks submission. Offline mock mode remains unchanged.

## 2026-10-22 — Draft edits through a restricted user-scoped RPC
- Require the HTTP boundary to validate complete v1 campaign output and authorized source asset IDs before accepting an edit. Only topic, LinkedIn and Instagram draft fields can change; identity/schedule/status are server-owned.
- Revoke direct authenticated UPDATE on public.campaign_days and use a PostgreSQL security-definer RPC with explicit auth.uid() and active OWNER/EDITOR membership checks, plus original-value comparison and blocked edits during queued/running renders. Do not grant service-role tokens to browsers.
- A UI preview is never evidence that a draft is saved; remote edits are enabled only after the authenticated PATCH returns committed data. DEV migration needs explicit approval, no hosted mutation in CI.

## 2026-10-22 — Bind user-uploaded media metadata to private Storage objects
- Browser may upload only PNG/JPEG/WebP bytes after declared commercial-use ownership/permission and evidence. Direct authenticated `media_assets` INSERT is revoked; a restricted server-side PostgreSQL RPC verifies the user-owned private Storage object, current shop edit membership, MIME/size/path and license fields before recording metadata.
- Upload UUID and shop ID determine the object path; neither browser-submitted paths nor browser-side license declarations alone grant access to another tenant or confirm independent copyright clearance. Storage object size/content-type remain untrusted until renderer decodes real bytes. Browser JWT/publishable key only; service keys never cross into the client.
- Registration/RLS checks are automated in disposable CI. Hosted migration and actual third-party asset provenance/approval remain unverified/approval-gated.
