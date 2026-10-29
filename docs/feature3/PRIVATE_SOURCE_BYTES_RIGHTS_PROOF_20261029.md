# Feature3 — Actual private source bytes + current independent rights gate (2026-10-29)

## Implemented, non-GPU / source-only

`azure-functions/campaign-api/feature3_private_source_proof.py` supplies the concrete byte verification callable required by `Feature3GPUJobPlanPreflight(source_proof=...)`. It takes an **authoritative media_assets row** already selected from service-only PostgREST and a **separate reviewer-backed current rights authority**. It denies foreign, public, malformed object path, unapproved licensing or user, revoked/expired revision and any unsupported media type. Before the GET, `current_rights(shop,asset)` must return exact authoritative reviewed SHA256/rights revision, commercial permission, provenance and retailer approval. It reads the *actual* registered object via backend-only HTTPS `/storage/v1/object/retailgrowth-media/{shop}/...`, fixed no-redirect URL and backend key, with private byte-size/MIME guards, Pillow real-image decode and pixel bounds. Compares SHA256 of actual bytes to the **independently reviewed** SHA, then calls current rights authority again to catch revocation during private Storage read. Outputs proof fields only; never source bytes, object path, signed URLs or provider permission.

This closes the **private source byte verification implementation** dependency for CPU-only job planning, but NOT the independent **legal provenance/retailer approval service**: that reader must be supplied by a trusted backend after real human/commercial evidence and current revocation data, not from the browser, media metadata alone, or a license string. The proof cannot itself establish rights by downloading pixels. It also does not authorize paid GPU, guarantee SQL/Storage atomicity, persist any object, claim a lease, or ensure production Supabase new secret auth acceptance; hosted real DEV test remains required.

`tests/api/test_feature3_private_source_proof.py` uses real Pillow-generated PNG, actual SHA compare and mocked `urllib.request.Request`, tests same shop, foreign source, untrusted license, revoked during GET, corrupt/tampered image, header mismatch, redirect, oversized data and untrusted origin. No external network or model.

## Integration dependency and release

Merge reviewed source only after exact-head four jobs and postmerge main four. Real backend wiring must instantiate:
`Feature3PrivateSourceProof(origin, backend_secret, current_rights=trusted_current_license_and_approval_reader)` and pass instance as `Feature3GPUJobPlanPreflight(admin_store=AdminStore(...),source_proof=instance)`. The actual current rights authority must be backed by the independently reviewed model/source evidence, versioned approval records and live policy; **never** inject a constant True or static demo manifest.

Actual Azure Queue trigger/paid execution remains OFF. For generated source media, make sure current rights authority refuses `UNREVIEWED` outputs even if their PNG bytes are valid. No hosted migrations, paid GPU, PROC/PROD, or WineShopPOS changes.
