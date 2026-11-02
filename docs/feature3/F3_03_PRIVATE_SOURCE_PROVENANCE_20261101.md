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

## 2026-11-02 — F3-03/F3-13 private HTTP runtime outage boundary

- Continued existing PR #865, not a duplicate source PR. The service-key private source reader already mapped HTTP/OSError/ValueError/TypeError/AttributeError to opaque `SourceProofDenied`, but a proxy or injected transport raising `RuntimeError` at open, status, header lookup or read escaped the intended private-read denial boundary.
- The existing `_private_bytes` error fence now maps `RuntimeError` to the same opaque denial. A targeted negative regression checks all four failure stages and confirms the model-original rights review is called **before** any private GET, but no post-read approval is performed on transport failure. Tests use synthetic Pillow bytes and fake transport only.
- This is error-contract hardening, **not** a new current-rights authority, source approval, hosted proof or inference. No change to GPU, paid models, hosted SQL, PROD or WineShopPOS.
- **Next:** verify final-head mandatory four-job PR CI after these commits, repair any failing tests on this branch, and obtain an independent private-media/service-key security review. Only then consider a safe current-main merge and fresh main 4/4. Original F3-03/F3-13 remain source-partial; 0/33 fully hosted accepted. Canonical task-ledger updates require a separate reviewed PR after accepted integration.

## 2026-11-02 — F3-03/F3-13 invisible commercial-provenance spoofing (source only)

- **Original IDs:** F3-03 trusted private source rights/bytes; F3-13 negative rights regression. Continue existing **PR #865** only; no overlapping changes to #859/#861/#862/#863/#864 or shared contracts.
- **Defect:** registered `attribution` accepted invisible Unicode bidi overrides/isolates, zero-width formatting, C1 controls, Unicode line/paragraph separators and lone surrogates. A raw string longer than 200 characters could also pass by trimming trailing whitespace. These can obscure displayed commercial provenance even though the independent current-rights authority remains mandatory.
- **Scoped source fix:** reject Unicode Cc/Cf/Cs/Zl/Zp characters and raw attribution lengths above 200 **before** any private Storage GET or independent rights callback. Preserve ordinary Unicode scripts, Indic combining marks, the immutable model SHA pre-read check, actual Pillow/SHA byte proof and the second current rights check. No changes to reviewer approval semantics or to GPU-off policy.
- **Regression:** 10 negative forged/padded attribution variants must produce `SourceProofDenied` with **zero** rights/Storage calls, plus a legitimate Marathi/Indic provenance positive control using synthetic Pillow bytes. Python test: `tests/api/test_feature3_private_source_proof.py`. GitHub Part 1 **four-job exact-final-head CI is mandatory and must be verified after this handoff commit**; earlier #41368102267 is stale for the new source.
- **Security/merge blocker:** independently submitted private-media/service-key and rights-display review of the complete #865 diff; then recheck main and exact-head 4/4, only merge if authorized, and require fresh main 4/4 before reviewed original-ID source ledger evidence. Separate shared documentation and task-receipt proposals #858/#860 are still unmerged and review-gated. Hosted signed rights, real licensed customer assets, no-URL route #471/#325, Azure #249 and genuine paid inference approvals remain external. **F3-03/F3-13 IN PROGRESS, 0/33 hosted accepted.** No GPU/paid inference, hosted SQL, PROD, unlicensed media or WineShopPOS touched.

## 2026-11-02 — F3-03/F3-13 full private-image pixel decode gate (source only)

