# Feature3 GPU-OFF private generated-image output adapter

2026-10-28. **Source-only**, independent of Feature2/4/5/7 and prior Feature3 #553/#555/#559. The existing FLUX worker, prepaid bridge, GPU lifecycle and disabled hosted flags are preserved.

## Implemented

- `poster-engine/feature3_private_output_v1.py` implements the existing `OptionalGPUProvider.write_private_output(shop, job, raw_png, metadata)` callback shape without starting GPU. The trusted worker supplies actual bytes; source tests use only Pillow-generated synthetic PNGs. Canonical UUIDv4 shop/job/claim/source identifiers, one attempt, provider/license provenance, bounds and mandatory human review flag are checked.
- Reject absent/oversized/animated/malformed PNG, embedded EXIF/XMP, bad dimensions, mismatched SHA, manipulated prices/durations, unauthorized job/rights and forged metadata before any upload. Derive exact private content-addressed `{shop}/feature3/gpu/{job}/{sha256}.png` key, never accept a browser object path.
- Require fresh source rights twice, including **after** private object staging. Verify exact private SHA/object/size upload ACK. If rights are revoked after a confirmed stage, request quarantining before DB insert.
- The injected **trusted** `commit` callback MUST be a single transaction/compare-and-swap locking current claim lease, source rights, subscription and registered media state; this source adapter is **not** the actual SQL RPC, schema release or hosted Storage transport. The callback returns an exact `GENERATED`, `UNREVIEWED` immutable registered media receipt, and the outward receipt contains no object path, image bytes, token URL or review/publish approval.
- When upload acknowledgement or DB registration is ambiguous, fail closed and **do not automatically retry, delete, settle a billed job, or infer a successful commit**. Separate privileged reconciliation/poison handling is still required.
- `tests/media/test_feature3_private_output.py`: 11 tests (valid synthetic private receipt, denied claim/rights/hash/metadata/oversize, revoked-after-stage quarantine, invalid ACK, no unsafe retries). The normal FFmpeg CI runs `tests/media/test_*.py`.

## Still blocked / not claimed

Actual protected service-role Storage object staging and one-shot PostgreSQL media registration CAS are **not implemented** in this source module. Neither real private Storage writes nor live SQL inserts were performed. A full GPU job still requires legitimate licensed source, actual successful FLUX inference, authoritative output registration, measured charge settlement/reconciliation, human identity/garment-fidelity verification and signed DEV acceptance.

Deployment of earlier Feature3 migrations, existing approval/reviewer HTTP flags, Azure #249 reliability validation and any actual paid GPU run all require separate authorization. GPU remains OFF; no paid inference, hosted resources, PROD or WineShopPOS touched. Coordinator must review source PR, verify four checks on exact head, merge under branch ownership rules and check independent `main` CI. This PR alone does not satisfy Feature3 GPU-OFF DEVELOPMENT COMPLETE.
