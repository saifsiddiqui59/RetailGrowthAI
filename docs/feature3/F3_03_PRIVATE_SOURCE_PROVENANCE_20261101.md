# F3-03 / F3-13 — private source provenance and HTTP metadata hardening

**Original task IDs:** F3-03 (trusted source-rights/byte verifier), F3-13 (cross-tenant, rights and ambiguous-ACK regressions). **Status:** SOURCE-ONLY IN PROGRESS; do not mark hosted/integrated DONE.

**Baseline:** main `456b1757d7df2f0cc28a5ef6c8ba203b18380948`, branch `feat/feature3-f3-03-private-source-provenance-transport-20261101`. Existing open PRs #858/#859/#860/#861/#862/#863/#864 remain separate. This branch does **not** modify their worker input reader, generated PNG HTTP route, browser Blob lifecycle, model catalog, coordinator ledger or shared interfaces.

## Distinct independent source defect

The existing `Feature3TrustedPrivateSourceProof` trusts the *shape* of a PostgREST registered source row only partially. A non-string `mime_type` can raise a `TypeError` during dictionary membership; malformed commercial-provenance URL/attribution may be passed to the independent review adapter before being rejected; an injected HTTP response with non-mapping `headers` or non-string `Content-Type` can raise `AttributeError` instead of a bounded `SourceProofDenied`. These malformed inputs must never produce a private source attestation or a paid GPU job plan.

## Scoped change and regression

- In `azure-functions/campaign-api/feature3_private_source_proof.py`, reject non-string MIME/license types, missing or unbounded/unsafe license URLs, attribution with control characters or >200 characters, and non-HTTPS credentialed/noncanonical URL declarations **before** private Storage GET. A declared license URL is metadata only, **never** independent rights proof.
- Validate HTTP response header accessor and `Content-Type` value types before using them. Preserve existing exact origin, private path, immutable SHA, Pillow, Content-Length, Content-Encoding, double current rights review, GPU-OFF and no raw signed URL behavior.
- Extend `tests/api/test_feature3_private_source_proof.py` with malformed source metadata, URL/attribution, forged transport header and valid declared CC0 URL-but-unapproved rights negative cases. Fixtures are fictional; test calls use fake HTTP transport and an explicit independent rights callback double, not real licensed media.

## Acceptance and remaining blockers

1. Verify targeted `tests/api/test_feature3_private_source_proof.py` and the mandatory four-job exact-final-head GitHub Part 1 CI. The Python CI job discovers `tests/api`.
2. Require an **independent** private-media rights/security review before integrating to main, because this changes service-role source-proof authorization. Verify changed paths and current main, then fresh postmerge main 4/4. Do not bypass review or infer it from green CI.
3. Original F3-03/F3-13 hosted completion remains blocked on independently licensed adult/model/garment rights, a current approved source-rights authority, real signed DEV negative tests, approved no-URL private binary route, #249 host reliability and separate paid inference approval. No hosted SQL, DEV/PROD cloud changes, GPU, media samples, queue dispatch or WineShopPOS changes in this PR.

**NEXT ACTION:** Inspect exact-final-head CI and independent review; if review is unavailable, keep PR open and work on other nonoverlapping original tasks. Do not append `integrated_done` receipts or modify immutable `coordination/feature_tasks.json`.

## 2026-11-01 follow-up: do not fetch revoked model originals before current approval

- Existing model-library originals have an immutable SHA-named private Storage key. Previously the backend used its service key to **read the original bytes before any independent current-rights check**. An unlicensed/revoked model should not be fetched at all.
- `Feature3TrustedPrivateSourceProof.__call__` now obtains an independent current model/source rights attestation using that **candidate key digest before** the service-owned private GET. It still hashes the **actual** private pixels, rejects any digest mismatch, and rechecks the same rights revision/approval after the read. A key-name digest is not itself a byte attestation or commercial approval.
- Targeted regression in `tests/api/test_feature3_private_source_proof.py` now asserts the call sequence `review -> GET -> review`, denial **without any GET** for initially unapproved model originals, denial on mid-read revocation and a successful generic-upload path. Generic non-SHA private media **cannot be preauthorized from a known digest** in this adapter and still performs two independent post-read checks; that limitation must remain explicit pending a separately reviewed immutable digest contract.
- **Status remains SOURCE-ONLY IN PROGRESS.** This additional sensitive private-read authorization change requires fresh exact-final-head four-job CI and independent private-media/security review before any merge; no self-approval or hosted DONE. The canonical task register remains unchanged.

## 2026-11-02 — F3-03/F3-13 independent continuation: malformed private HTTP + rights outages
- **Existing PR:** #865, same branch and original task IDs. Latest pre-batch main `456b1757d7df2f0cc28a5ef6c8ba203b18380948`. Previous exact-head `b5f525cd0a7e7a05147d7063b3ef85303453e530` CI #41332355450 passed 4/4, but is **superseded** by this new code and cannot authorize a merge.
- **Source fix:** private service-key HTTP response now explicitly requires callable URL/status/read methods; malformed headers that throw TypeError/AttributeError become a bounded `SourceProofDenied`. A rights callback throwing timeout/connection/runtime failure becomes `SourceProofDenied`, never an approved source receipt or a reason to fetch a SHA-named model original. Real SHA, two independent review checks and no-redirect/size/Pillow guards remain unchanged.
- **Regression:** new cases in `tests/api/test_feature3_private_source_proof.py` exercise missing HTTP methods, a throwing headers accessor, independent reviewer outage **before** model-original private GET, and generic upload reviewer outage after bytes (no false pre-read protection claim). Synthetic offline fixtures only.
- **NEXT ACTION:** inspect mandatory new exact-final-head 4/4 GitHub CI and repair any failures. Obtain **independent** Feature3 private-media/service-key authorization review of the changed diff, recheck latest main and effective protected merge rules, then only merge if authorized; require fresh main 4/4 and reviewed original-ID progress evidence. F3-03/F3-13 remain SOURCE-ONLY IN PROGRESS and **0/33 hosted**. The generic upload's lack of immutable pre-read digest remains a separate versioned contract dependency. No GPU/paid models, hosted SQL, PROD, customer media or WineShopPOS touched.
