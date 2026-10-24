# Branded onboarding notification email handoff — source-only

- This branch is intentionally based on the existing email implementation `feat/p1-email-notifications` (open PR #206), **not** merged or edited into the other lead's working branch.
- Adds a display name `RetailGrowthAI` on the separately configured `From` email header and accessible plain text + HTML multipart messages for new pending retailer, retailer approved and retailer rejected.
- HTML is generated from fixed server-side content with HTML-escaped approved HTTPS site links. Emails never include passwords, Auth tokens or untrusted business descriptions. Real sender address may match the owner's WineShopPOS address with separately authorized project-specific credential; **do not reuse WineShopPOS production app password**. WineShopPOS original code remains untouched.
- Requires parent #206 worker to accept/merge this child PR before activating sending. Current parent uses feature-flagged SMTP sender and notification outbox; **off by default**. Deployment, Auth sender configuration, secure queue migration and real delivered mail are NOT done by these source edits. Maintain at-least-once delivery disclosure.
