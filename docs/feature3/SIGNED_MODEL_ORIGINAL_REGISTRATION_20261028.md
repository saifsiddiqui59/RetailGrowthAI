# Feature3 P0 — Authenticated model-original private registration (source only)

Date 2026-10-28. GPU and hosted migrations remain OFF. This fixes a missing contract between the earlier merged `register_uploaded_image` (accepts only `uploads/`) and Feature3 `feature3_import_pending_model` (requires an already registered `model-library/{model_id}/{sha256}.png`).

## Source implementation

- Additive `20261028232000_feature3_model_original_registration.sql` introduces `public.feature3_register_model_original` authenticated retailer OWNER/EDITOR RPC, deriving actor from `auth.uid()` and checking current active membership, private Supabase Storage object **owner ID**, tenant-scoped exact key, PNG MIME/size, nonduplicated path, declared license metadata and bounded per-shop model count. The original private PNG must already be uploaded using the **same signed user's JWT**; no service bypass or public URL is accepted. The registered `media_assets` UUID is distinct from model ID, and source stays `UPLOAD` with `SOURCE_REGISTERED_PENDING_EVIDENCE`.
- Existing `Feature3V2Store`, `Feature3V2API` and `HTTPAPI` gain strict signed `POST /api/shops/{shop_id}/feature3-model-originals/register`, behind both existing Feature3 and model-review flags (default OFF). Azure Functions route registration for the already implemented `feature3-models/import` endpoint was also missing and is now explicitly mounted. No new GPU route.
- Disposable `tests/security/poster_feature3_model_original_negative.sql` exercises signed owner / viewer, wrong SHA, duplicate registration and successful source-row to **PENDING_REVIEW-only** model import. Mocked `tests/api/test_feature3_model_original_registration.py` checks expired/foreign/VIEWER/EDITOR/forged receipts and exact one-shot JWT/RPC semantics.
- Migration inventory, security capability markers and legacy Feature2 hosted executor denylist explicitly recognize this version while keeping `authorized_to_apply=false`.

## Explicitly NOT complete/real

The RPC checks Storage **metadata and declared object path**, not original PNG bytes' cryptographic hash. The existing trusted private binary evidence reader from #553 must re-fetch actual uploaded bytes and compare SHA before independent verified license/likeness/age/provenance evidence commit and separately signed human reviewer + independent platform curator approval. A retailer-declared `license_name='owned'` is NOT independent legal evidence. No real licensed adult image, invoice, curator, customer signed DEV test or paid FLUX/VTON call occurred.

The browser signed model workflow PR #563 is still host-disabled and will require an explicitly reviewed private original PNG upload UI/server resolver; this source path does NOT upload files from a browser. The model-original original may be modified/revoked until separately fenced by the evidence/review stage; consumers must refresh original byte SHA and rights every use. Hosted migration, signed DEV acceptance, Azure #249 reliability and real output QA require separate authorization. No WineShopPOS touched.

**Coordination:** this branch independently introduces source-only version `20261028232000`; coordinator must integrate it after #565 `20261028230000` and #566 `20261028231000`, reconcile all three exact migration inventory/Feature2 hosted denylist entries, run four PR CI jobs on final head, and verify independent main CI after merges. Do not self-merge.
