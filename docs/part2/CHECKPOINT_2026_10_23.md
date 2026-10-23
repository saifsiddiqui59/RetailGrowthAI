# Part 2 — 2026-10-23 safe-source checkpoint and coordinator handoff (NOT FINAL)

## Verified internal merges
- #161/#162/#164/#165/#166/#168/#170 were merged before this checkpoint; no duplicate implementation.
- [#171](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/171) independently gated Meta/LinkedIn OAuth provider registration and strict token/identity transport. Initial Python job failed due to a test importing a different exception class instance; corrected without weakening checks. Exact revised push CI [40018201041](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40018201041) **4/4 passed**, merged to P2 integration as `a973ed2070a92cb9a4ace80b60b82f2fe1558846`. Post-merge integration [40018611305](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40018611305) **4/4 passed**.
- [#172](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/172) disallows HTTP redirects and unexpected TLS ports on confidential social authoring Supabase RPCs; regression-tested. [40018540917](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40018540917) **4/4 passed**, merged `819c19475d831e417989d3f8a94d2ee90422ca52`. Post-merge [40019076415](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019076415) **4/4 passed**.
- [#174](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/174) disallows redirects/non-443 ports on OAuth private Supabase RPCs and bounds responses to 64KiB. [40018759345](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40018759345) **4/4 passed**, merged `652289ac93359ecf384fe28418ee0fa475fa8398`. The corresponding integration-head CI must be inspected separately.
- [#175](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/175) adds DRAFT-only safe revision/rescheduling through authenticated API, retailer editor and a **tenth staged P2 SQL source** `20261023190900_p2_social_draft_revision.sql`. Exact revised branch [CI 40019171343](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019171343) **4/4 PASS** and internally merged as `362ffd0b66ce3c541350a880c66ff1ec13c4f8fc`. Post-merge integration [CI 40019649987](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019649987) **4/4 PASS**. Do not apply staged SQL to hosted DB.

## Release state
All active publishing/OAuth/worker/frontend gates stay OFF. CI covers offline mocks, private disposable PostgreSQL and synthetic FFmpeg, not real-provider account connection, live platform posting, Azure deployment or hosted migrations. Do NOT import Part 2 pending SQL into Part 1 historical migrations without reviewed staged migration ordering. No WineShopPOS modifications.

## Remaining engineering work
1. Post-#175 integration-head CI #40019649987 passed 4/4. Verify any later security/docs PR integration-head CI before final handoff. Keep hosted SQL and release flags OFF.
2. Complete account choice and provider grant/revocation semantics; real Meta/LinkedIn/Google API scope/version/app-review validation remains external.
3. Wire production-safe durable media upload/session context, object-hash/license/FFprobe/media rights, remote publication receipts and reconciliation for Instagram Reels/YouTube Shorts; existing mocks do not prove live publishing.
4. Finish approved-job revoke/reschedule and quota refund policy without replay or double-charge; the new #175 flow deliberately edits **DRAFT only**, never a possibly sent job.
5. Expand authenticated browser, database and queue failure-injection E2E, tenant boundary and provider-specific data validation; update final handoff after verified CI.
6. Refresh newest `main` and send only a final integration PR to the coordinator after engineering is complete.

## Independent owner release approvals still required
- P2 hosted migration execution, with reviewed chronological schema compatibility
- Azure Functions+Queue+Storage worker deployment and release flags
- Meta/LinkedIn/Google confidential OAuth apps and grants/app reviews
- Plan-specific actual publish quotas/subscription allowances
- Controlled real-provider E2E publishing test and commercial media rights approval

No completed internal PR constitutes any of these approvals.

- [#178](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/178) prevents signed-in retailer JWT leakage via social read endpoint redirects and bounds read replies. Exact [CI 40019859294](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40019859294) **4/4 PASS**; merged P2 integration as `b78cd4d000d48086a7da43cd2dd0494790f01c9b`. Verify its post-merge integration check independently.
- [#180](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/180) is the pending mocked Playwright social authoring security journey; do not mark green/merged until all four checks actually pass.

## Fresh Part 1 compatibility boundary
GitHub comparison at this checkpoint: `main` `d590a3cf7ad9beb37f8d74c7f310627252fef620` and Part2 integration `b78cd4d000d48086a7da43cd2dd0494790f01c9b` **diverged**; comparison reported 12 commits on main not contained in the integration branch and 47 commits on P2 not in main. Review new Part1 onboarding approval migration `20261023191246_p1_onboarding_approval.sql`, `frontend/src/App.jsx`, platform admin changes and Azure SWA auth workflows before any final Part2-to-main compatibility PR. Coordinator owns final merge, do not copy newer main blindly into Part2 or claim compatibility verified.
