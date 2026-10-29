"""Service-only Feature3 worker composition for existing durable GPU jobs.

Connect the pre-existing one-shot PostgREST claim/reservation/output CAS with
immutable Supabase Storage POST + independent byte-for-byte readback. Does not
create a job, authorize a model, turn on GPU, fetch weights or send a queue
message. The caller MUST supply genuine current tenant/source-rights and
private-asset readers, and independently measured provider cost.

No user JWT, browser callback, public URL or customer asset should be used in
this module. A failed or ambiguous output CAS is never automatically replayed.
"""
from __future__ import annotations

from ai_providers_v2 import ProviderBlocked
from feature3_gpu_prepaid_bridge import PrepaidGPUJobCallbacks
from feature3_private_output_storage import Feature3PrivateOutputStorage
from feature3_private_output_v1 import PrivateOutputRegistrar


_EXPECTED_COMMIT = frozenset((
    "shop_id", "job_id", "claim_token", "attempt", "media_asset_id",
    "image_sha256", "private", "review_status",
))
_EXPECTED_RESERVATION = frozenset((
    "reservation_id", "shop_id", "job_id", "attempt",
    "claim_token", "reserved_usd",
))


class Feature3PrivateGPUWorker:
    """Bind existing service-only SQL and private Storage to one guarded worker.

    service must supply the existing Feature3GPUServiceStore methods: claim,
    read_prepaid_reservation, commit_private_output and finish. The service
    methods independently verify the one-shot SQL lease and final CAS.

    current_rights(shop, job, claim_token, source_ids) must independently
    re-evaluate actual shop subscription, approved model/garment rights,
    current revisions and revoked/foreign sources at EVERY call. Do not
    replace this with caller-supplied metadata or static True in production.
    """

    def __init__(self, *, provider, service, supabase_origin, backend_secret,
                 current_rights, resolve_private_inputs, trusted_meter_usd,
                 storage_transport=None):
        required = ("claim", "read_prepaid_reservation",
                    "commit_private_output", "finish")
        if not all(callable(getattr(service, method, None)) for method in required):
            raise ProviderBlocked("Exact service-only GPU RPC store is required")
        if not all(callable(fn) for fn in (
            current_rights, resolve_private_inputs, trusted_meter_usd,
        )):
            raise ProviderBlocked("Live media-rights, reader and billed usage meter required")
        if not callable(getattr(provider, "status", None)):
            raise ProviderBlocked("Separately gated GPU provider required")

        self.service = service
        self._rights = current_rights
        self.storage = Feature3PrivateOutputStorage(
            supabase_origin, backend_secret, transport=storage_transport,
        )
        self.registrar = PrivateOutputRegistrar(
            validate_claim=self._validate_claim,
            reauthorize=self._rights,
            stage=self.storage.stage,
            commit=self._commit,
            quarantine=self.storage.quarantine,
        )
        self.jobs = PrepaidGPUJobCallbacks(
            provider=provider,
            claim_rpc=service.claim,
            read_authorization=self._rights,
            resolve_private_inputs=resolve_private_inputs,
            read_prepaid_reservation=service.read_prepaid_reservation,
            register_private_output=self.registrar,
            trusted_meter_usd=trusted_meter_usd,
            finish_rpc=service.finish,
        )

    def _validate_claim(self, shop, job, attempt, token, sources, digest):
        # A previously verified claim could expire during expensive inference.
        # Fetch the authoritative SQL RUNNING lease and existing RESERVED
        # amount just before staging any private output. No new reservation.
        row = self.service.read_prepaid_reservation(shop, job, attempt, token)
        if (not isinstance(row, dict) or set(row) != _EXPECTED_RESERVATION or
            row.get("shop_id") != shop or row.get("job_id") != job or
            row.get("claim_token") != token or row.get("attempt") != attempt):
            raise ProviderBlocked("Missing current one-shot GPU reservation or lease")
        if self._rights(shop, job, token, sources) is not True:
            raise ProviderBlocked("Source rights revoked before Storage stage")
        return True

    def _commit(self, shop, job, attempt, token, key, digest, size, sources):
        # Existing Feature3GPUServiceStore validates the FULL SQL CAS result,
        # then intentionally returns this minimal service-only receipt. The
        # PrivateOutputRegistrar needs source and exact object identity too,
        # which are reconstructed exclusively from the same checked inputs.
        receipt = self.service.commit_private_output(
            shop, job, attempt, token, key, digest, size, sources,
        )
        if (not isinstance(receipt, dict) or set(receipt) != _EXPECTED_COMMIT or
            receipt.get("shop_id") != shop or receipt.get("job_id") != job or
            receipt.get("claim_token") != token or receipt.get("attempt") != 1 or
            receipt.get("image_sha256") != digest or
            receipt.get("private") is not True or
            receipt.get("review_status") != "UNREVIEWED"):
            raise ProviderBlocked("Private output SQL CAS unconfirmed; reconcile")
        return {**receipt, "object_path": key, "source": "GENERATED"}

    def execute(self, job):
        """Run only if the independently licensed, budgeted provider is ON.

        This method makes no policy decision to activate a paid model and
        performs no automatic retry after any uncertain Queue/Storage/SQL ACK.
        """
        return self.jobs.execute(job)
