"""F3-08: adapt an RLS-validated minimal private generated PNG receipt.

The underlying TenantStore already checks the exact tenant, job, asset,
bucket, source, path and MIME against the user's JWT/RLS query. This adapter
restores identity fields required by the second, independent reader fence.
It does not grant media rights, approve models, or issue signed URLs.
"""
import re
from tenant_store import canonical_uuid

_SHA_PNG = re.compile(r"[a-f0-9]{64}\.png\Z")


class VerifiedGeneratedAssetTenant:
    def __init__(self, tenant):
        if not all(callable(getattr(tenant, name, None)) for name in
                   ("member", "feature3_gpu_job", "feature3_generated_asset")):
            raise ValueError("RLS tenant adapter required")
        self._tenant = tenant
        self.origin = tenant.origin
        self.key = tenant.key

    def member(self, token, actor, shop):
        return self._tenant.member(token, actor, shop)

    def feature3_gpu_job(self, token, shop, job):
        return self._tenant.feature3_gpu_job(token, shop, job)

    def feature3_generated_asset(self, token, shop, job, asset_id):
        shop, job, asset_id = map(canonical_uuid, (shop, job, asset_id))
        receipt = self._tenant.feature3_generated_asset(token, shop, job, asset_id)
        if type(receipt) is not dict:
            return None
        prefix = f"{shop}/feature3/gpu/{job}/"
        path = receipt.get("object_path")
        if (type(path) is not str or not path.startswith(prefix)
                or not _SHA_PNG.fullmatch(path[len(prefix):])
                or type(receipt.get("mime_type")) is not str
                or receipt["mime_type"] != "image/png"):
            return None
        expected = {"id": asset_id, "shop_id": shop,
                    "storage_bucket": "retailgrowth-media",
                    "source": "GENERATED"}
        if any(name in receipt and
               (type(receipt[name]) is not str or receipt[name] != value)
               for name, value in expected.items()):
            return None
        return {**receipt, **expected}
