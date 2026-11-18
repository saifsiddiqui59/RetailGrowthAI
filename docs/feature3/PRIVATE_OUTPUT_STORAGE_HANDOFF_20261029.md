# Feature3 private generated PNG stage/readback — source handoff (2026-10-29)

This adapter is **trusted worker source only**, no hosted execution or paid model. It is not a URL-serving API. Existing DB has the real version-31 private CAS RPC and ledger, but no real generated output or signed consumer run has been completed.

## Source
- `poster-engine/feature3_private_output_storage.py`: accept exact canonical `{shop_id}/feature3/gpu/{job_id}/{sha256}.png`, service-only Supabase URL/secret, actual Pillow-verified PNG (100 bytes..25 MiB), no-upsert POST to private `retailgrowth-media`, exact Storage ACK path, read-back GET exact binary equality+sha. No automatic retries after unknown writes; no public Storage paths, JWTs or signed URLs in returned receipts.
- `poster-engine/feature3_private_output_v1.py`: already-in-repo source-only `PrivateOutputRegistrar`, which calls current lease and rights callbacks before `storage.stage`, checks receipt, calls fresh rights again, and commits via a separate one-shot transactional SQL CAS callback. On revocation before CAS only, it calls `storage.quarantine`; a lost commit ACK **must never be automatically retried/deleted**.
- `tests/media/test_feature3_private_output_storage.py`: real synthetic PNG decode/sha with mocked HTTPS Supabase transport, mutation denial, ACK uncertainty, corrupted object, failure to delete on uncertain state, revoked-stage deletion, and secret/origin checks. Passing mock transport is not a live Storage acceptance test.

## Integrate in a private worker only

```python
from feature3_private_output_storage import Feature3PrivateOutputStorage
from feature3_private_output_v1 import PrivateOutputRegistrar
stage = Feature3PrivateOutputStorage(supabase_https_origin, backend_secret)
registrar = PrivateOutputRegistrar(
    validate_claim=trusted_current_one_shot_lease,
    reauthorize=trusted_current_shop_model_garment_rights,
    stage=stage.stage,
    commit=existing_feature3_gpu_sql_cas,
    quarantine=stage.quarantine,
)
# Never call registrar until an ACTUAL, independently authorized generated
# PNG exists, with current lease, source rights and bounded confirmed budget.
```

The adapter must be instantiated with a private service role key in a cloud worker, **never** sent to browser or GitHub CI. Complete live post-write/read-back/foreign-shop/permission/rights-revocation/expiry testing after approved deployment, under current RLS. Existing short-lived signed URLs already issued cannot necessarily be invalidated immediately; client-side link hiding is only defense-in-depth. Do not count queue ACK as GPU execution, virtual try-on or cost settlement.

No cloud resources, VTON inference, customer or WineShopPOS media were used to develop this code.

## 2026-10-29 follow-up — one-shot unknown-ACK fencing (source PR)
- The trusted worker now marks each exact `(shop_id, immutable SHA object key, one-shot claim token)` as attempted **before POST**, so malformed ACK, timeout or altered downloaded bytes cannot lead to a second POST inside that worker instance. Restart/replay must be reconciled against authoritative SQL and Storage rather than inferred safe from a new process.
- The quarantine callback is one-shot even if a DELETE times out: it consumes the locally confirmed pre-CAS stage permit **before** requesting deletion. A 2xx DELETE does not suffice; a fresh authenticated private exact-key GET must return confirmed **404** before returning True. Any 401/403, timeout, redirect, or still-present key is UNKNOWN and must be investigated; the worker must never repeat DELETE automatically.
- Positive/negative transport tests exercise post-readback SHA, 404-confirmed removal, deceptive 2xx deletion ACK, lost DELETE ACK, uncertain post-delete GET and stage POST replay denial. These are **mock network tests** with real Pillow-generated PNG bytes. The caller must invoke quarantine only on independently confirmed rights revocation **before** the SQL commit. A lost SQL CAS ACK is never eligible for this cleanup.
- Historical actual real OpenVTO inputs and sample 9-second FFmpeg footage remain in Actions runs #40829987383 and #40831572603; this hardening is independent of them, not new VTON/FLUX or customer assets. Original asset SHA256 is in the generated verified `manifest.json`; pinned upstream Git blob hashes are in `poster-engine/feature3_demo_inputs.py`.
- **Release:** until a real signed DEV storage execution and an explicit state reconciliation/worker deployment, label this source-only. CI and PR-head evidence must be inspected independently. Azure #249 remains unresolved, and already issued signed Storage URLs have their own expiry semantics.

## 2026-10-29 — Concrete trusted service composition (source-only)
- Added `poster-engine/feature3_private_gpu_runtime.py` with `Feature3PrivateGPUWorker` to **actually compose**, rather than leave as a sketch, the existing service-only `Feature3GPUServiceStore` methods `claim`, `read_prepaid_reservation`, `commit_private_output`, `finish`, immutable `Feature3PrivateOutputStorage` and prepaid `PrepaidGPUJobCallbacks`. The callback re-reads the authoritative SQL RUNNING/RESERVED lease immediately before output stage; source rights are read afresh by the trusted caller before and after stage; Storage must prove exact PNG bytes; the service-only one-shot CAS result is validated and converted into the private registrar's complete internal receipt. A lost SQL ACK never deletes or repeats output.
- `tests/media/test_feature3_private_gpu_runtime.py` executes CPU-only in-memory `OptionalGPUProvider` with Pillow bytes, injected mock PostgREST service and fake HTTPS private Storage: successful one-claim, two lease reads, one Storage POST/GET, one SQL CAS and one measured settlement; disabled provider has no IO; stale/foreign claim, corrupted staged bytes, revoked rights and ambiguous SQL CAS must fail closed. The test's local config `gpu_deployed=true` **only activates a fake synchronous in-memory runner**, never a real provider or billable endpoint.
- No Azure entrypoint/queue deployment, credential changes, real tenant rights reader, curated source, paid inference, cloud settlement or signed DEV E2E is implied. Production must inject actual current shop rights and real source byte loader; never replace test lambdas with `lambda: True`. This branch is separate from financial unknown-output settlement PR #632 and the Storage one-shot/quarantine PR #629; all three must pass review and be integrated before any hosted activation.
