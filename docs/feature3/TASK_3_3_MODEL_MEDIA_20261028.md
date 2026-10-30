# Task 3.3 — Registered media ownership must precede model catalog creation

The existing `poster-engine/model_library_v2.import_model_image` normalized
real PNG bytes and stored a private content-addressed file, but its candidate
record did **not** require a real `media_assets.id`, even though the
`public.feature3_models` table requires
`(owner_shop_id,media_asset_id)` referencing the owning retailer's media.
This is an actual workflow gap, not a call for another mock.

The model import contract now requires the server-owned private image writer
to return `{key, sha256, private:true, owner_shop_id, media_asset_id}`.
It refuses absent, noncanonical or foreign shop media registrations and only
calls the catalog-registration callback after proof. The resulting pending
record includes `media_asset_id` and stays `PENDING_REVIEW`.

This is source behavior only. A real authenticated server must still stream
private uploaded media bytes under JWT/RLS, confirm the database media asset
and Storage object's hash, write using the already deployed catalog schema,
and implement human approval/revocation and a same-shop private reuse route.
Never derive an asset UUID from a browser assertion or reuse the inactive
Feature2 synthetic shop image. The model visual and commercial reviews are
still release gates. This change does not run FLUX or purchase a GPU.

Negative tests: wrong shop, missing registered ID and forged ID.
No WineShopPOS/PROD.
