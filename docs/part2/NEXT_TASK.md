# Part 2 — Next unfinished tasks

1. Verify all four 4/4 GitHub Actions jobs on PR #108/#110/#112/#114 exact heads; self-review and merge passing PRs **only** into `feat/part2-integration`. Verify 4/4 on combined integration head. Fix failures without disabling tests.
2. Rebase or merge current `main` into Part 2 integration after reviewing Part 1 API, migration and frontend changes. No force-push to main.
3. Design backend `/api/social/accounts`, `/api/social/oauth/start`, `/api/social/oauth/callback`, `/api/social/accounts/{id}/disconnect`, `/api/social/jobs`, approval and cancel endpoints. Verify live user+shop actor for EVERY action. OAuth state DB consume must be atomic; callback tokens encrypted before private persistence. Callback CSRF/session and provider account/role checks mandatory.
4. Build worker path: atomic due-claim/lease, server verified approval digest, approved media/rights and metadata, active account/scope, subscription publishing quota, no external side effects on absent entitlement. Queue messages UUID-only; deduplicated private outbound receipts. No blind retry on ambiguous external POST, including YouTube resumable session or Instagram container publication.
5. Implement *approved* platform-specific API transports and upload protocols; no live calls until scopes/app review and explicit owner approval. Meta professional IG, Page scopes/roles, LinkedIn developer program and YouTube consent/audit remain blockers.
6. Add tested post approval/revoke/schedule/unschedule and disconnect flows, approval freshness after draft edits, blackout for regulated/uncleared media, platform-specific FFprobe media checks (not generic 30-second assumption).
7. Add role/tenant/security/expiry/replay negative SQL tests to disposable DB CI, end-to-end mocked browser journey, and cross-platform reconciliation tests. Existing P1 historical SQL preflight must remain unchanged.
8. Determine Part 2 per-plan publish allowances with owner approval; reserve exactly once per logical approved job using authoritative subscription period; do not invent paid plans or reuse P1 campaign/render units.
9. After internal completion and green CI, open one `feat/part2-integration` -> `main` final PR for Coordinator. Do not merge it.

Separate approvals are mandatory before hosted DEV SQL, Azure deployment, provider OAuth installation or any real customer publish.

## Latest checked priority after internal P2 foundations (2026-10-23)

1. Finish/disclose current combined integration-head four-job CI after main refresh and #123, and fix any regressions on P2 only. Existing `main` might continue moving; refresh again before final PR. Do **not** overwrite Part 1's new Account/Subscription shell.
2. Implement **DB-atomic** OAuth state consume (and rejection of replay/mismatched actor), provider account connect/disconnect + encrypted credentials; backend authorization and refresh must never expose server secrets.
3. Review pending social SQL in disposable Supabase/Postgres, add negative RLS role/tenant tests, append a uniquely versioned reviewed migration after applied 11. Hosted Supabase application requires separate explicit owner approval. Historical P1 migration preflight is pinned; do not insert unapproved SQL into `supabase/migrations`.
4. Build durable publication schedule, job/attempt claim token RPC, server-authoritative subscription-quota reservation with no double debit, queue/timer and poisoned/reconciliation workers. Existing Part 1 queue names and usage enums remain untouched.
5. Implement network transports with current per-provider API requirements; never automatically retry ambiguous external create-post calls. Instagram container FINISHED, YouTube resumable binary completion, Facebook Page and LinkedIn granted author roles must be verified in mocks before live app approval.
6. End-to-end approval/edit/cancel and cross-tenant, expired account, revoked role, media-rights and quota exhaustion tests. Enable `VITE_PART2_SOCIAL_ENABLED` or `RETAIL_PART2_SOCIAL_ENABLED` only as part of independently approved hosted release.
7. When **all** internal functionality is implemented and 4/4 final integration CI green, open `feat/part2-integration` → fresh `main` final PR for coordinator. Do not merge it yourself.

## Next after security/schema correction
- Run **four actual Actions jobs** on the exact final `feat/part2-integration` commit after this doc update; don't infer integration green from the preceding PRs.
- Before final Part 2-to-main PR, inspect fresh Part 1 main and preserve latest frontend/subscription and any API changes. Current Part 2 main merge baseline was `302ee4ad`; newer coordinator commits may exist.
- Still no real OAuth code exchange/refresh/disconnect, no publication quota configuration, no durable social dispatcher SQL and Queue trigger, no posted social content or E2E. Implement and test those as separate owner-managed Part 2 branches without requiring coordinator merges.
