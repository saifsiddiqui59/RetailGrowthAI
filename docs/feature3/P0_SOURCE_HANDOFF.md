# Feature #3 P0 Coordinator Source Handoff — 2026-10-26

**SOURCE ONLY / NOT ENABLED / NOT DEPLOYED.** Parallel creative branch: PR #321.

## Implemented on this coordinator integration branch

- New additive Feature3 model catalog and poster design v2 Supabase migration; RLS for both tables; browser read-only grants; server-only model registration and review; verified-rights constraint before APPROVED.
- Protected v2 poster save RPC: actor derived from JWT, live OWNER/EDITOR authorization, campaign/day DRAFT, trial/subscription lock, bounded validated design JSON, current shop media rights, revision CAS, immutable APPROVED design, new variation lineage. No v1 schema changes.
- Python user-JWT PostgREST store and source-only v2 API model-list and design-list/create/update; Feature3 routes are disabled by default behind RETAIL_FEATURE3_V2_ENABLED and not configured in hosted DEV.
- Disposable SQL role, tenant, stale CAS, source-media and forged-approval tests, plus Python mocked API denial tests. The original DEV migration preflight allowlist is extended explicitly with new protected SQL markers; historic ten-migration execution remains blocked without approval.
- No third-party model import, hosted migration, paid GPU inference, Azure provisioning or WineShopPOS/prod changes.

## Blockers that must remain visible

1. SQL server_document_sha256 is SHA256 of PostgreSQL JSONB text and is NOT the Python poster-engine canonical design_fingerprint. Reconcile digest and immutable final revision before enabling actual v2 rendering/approval.
2. Cross-tenant platform model **metadata** visibility never grants image bytes. Build a new current-RLS private media grant/delegation for actual shared model reuse. No public Blob paths.
3. Existing PR #321 UI needs authenticated approvedModels and authorized private imageMap supplied by a signed-in host. Current API returns catalog metadata only; private binary loading and actual v2 save-client UI need integration.
4. v2 server-render queue, existing trial ledger/outbox, private output proof and signed PNG/GIF/MP4 downloads are NOT wired. The v1 renderer must never be fed v2 JSON.
5. P2 Konva mounting needs reviewed dependencies, browser/server parity and mobile tests. FLUX/VTON still requires real weights, operator licensing and budget approvals. No paid GPU activation.
6. Owner explicitly deferred genuine Indian source-image visual review, independent rights research and Hosted DEV/live browser E2E from current sprint. Third-party rights enforcement is not waived.

Only coordinator integrates PRs and updates canonical PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG after review. CI success is source-only evidence, not live acceptance.
