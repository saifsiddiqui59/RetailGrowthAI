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
