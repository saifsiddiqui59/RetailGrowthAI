# Part 1 — branded notification message follow-up (source-only)

- Parent notification outbox/SMTP PR #206 is already merged into `feat/part1-completion`. This PR adds only RetailGrowthAI sender display name and accessible HTML+text alternatives, escaping, and tests on the integration head.
- Supabase Auth confirmation/reset templates remain separate from the server-only approval/rejection notification worker.
- Sending remains OFF until independent project-specific SMTP authorization, secrets, backed-up DEV schema migration approval, and genuine inbox verification. The same authorized mailbox address as WineShopPOS may be configured with a different display name, but WineShopPOS production SMTP credentials must never be read/reused.
- At-least-once SMTP may duplicate on ambiguous failure; this PR does not claim delivery or deployment. WineShopPOS, PROD, Part2 and Part3 remain unchanged.
