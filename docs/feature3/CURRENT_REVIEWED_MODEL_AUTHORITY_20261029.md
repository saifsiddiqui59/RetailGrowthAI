# Feature #3 current reviewed-model authority handoff — 2026-10-29

## Completed source only

- `azure-functions/campaign-api/feature3_model_review_authority.py` adds `Feature3ApprovedModelReviewAuthority` and `build_approved_model_gpu_off_preflight`. It connects the already-merged real private image byte/hash source reader with the current approved-model review evidence **through a narrowly named, service-only read RPC**. The existing GPU-OFF preflight still performs independent job/shop/subscription checks and twice checks the source authority, and its result never permits a provider call or paid retry.
- A successful verdict is limited to exactly seven fields: same-shop media id, real image SHA, integer current rights revision (at least 2), independent image licence verification true, current human model/likeness approval true, and revocation false. Missing source, altered identity, foreign model, revoked/false reviewer status, extra keys, wrong SHA or untrusted format are denied. A non-model product/garment source is **not** authorized by this model-specific authority.
- The existing `AdminStore` now restricts the proposed read RPC `rpc/feature3_read_current_model_review` to **POST through a backend secret only**, never a JWT/browser read or generic status write. `tests/api/test_feature3_model_review_authority.py` tests the actual urllib POST path/payload via a non-network fake, exact response validation and unauthorized inputs. No public URI, source bytes, token, spend permission or GPU is returned.
  
## External database and legal evidence gate — **not implemented/live**

The corresponding SQL function is a **proposal only**; an executable SQL proposal could not be added through the tool during this change, and no migration was created/applied. Before any Azure runtime may call the bridge, the coordinator/DB owner must review and add a versioned read-only SECURITY DEFINER function, grants restricted to `service_role` and explicit grants revoked from `public`, `anon`, `authenticated`, under an approved migration. An authoritative response must be computed atomically from:

1. Current `feature3_models` row with `status=APPROVED`, `rights_verified=true`, matching shop/media/image SHA, synthetic adult and approved poster use, and current `rights_revision`.
2. The immutable `retail_private.feature3_model_evidence` matching that model/source SHA, licence evidence hash, source kind, commercial re-use, synthetic-adult and component rights.
3. Its *latest* `retail_private.feature3_model_review_events` revision, APPROVE/APPROVED decision, same source SHA, evidence revision and all six required human review checks true; a later revoke must never be hidden by an older approval.
4. The exact current `media_assets` owner, private bucket, immutable model-library path, PNG SHA/format and independently approved commercial licence evidence.

Return exactly the seven-value receipt or NULL. No fallback to self-declared `license_name`, UI checkbox, demo OpenVTO source, model weights or synthetic receipts. Product and garment originals need a **separate** commercially reviewed evidence authority; they must fail closed under this model-only path. Do not equate a signed review event with independently verified external commercial contracts unless the original legal evidence was genuinely checked.

## Remaining release gates

- DB owner review, a new **separately approved** migration and negative disposable tests for anon/JWT/foreign/rotated/revoked reviews.
- Live current rights and private byte reads under service credentials, paired to actual single-shot SQL claim, before any worker provider activation.
- Signed DEV testing of real approved and revoked model records, exact SHA and customer consent, and human garment fidelity evaluation.
- Azure #249, paid GPU/VTON provider, actual queue/poison, signed browser output previews and operator billing verification remain separate.

No canonical Supabase migration, DEV/PROD cloud setting, paid provider, queue delivery or WineShopPOS resource was changed.
