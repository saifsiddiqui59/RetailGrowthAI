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
