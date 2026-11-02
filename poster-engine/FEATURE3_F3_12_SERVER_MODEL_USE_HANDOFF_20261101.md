# Feature3 F3-12 / F3-13 — server-side approved model reuse and catalog safety

## Original task coverage and gap

F3-12 is the **approved reusable model library**; F3-13 is its negative rights/security regression package. Existing `checked_model_for_use` accepted any approval-use collection containing a requested use (including duplicates and unknown `admin`/paid permissions) and did not reject missing/unknown model image-license IDs. It also accepted CC-BY attribution of a non-string truthy value. The React browser selector independently rejected these fields, but source authorization must fail closed before backend private-media lookup; browser filtering is not server rights enforcement.

The server helper now accepts only **bounded, nonempty, unique subsets** of the known `poster`, `try_on`, `video_reference` uses; requires an explicitly recognized per-image license ID; rejects unhashable/nonstring license/scope/usage; and requires bounded text attribution including non-whitespace CC-BY credit. Existing independent `authorize_use` callback is still mandatory for actual up-to-date shop/model approval; this source contract does not itself approve any license or likeness.

The server model catalog skips malformed rows that would otherwise crash an entire authorized model picker; no raw URLs, private object keys or media bytes are exposed. Untrusted/forged models never reach the `resolve_private_media` callback. These checks align with the pre-existing strict browser `feature3-approved-models.mjs` contract without changing frontend schema.

## Files, tests, acceptance

- `poster-engine/model_library_v2.py` and `poster-engine/model_catalog_projection_v2.py`: fail-closed server reuse and resilient picker.
- `tests/media/test_feature3_model_library.py` and `tests/media/test_feature3_model_catalog_projection.py`: negative license/rights/use/attribution, malformed-row isolation and positive bounded subset cases, using only synthetic in-memory model metadata.
- Required exact FINAL-head 4/4 Part 1 CI; independent model licensing/private-media affected-lead review; main integration and fresh postmerge main 4/4 before source receipt can be marked integrated.
- This is **source tested only**, not approved likeness, commercially reusable imagery, true service-only license review, signed DEV RLS/Storage or actual generated model output. F3-12/F3-13 original full hosted acceptance remains blocked. Never pretend model code licensing equals per-image licensed use.

No GPU, paid provider, live model-generation, customer photos, hosted SQL, PROD, sample media or WineShopPOS.

## Same PR extension — current signed catalog adapter before user-selected preview
- `azure-functions/campaign-api/feature3_v2_store.py::list_models` is a second distinct backend trust boundary: an injected/tested PostgREST row previously passed through an unchecked `approved_uses="poster"` string, invalid per-image license, malformed SHA or failed synthetic-adult field. The adapter had hardcoded `synthetic_adult=True` without selecting the actual DB column. It now queries `synthetic_adult` (column exists in the original Feature3 proposed migration) and validates **exact** adult flag, source kind, shop-only status, license ID, immutable SHA, label, attribution and unique bounded poster-use grants before requesting JWT/RLS-owned media. A truthy but non-boolean media callback is never acceptance.
- `tests/api/test_feature3_model_catalog_current_rights.py` independently exercises the real `Feature3V2Store` adapter with fake RLS/JWT and negative malformed rows: no private asset lookup for invalid metadata, CC-BY attribution and adult status, even with a correctly shaped ID; a malformed row does not block a valid shop model, and duplicate IDs do not create duplicate selectable previews. Source-only fixture proof, **not** a live JWT, approved likeness or deployed migration.
- This cohesive extension stays inside existing F3-12/F3-13 PR #864 rather than creating a duplicate per-micro-task PR. The old final-head CI from before these commits must be rerun at the **new exact head** and checked 4/4; review is still independent.

## Final negative provenance type fence (same PR #864)
- Server `ModelCandidate` is untrusted structured input. Lists/dictionaries supplied for `scope`, `source_kind`, `license_id` or `pose` previously raised uncaught Python `TypeError` during membership checks; they now explicitly deny with `ModelLibraryDenied` before any private Storage or model registry operation.
- New `test_unhashable_model_provenance_never_reaches_storage_or_registry` proves eight malformed type cases, with zero persisted byte/registry side effects. This stays in original F3-12/F3-13 alongside current synthetic-adult JWT catalog and model use validation; requires exact new final-head CI rather than relying on prior green runs.

## 2026-11-02 — F3-12 malformed model provenance URI denial

- Existing `_source_uri` used `urllib.parse.urlsplit` without trapping malformed IPv6/port `ValueError`, and Python silently strips embedded CR/LF/TAB or leading controls. A forged model provenance link could therefore cause an uncaught exception or differ from the URL actually presented to an independent license reviewer.
- The import boundary now rejects whitespace/control/backslash URL spellings before parsing and maps malformed authority/port parsing to `ModelLibraryDenied` before any private media write or model registration. A valid `https://example.com:443/license` remains supported; a provenance URL is **never** itself proof of license or approval.
- Added deterministic `test_malformed_https_provenance_denies_before_private_storage` negative cases for malformed port/IPv6, leading space, newline/tab, backslash and DEL, plus a positive explicit-443 case. Existing callback/rights and approved-model catalog behavior is unchanged.
- **Acceptance:** verify final-head four mandatory CI jobs after this patch, obtain independent model-rights/private-media review of #864, then reconcile current main and merge only when authorized; fresh main 4/4 and separately reviewed original task ledger evidence remain required. Source-only F3-12/F3-13, hosted 0/33; no GPU, paid inference, hosted SQL, PROD or WineShopPOS.

## 2026-11-02 — Model metadata control characters and early private-lookup denial

- The untrusted model importer accepted embedded CR/LF/DEL in model labels and attribution, and accepted overlong raw labels padded with spaces. Reuse could return control-character attribution to a downstream consumer. The server-side picker validated labels **after** resolving private media, causing unnecessary rights/private lookups for rows that could never be shown.
- F3-12/F3-13 now reject unsafe or overlong label/attribution before storage, reject unsafe reuse attribution before the rights callback, and validate picker labels **before** either authorization or private-media lookup. Tests exercise denial with zero side effects and preserve the existing positive picker/import paths.
- All changes remain in #864 feature-owned model-library paths, with offline fixtures only. Require new exact-head four-job CI, independent model-rights/private-media review, and fresh-main postmerge CI before any source task completion receipt. No hosted acceptance.