- **Existing PR #865 / original IDs F3-03 and F3-13.** Independent local Pillow reproduction showed that `Image.verify()` can accept a JPEG missing its final bytes while `Image.load()` fails: a valid SHA of a corrupted private JPEG must not be mistaken for a usable, independently reviewed original.
- The source proof now reopens each size/format-bounded private image and forces a full pixel decode after structural verification and before emitting the SHA receipt or performing the final current-rights check. Invalid compressed pixels produce opaque `SourceProofDenied`. This preserves pre-read model approval, actual SHA matching, current rights revision recheck, private HTTPS only and GPU OFF.
- Three deterministic truncated JPEG negatives (2/20/80 missing bytes) establish the former `verify()` blind spot and require denial after a single pre-read rights check and one private GET, **without** post-read approval. Existing valid PNG/JPEG/WebP controls remain. All fixtures are generated offline; no commercial/hosted media or model execution.
- **Next action:** verify the new exact-head mandatory four-job CI; fix any failure without weakening tests. Obtain independent private-media/security and rights review before merging #865; after any authorized merge verify fresh main 4/4, then propose reviewed original-ID evidence receipts. F3-03/F3-13 remain source-partial and **0/33 hosted accepted**. Do not modify hosted SQL, PROD, GPU, WineShopPOS or shared task ledgers.

## 2026-11-02 — F3-03/F3-13 service-key URL/header canonicalization (source only)

- Continue existing PR #865; original F3-03/F3-13, no new task IDs. Python's URL parser can silently strip C0 whitespace, CR/LF and TAB; an ambiguous Supabase Storage origin must not reach the service-key HTTP request. The origin parser now requires bounded printable ASCII and an exact canonical HTTPS origin, rejecting even empty query/fragment markers.
- Backend service-key and legacy JWT HTTP header values must be bounded printable ASCII, excluding DEL, Unicode and CR/LF, before constructing an authenticated request. Existing ordinary `sb_secret_` and legacy JWT shapes remain supported. Regression cases cover malformed origins/credentials and valid canonical configurations.
- Source-only deterministic tests; no real keys, Storage GET, hosted media, paid inference, GPU, SQL, PROD or WineShopPOS. **NEXT ACTION:** verify final-head four-job CI, obtain independent private-media/service-key security review of complete PR #865, recheck main and only merge if authorized; require fresh main 4/4 before reviewed F3-03/F3-13 receipts. Hosted 0/33; no original task DONE.

## 2026-11-02 — F3-03/F3-13 opaque private HTTP adapter and bounded length (source only)

- Continued existing PR #865 without duplicating F3-03/F3-13 work. A service-owned private Storage proxy can raise ordinary exceptions outside the previous explicit HTTP/RuntimeError list; these must not leak implementation details or permit a final current-rights receipt. The reader now rethrows deliberate `SourceProofDenied` and maps all other ordinary adapter exceptions to an opaque denial, without swallowing process-control `BaseException`.
- Bound `Content-Length` to 1–8 ASCII decimal digits (25 MB maximum) before integer parsing or reading private bytes. This rejects excessively long numeric headers, including zero-padded values that would otherwise be accepted.
- Offline regressions cover four proxy failure stages across four exception families and three oversized numeric header encodings; require one pre-read model rights check, one attempted private GET, zero post-read approval. Existing successful real Pillow image checks and independent current-rights barriers remain.
- **NEXT ACTION:** Verify exact-final-head mandatory 4/4 GitHub PR CI, repair any failure, then obtain independent private-media/service-key security review. No merge or original task DONE until independent approval, current-main compatibility and fresh postmerge main 4/4. F3-03/F3-13 source partial; hosted 0/33. No GPU, paid inference, hosted SQL, PROD, unauthorized media or WineShopPOS changes.

## 2026-11-02 — F3-03/F3-13 private response-header folding and Unicode denial

