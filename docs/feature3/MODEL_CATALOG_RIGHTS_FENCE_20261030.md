# Feature #3 F3-12 / F3-13 — catalog license and usage validation (2026-10-30)

Source-only, CPU-only defensive validation. This work does **not** approve any real model, establish commercial/likeness rights, authorize GPU inference or change a tenant's grants.

## Scope
- The signed-in host's model selector now refuses catalog entries whose `license_id` is missing or outside the existing import contract: `CC0-1.0`, `CC-BY-4.0`, `REVIEWED-COMMERCIAL`.
- `approved_uses` must be a bounded (1–3), unique array containing only `poster`, `try_on`, `video_reference`, and explicitly contain the requested use. A forged or format-confused entry is not displayed as a selectable approved model.
- Existing private image map, same-shop scope, SHA and attribution checks remain unchanged. The server must independently check live RLS, human review, immutable bytes, license and revocation before any save, export or inference.

## Verification
- Added offline Node regression cases to `tests/frontend/feature3-approved-models.test.mjs`, including unknown/missing license IDs, malformed/duplicate uses and valid recognized combinations.
- Exact-head four-job PR CI and coordinator-reviewed integration remain required. Until then this is **source proposed**, not an integrated DONE receipt.
- Hosted rights acceptance remains blocked by `F3-LICENSED-MEDIA` (Feature #3 owner: independently verified original commercial/likeness evidence, current grants and human reviewer receipt). Signed two-tenant DEV E2E remains separately required; neither is simulated by this fixture test.

No SQL, cloud resource, GPU, paid inference, PROD or WineShopPOS changes.
