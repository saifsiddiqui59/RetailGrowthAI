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