- Continued existing PR #865 (no new task IDs or duplicate PR). Existing final-head `adcd4362` PR CI #41483285480 passed all four mandatory jobs; independent private-media/security reviews remain absent, so that prior green head was **not merge-authorized**.
- The service-key private Storage response previously accepted `Content-Type: image/png\r\n` and `Content-Encoding: identity\n` after stripping whitespace; it also accepted invisible bidi Unicode and unbounded media parameters. This new source-only guard requires bounded printable ASCII for present Content-Type and Content-Encoding before any private body read, while retaining legitimate printable MIME parameters and padded `identity` values.
- Offline regressions deny eight folded, Unicode and oversized header values before pixel read and without a post-read rights receipt, plus one positive compatibility case. The immutable model pre-read rights check, actual SHA/Pillow decode and final independent review remain mandatory.
- **NEXT ACTION:** verify mandatory exact-new-head 4/4 CI; repair failures in this PR if needed; obtain independent private-media/service-key security review of the complete diff; only then consider main merge and fresh main 4/4. F3-03/F3-13 source partial, **0/33 hosted accepted**. No GPU, paid inference, hosted SQL, PROD, unauthorized media or WineShopPOS changes.


## 2026-11-03 — F3-03/F3-13 ambiguous provenance URL parser denial

- Continuing existing PR #865 on its unchanged branch, not opening a duplicate. Python urlsplit accepted declared HTTPS licence URLs containing backslashes or invalid percent escapes, which can be interpreted differently by browser URL parsers and misrepresent displayed commercial-rights provenance.
- The _license_url validator now denies those ambiguous declarations before any private Storage GET or independent reviewer callback; valid percent-encoded HTTPS metadata remains supported. These declarations still never prove commercial rights. Added offline negative and positive regression cases to tests/api/test_feature3_private_source_proof.py.
- Mandatory final-head four-job CI and independent private-media/rights security review remain merge gates. F3-03/F3-13 remain source-partial; no hosted acceptance, paid GPU/inference, hosted SQL, PROD or WineShopPOS action.
- NEXT ACTION: verify exact-head Python/frontend/FFmpeg/Supabase 4/4, fix any failures, obtain independent review, then reassess current main before any authorized merge. Keep original task ledger unchanged until postmerge evidence.

## 2026-11-03 — F3-03/F3-13 ambiguous URL authority canonicalization (source only)

- Continued existing PR #865 after confirming preceding exact-head CI #41501647302 **4/4 PASS** at `9e765597`; no independent security/rights reviews were present, so no merge was authorized.
- `_license_url` now rejects percent-encoded host authority, an empty explicit port and zero-padded :443 forms that Python accepts but browser URL handling may normalize differently. Canonical explicit :443 and percent-encoded path remain accepted as *declarations only*, never evidence of commercial permission.
- Five new fail-closed negative cases require zero rights-review/Storage calls, plus a valid :443 positive control. Synthetic offline tests only; no model inference, hosted SQL, DEV/PROD deployment, customer media or WineShopPOS changes.
- **NEXT ACTION:** verify mandatory exact-new-head Python/frontend/FFmpeg/Supabase 4/4; repair failures without weakening tests. Obtain independent private-media/rights/security review of complete #865, then recheck current main/merge policy and merge only if eligible. After any authorized merge verify fresh main 4/4 before proposing reviewed original F3-03/F3-13 ledger receipts. Source partial; **0/33 hosted accepted**.

## 2026-11-03 — F3-03/F3-13 stable registered-row rights snapshot (source only)

- Existing PR #865, original F3-03/F3-13: snapshot the exact authoritative PostgREST media row before path/MIME validation and preserve that immutable snapshot through private Storage GET and both independent rights checks. This prevents a caller or injected transport callback from changing the licence, attribution or MIME metadata after the pre-read attestation but before the post-read review. Reject custom mapping subclasses at the private service-key boundary.
- Two deterministic offline regressions cover mid-read caller mutation and mutable mapping subclass denial; no real media, network, provider, GPU, SQL or PROD action.
- Previous head `272784951f30e512568fd21479264a0ad74a26db` had four successful CI jobs in run #41511844372; that evidence becomes stale on this change. **NEXT ACTION:** verify new exact-head four-job CI, repair any failures, obtain independent private-media/service-key and commercial-rights review, recheck current main, and merge only if independently authorized. After authorized merge require fresh main 4/4 and reviewed original-ID ledger receipt. F3-03/F3-13 source-partial; hosted 0/33. No WineShopPOS changes.
