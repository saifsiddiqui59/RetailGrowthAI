# Feature3 — signed retailer model import and independent review browser flow

2026-10-28 source continuation, FLUX GPU OFF. Reuses already-merged backend routes from Feature3 #559 (pending import) and #555 (human review/revoke). No new SQL, HTTP endpoint, infrastructure, paid inference, import of user media or WineShopPOS changes.

## Source changes

- `frontend/src/features/creative/feature3-model-workflow-api.mjs` adds strictly signed JWT one-shot HTTP POSTs to existing:
  - `POST /api/shops/{shop_id}/feature3-models/import`
  - `POST /api/shops/{shop_id}/feature3-models/{model_id}/review`
  - `POST /api/shops/{shop_id}/feature3-models/{model_id}/revoke`
- HTTPS API origin only, no credentials embedded in URL, no redirect following, token from the existing signed-in host, no service key, no POST replay on uncertain 409/503/timeout.
- Exact input and response contracts for `PENDING_REVIEW` import, human six-check `APPROVE/REJECT` with audit event and rights revision CAS, and explicit `REVOKED` with verified current image SHA and auditable reason. Fail closed on foreign or forged statuses, extra rights flags, wrong revisions and missing proof. Client validation is defense-in-depth; only backend JWT verifier, OWNER/EDITOR membership, SQL model revision/evidence and independent curator can grant approval.
- `Feature3SignedModelWorkflow.jsx` provides an optional accessible import/review/revoke surface for a pre-existing registered private original PNG; independent human checks must be completed consciously and are not inferred from synthetic fixture images. No browser Storage upload or service role is introduced. A late/unknown result never triggers an automatic retry.
- `Feature3ModelLibraryReview.jsx` and `Feature3StudioPanel.jsx` accept optional `modelWorkflowApi` and `modelWorkflowEnabled=false`. The new UI is **not mounted or enabled by the default host**. It cannot flip the two existing backend release flags or open paid GPU routes.

## Offline tests and hard boundaries

- `tests/frontend/feature3-model-workflow-api.test.mjs`: 12 Node test cases with fictional signed sessions, foreign shop, wrong status, six checks, explicit rejection/revocation, blocked raw Storage path, expired JWT, blocked service/publishable keys, 409/503 no retry and base-origin restriction. These tests do not prove genuine browser login or commercial rights; source code build must pass exact-head CI.
- The model private original must already be uploaded and registered under the customer shop through the existing protected media process. The HTTP import route does **not** upload image bytes or prove license. The service-only evidence writer (#553), independent person/license reviewer and signed decision/revocation SQL (#555) must be deployed after separately reviewed migrations before any genuine positive hosted acceptance.
- The present UI requires manually supplied current revision and independent evidence revision; a complete authenticated read-back/status and private-media upload browsing experience remains future work. It is NOT an automatic real-customer approval.
- Real approved licensed photos, real VTON, accurate garment identity, GPU inference and budget, private output CAS/storage implementation, downstream live handlers, Azure #249 reliability and signed two-tenant DEV checks are still open.
- No hosted SQL, provider call, GPU, PROD or WineShopPOS touched. Coordinator must review and merge after four exact-head jobs and separately verify main CI.
