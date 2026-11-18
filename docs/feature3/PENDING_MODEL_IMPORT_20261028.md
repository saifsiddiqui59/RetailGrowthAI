# Feature3 — signed retailer model import (pending only)

Source change dated 2026-10-28. This fills the first step ahead of the existing independently verified original-model evidence and signed human review/revocation. The FLUX.2 Klein 4B GPU remains OFF.

## Implemented

- Additive source migration `supabase/migrations/20261028223000_feature3_pending_model_import.sql`: `public.feature3_import_pending_model` accepts only a real signed Supabase `authenticated` OWNER/EDITOR who is currently active in the owning retailer shop; derives the actor exclusively from `auth.uid()`. No client-provided actor, model scope, status, or rights approval is accepted.
- Registration requires a previously registered private same-shop `media_assets` PNG whose exact owner-first immutable `{shop}/model-library/{model_id}/{sha256}.png` Storage path matches the supplied SHA and media UUID. Reject malformed metadata, missing licensed-source declaration, wrong role/shop, duplicated allowed use, and unsafe attribution. A row lock on the shop bounds the total registered model catalog to 30 records per shop. One model UUID is immutable; a retry of an uncertain insert fails with no inferred success.
- The sole result is `PENDING_REVIEW`, `rights_verified=false`, `evidence_verified=false`, `rights_revision=1`, `gpu_authorized=false`. This is **not** genuine source-license evidence, adult-model proof, inference authorization or marketing approval. All actual original-model byte SHA and license/likeness evidence are handled independently by the prior Feature3 private evidence service and service-only commit from #553. Final signed human review is a separate transaction under #555.
- The existing `Feature3V2Store`, `Feature3V2API`, and `HTTPAPI` get strict signed `POST /shops/{shop_id}/feature3-models/import`. It is OFF unless existing `RETAIL_FEATURE3_V2_ENABLED` **and** `RETAIL_FEATURE3_MODEL_REVIEW_ENABLED` are both true. It creates no public upload, service-role route, GPU job, image, model weights, published artifact or storage link.
- Synthetic HTTP tests `tests/api/test_feature3_pending_model_import.py`, disposable Postgres `tests/security/poster_feature3_pending_import_negative.sql`, and exact migration version+capability guard tests exercise valid pending-only receipt, foreign shop/VIEWER/expired JWT, changed registered media SHA, forged approval flags, duplicate registrations and direct-table write denial.

## Still pending

The registered original-model private Storage binary must be uploaded by a real customer before a genuine submission can work; the existing upload/media registration process and licensing are separate. The new SQL and prior model-review/evidence SQL migrations are **not deployed** to hosted DEV. Protected true tenant and independent human curator acceptance, an actual rights-cleared adult synthetic model + original kurti, accurate VTON inference, generated private output registration, Feature2/4/5 real consumers, GPU budget/cleanup and original Azure #249 reliability remain unfinished. Tests are fictional and do not prove genuine customer credentials or commercial-rights documents.

Do not switch on GPU or enable source route flags in a hosted app until the explicitly approved release and human source-rights acceptance has been verified. No PROD, WineShopPOS or paid resource touches.
