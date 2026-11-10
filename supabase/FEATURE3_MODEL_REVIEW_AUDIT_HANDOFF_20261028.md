# Feature3 P0 — durable model review and signed SQL CAS (2026-10-28)

SOURCE ONLY. The migration supabase/migrations/20261028190000_feature3_model_review_audit.sql and
disposable CI tests/security/poster_feature3_model_review_negative.sql are **not** hosted DEV or PROD execution.

## Security contract

1. Private retail_private.feature3_model_evidence is only INSERTable by a trusted service after genuinely checking actual private PNG bytes, per-image licence/likeness rights and source. Browser actors cannot write verified evidence.
2. public.feature3_review_model is an authenticated, database-checked OWNER/EDITOR signed RPC, deriving human reviewer identity exclusively from auth.uid and current active shop membership. Platform model approval also requires an independent current platform-admin grant, never uploader self-approval. Six explicit human boolean attestations and human notes are required; client approval flags alone are not trusted licence evidence.
3. The function locks existing model, trusted evidence and media, verifies tenant/model/media/immutable digest/license/revision/current Storage key, inserts a private durable audit event and updates status and rights_revision in a single SQL transaction. Missing/stale/ambiguous receipt fails closed. The SQL does not inspect Storage pixels; trusted evidence writer must do so first.
4. public.feature3_revoke_model fences the same current approved model/revision/sha, records reason and revoker, increments rights_revision and marks REVOKED. It allows emergency revocation after external rights expire.
5. A separate trigger blocks direct model INSERT as APPROVED, direct model status/rights revision PATCH without matching audit event, and mutations of immutable registered identity, source SHA or licence details. The browser has no INSERT/UPDATE on model/evidence/event tables.
6. This never triggers GPU, real model rendering, paid FLUX, generated asset registration, download URLs or marketing publication.

## Remaining P0 work

- Review/add source PR via coordinator, run exact four CI jobs and independent main; release migration to RetailGrowthAI DEV only with separate owner-approved deployment and validation.
- Implement a server-only, private Storage + licence evidence writer that checks real registered PNG byte SHA and adult identity, records independently verified evidence, and binds the source-only Feature3 reviewer callbacks to a genuine signed auth-token session. No service-key impersonation of end users.
- Test true authenticated OWNER/EDITOR/VIEWER/foreign/expired cases and model-rights races on DEV after deployment. Disposable SQL fixtures only test database boundaries, not actual licensed images.
- Obtain independently licensed tenant-owned kurti and synthetic adult reference, preserve exact garment fidelity, connect Feature2 storyboards, Feature4 editor, and Feature5 worker first-frame receipts only when current rights and job lease are proven.
- Continue real video provider licensing, output-byte registration, queue/outbox, bounded settlement, Azure #249 reliability and hosted quality acceptance with GPU OFF until separate spending approval.

No hosted database migration, Azure resource write, real paid model generation, PROD or WineShopPOS change in this branch.
