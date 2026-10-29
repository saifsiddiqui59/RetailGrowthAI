# Feature3 actual private input byte and source rights proof — 2026-10-29

## Existing task now implemented as source

`azure-functions/campaign-api/feature3_private_source_proof.py` provides `Feature3TrustedPrivateSourceProof` and `build_verified_gpu_off_preflight`:

1. Accept only an **authoritative same-shop** `media_assets` row already retrieved by service-only PostgREST; reject arbitrary URLs, non-private bucket, licence placeholders, foreign shop, path traversal, escaped path segments, unsupported MIME or mismatched extension.
2. With an explicitly configured Supabase backend service credential, use **GET only** on the exact `/storage/v1/object/retailgrowth-media/<registered-path>` endpoint; never fetch a URL supplied by the retailer and never redirect.
3. Limit network read to 25 MiB; validate real Pillow PNG/JPEG/WebP single-frame bytes, dimensions, MIME, optional Content-Length and max pixel count, then SHA256 the **actual downloaded bytes**.
4. Require a **separately injected current independent licence and customer approval authority** that binds the original same-shop media ID and actual binary digest to a reviewed `rights_revision`. Call this authority twice, refusing any revoked approval or changed revision. The media row's self-declared licence name, UI consent or demo manifest is not accepted as legal approval.
5. Produce the exact `Feature3GPUJobPlanPreflight` source-proof receipt, containing only shop ID, media ID, SHA256, current reviewed revision and four strict booleans. No private object path, key, image bytes, signed URL, GPU charge or publish approval is returned. The existing planner checks the same proof again around its second authoritative SQL snapshot.

Tests in `tests/api/test_feature3_private_source_proof.py` generate real Pillow pixels and mock the actual HTTPS request boundary. They cover PNG/JPEG/WebP bytes; identity/URL injection; MIME, redirect, byte and size mismatch; private rights denied/revoked in flight or revised after first check; missing independent authority, invalid key/origin and factory integration.

## What is still not operational

An actual independent approved licence/evidence/revocation authority must be implemented and deployed from genuine customer-reviewed source records. `build_verified_gpu_off_preflight` takes that authority as a mandatory backend dependency and **does not implement legal title verification from a license_name field**. The host must supply a protected service credential, not return it in any HTTP response and never instantiate this adapter in React. Neither source bytes nor attestation have been checked against a real RetailGrowthAI DEV customer asset in this PR.

No Azure Queue trigger is attached. No SQL claim is made, paid model enabled, job executed, commercial image licensed, poster published or hosted storage mutated. Developer synthetic fixtures cannot justify live provider activation. Existing #640/#641/#644 sources are merged and postmerge CI verified; this PR requires its own exact-head four CI jobs and coordinator main integration. No WineShopPOS or PROD change.

Next: human/independent source-rights authority and immutable evidence backend; reviewed protected generated PNG binary endpoint, gallery preview Blob revocation, actual queue claim/poison/manual recovery, Feature2/4/5/7 source consumers, live signed DEV E2E and Azure issue #249.
