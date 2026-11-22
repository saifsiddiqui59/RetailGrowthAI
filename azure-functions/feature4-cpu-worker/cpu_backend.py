"""Native Feature4 CPU worker-only adapters. Deliberately outside the v1 ZIP.

Only an isolated F4 worker can import this module. Never expose its AdminStore
or private Storage credentials through a browser or the legacy render queue.
"""
from hashlib import sha256
from pathlib import Path

from tenant_store import StorageUnavailable


class Feature4CpuAdmin:
    def __init__(self, store):
        self.store = store

    def render_status(self, job_id):
        return self.store.feature4_render_status(job_id)

    def claim_feature4_render(self, job_id):
        return self.store.claim_feature4_render(job_id)

    def render_authorized(self, claim):
        return self.store.feature4_render_authorized(claim)

    def feature4_claim_current(self, claim):
        return self.store.feature4_claim_current(claim)

    def load_feature4_bundle(self, claim):
        return self.store.feature4_load_bundle(claim)

    def complete_feature4_render(self, claim, object_path, proof, rendered_as):
        return self.store.complete_feature4_render(
            claim, object_path, proof, rendered_as)

    def render_failure(self, claim, code, permanent=False):
        return self.store.feature4_render_failure(
            claim, code, permanent=permanent)


class VerifiedFeature4Media:
    """Only return an output key after independent remote SHA-256 readback."""

    def __init__(self, media):
        self.media = media

    def download(self, shop_id, key, destination):
        return self.media.download(shop_id, key, destination)

    def upload(self, shop_id, job_id, media_file, *, lease_token):
        output = Path(media_file)
        if output.is_symlink() or not output.is_file():
            raise StorageUnavailable("untrusted local CPU render path")
        digest = sha256()
        with output.open("rb") as reader:
            for data in iter(lambda: reader.read(1024 * 1024), b""):
                digest.update(data)
        key = self.media.upload(shop_id, job_id, output, lease_token=lease_token)
        if self.media.verify_uploaded_mp4(shop_id, key, digest.hexdigest()) is not True:
            raise StorageUnavailable("private output checksum not verified")
        return key
