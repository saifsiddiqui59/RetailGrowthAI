"""Read-only Feature3 GPU job planning from actual service-role PostgREST state.

The Azure Queue payload supplies ONLY IDs. A plan must be reconstructed from
the authoritative job, versioned design, active author, subscription, model
review, and exact registered private images. Independently reviewed current
media rights AND byte SHA attestation are required for each source.

This module never claims a GPU job, starts inference, reserves usage, sends a
queue message, settles spend, or returns private object paths/credentials.
A preflight receipt is NOT GPU authorization: actual workers must re-check
rights and single-use lease after an approved provider is enabled.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

from tenant_store import canonical_uuid, StorageUnavailable

_SHA = re.compile(r"^[a-f0-9]{64}$")
_SUPPORTED = {"image/png", "image/jpeg", "image/webp"}
_LICENSES = {"owned", "cc0", "commercial", "royalty_free"}


class Feature3PlanDenied(PermissionError):
    """A generic denial, never revealing foreign shop/model/media existence."""


def _single(store,table,shop,identifier,columns):
    rows = store.request(table, query={
        "select":columns,"shop_id":"eq."+shop, "id":"eq."+identifier,"limit":"2",
    })
    if not isinstance(rows,list) or len(rows) != 1 or not isinstance(rows[0],dict):
        raise Feature3PlanDenied("Authoritative shop job/design unavailable")
    return rows[0]


def _time(value):
    if type(value) is not str:
        raise Feature3PlanDenied("Current subscription timestamps required")
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise Feature3PlanDenied("Current subscription timestamps required") from exc
    if dt.tzinfo is None:
        raise Feature3PlanDenied("Timezone-aware subscription required")
    return dt.astimezone(timezone.utc)


def _uuid(value):
    try:
        return canonical_uuid(value)
    except (ValueError,TypeError,AttributeError) as exc:
        raise Feature3PlanDenied("Canonical source ID required") from exc


class Feature3GPUJobPlanPreflight:
    """Live, strict, NO-GPU read-only SQL/media current-rights preflight.

    source_proof(shop_id, registered_media_row) is a trusted private backend
    verifier of **actual immutable image bytes, separate legal/source approval
    and revoked/current rights**. A browser-supplied model, filename hash or
    declared media license must never satisfy that verifier.
    """

    def __init__(self, *, admin_store, source_proof):
        if not callable(getattr(admin_store,"request",None)) or not callable(source_proof):
            raise ValueError("Trusted service PostgREST and source verifier required")
        self.store=admin_store
        self.proof=source_proof

    def _snapshot(self, shop, job, claimed_token=None):
        s=self.store
        j=_single(s,"feature3_gpu_jobs",shop,job,
            "id,shop_id,requested_by,design_id,design_revision,design_server_sha256,status,attempts,claim_token,lease_until,output_asset_id")
        if (j.get("id") != job or j.get("shop_id") != shop or
                j.get("output_asset_id") is not None or
                type(j.get("design_revision")) is not int or
                not 1 <= j["design_revision"] <= 1_000_000 or
                not isinstance(j.get("design_server_sha256"),str) or
                not _SHA.fullmatch(j["design_server_sha256"])):
            raise Feature3PlanDenied("Job is not a current GPU plan")
        if claimed_token is None:
            if (j.get("status")!="QUEUED" or j.get("attempts")!=0 or
                    j.get("claim_token") is not None or
                    j.get("lease_until") is not None):
                raise Feature3PlanDenied("Only fresh unclaimed plan allowed")
        elif (j.get("status")!="RUNNING" or j.get("attempts")!=1 or
              j.get("claim_token")!=claimed_token or
              not isinstance(j.get("lease_until"),str)):
            raise Feature3PlanDenied("Current one-shot claimed job unavailable")
        actor,design=_uuid(j.get("requested_by")),_uuid(j.get("design_id"))
        members=s.request("shop_memberships",query={
            "select":"shop_id,user_id,role,active",
            "shop_id":"eq."+shop,"user_id":"eq."+actor,"active":"eq.true",
            "limit":"2"})
        if (not isinstance(members,list) or len(members)!=1 or
                members[0].get("shop_id")!=shop or
                members[0].get("user_id")!=actor or
                members[0].get("active") is not True or
                members[0].get("role") not in ("OWNER","EDITOR")):
            raise Feature3PlanDenied("Job author not currently eligible")
        subscriptions=s.request("shop_subscriptions",query={
            "select":"shop_id,status,valid_from,valid_until,period_start,period_end",
            "shop_id":"eq."+shop,"limit":"2"})
        if (not isinstance(subscriptions,list) or len(subscriptions)!=1 or
                subscriptions[0].get("shop_id")!=shop or
                subscriptions[0].get("status") not in ("TRIAL","ACTIVE")):
            raise Feature3PlanDenied("Current subscription unavailable")
        sub=subscriptions[0]
        now=datetime.now(timezone.utc)
        if not (_time(sub.get("valid_from")) <= now < _time(sub.get("valid_until"))
                and _time(sub.get("period_start")) <= now < _time(sub.get("period_end"))):
            raise Feature3PlanDenied("Subscription expired or not started")
        d=_single(s,"feature3_poster_designs",shop,design,
                  "id,shop_id,revision,status,server_document_sha256,design")
        if (d.get("id")!=design or d.get("shop_id")!=shop or
                d.get("status")!="DRAFT" or
                d.get("revision")!=j["design_revision"] or
                d.get("server_document_sha256")!=j["design_server_sha256"]):
            raise Feature3PlanDenied("Versioned poster design changed")
        body=d.get("design")
        if (not isinstance(body,dict) or
                body.get("schema")!="retailgrowth.poster.v2" or
                body.get("shop_id")!=shop or
                not isinstance(body.get("layers"),list) or
                not 1 <= len(body["layers"]) <= 24):
            raise Feature3PlanDenied("Untrusted versioned poster layers")
        ids=[]
        for layer in body["layers"]:
            if not isinstance(layer,dict) or layer.get("type") not in ("text","rect","image"):
                raise Feature3PlanDenied("Untrusted image source layer")
            if layer["type"]=="image":
                ids.append(_uuid(layer.get("asset_id")))
        unique=tuple(sorted(set(ids)))
        if not 1 <= len(unique) <= 12:
            raise Feature3PlanDenied("No bounded registered private image sources")
        assets=s.request("media_assets",query={
            "select":"id,shop_id,storage_bucket,object_path,mime_type,source,license_name,license_url,attribution",
            "shop_id":"eq."+shop,
            "id":"in.("+",".join(unique)+")","limit":"13"})
        if not isinstance(assets,list) or len(assets)!=len(unique) or any(
                not isinstance(x,dict) for x in assets):
            raise Feature3PlanDenied("Private registered sources unavailable")
        by_id={}
        for row in assets:
            asset=_uuid(row.get("id"))
            key=row.get("object_path")
            if (asset not in unique or asset in by_id or
                    row.get("shop_id") != shop or
                    row.get("storage_bucket") != "retailgrowth-media" or
                    row.get("mime_type") not in _SUPPORTED or
                    row.get("source") not in ("UPLOAD","GENERATED") or
                    row.get("license_name") not in _LICENSES or
                    not isinstance(row.get("attribution"),str) or
                    len(row["attribution"].strip()) < 10 or
                    (row.get("license_name")!="owned" and
                     (not isinstance(row.get("license_url"),str) or
                      not row["license_url"].startswith("https://"))) or
                    not isinstance(key,str) or
                    not key.startswith(shop+"/") or len(key)>256 or
                    any(c in key for c in ("..","\\","%","?","#")) or "//" in key):
                raise Feature3PlanDenied("Private source ownership or rights invalid")
            by_id[asset]=row
        models=s.request("feature3_models",query={
            "select":"owner_shop_id,model_id,media_asset_id,status,rights_verified,synthetic_adult,approved_uses,rights_revision,image_sha256",
            "owner_shop_id":"eq."+shop,
            "media_asset_id":"in.("+",".join(unique)+")",
            "limit":"13"})
        if not isinstance(models,list) or len(models)>len(unique):
            raise Feature3PlanDenied("Untrusted model catalog approval")
        model_ids=set()
        for model in models:
            if not isinstance(model,dict):
                raise Feature3PlanDenied("Untrusted model approval")
            asset=_uuid(model.get("media_asset_id"))
            if (asset not in by_id or asset in model_ids or
                    model.get("owner_shop_id")!=shop or
                    model.get("status")!="APPROVED" or
                    model.get("rights_verified") is not True or
                    model.get("synthetic_adult") is not True or
                    type(model.get("approved_uses")) is not list or
                    not 1 <= len(model["approved_uses"]) <= 3 or
                    any(type(use) is not str or
                        use not in ("poster","try_on","video_reference")
                        for use in model["approved_uses"]) or
                    len(set(model["approved_uses"])) != len(model["approved_uses"]) or
                    "poster" not in model["approved_uses"] or
                    type(model.get("rights_revision")) is not int or
                    model["rights_revision"] < 2 or
                    not isinstance(model.get("image_sha256"),str) or
                    not _SHA.fullmatch(model["image_sha256"])):
                raise Feature3PlanDenied("Model source review revoked or stale")
            model_ids.add(asset)
        return {"job":j,"design":d,"member":members[0],
                "subscription":sub,"assets":by_id,"models":models,"ids":unique}

    def _check(self, shop_id, job_id, claimed_token=None):
        shop,job=_uuid(shop_id),_uuid(job_id)
        snapshot=self._snapshot(shop,job,claimed_token)
        verified=[]
        model_hashes={m["media_asset_id"]:m["image_sha256"] for m in snapshot["models"]}
        for asset in snapshot["ids"]:
            raw=self.proof(shop,dict(snapshot["assets"][asset]))
            if (not isinstance(raw,dict) or set(raw)!={
                "shop_id","asset_id","image_sha256","rights_revision",
                "private_bytes_verified","independent_license_verified",
                "current_customer_approval","rights_revoked"
            } or raw.get("shop_id")!=shop or raw.get("asset_id")!=asset or
                not isinstance(raw.get("image_sha256"),str) or
                not _SHA.fullmatch(raw["image_sha256"]) or
                type(raw.get("rights_revision")) is not int or
                raw["rights_revision"]<1 or
                raw.get("private_bytes_verified") is not True or
                raw.get("independent_license_verified") is not True or
                raw.get("current_customer_approval") is not True or
                raw.get("rights_revoked") is not False or
                (asset in model_hashes and
                 raw["image_sha256"]!=model_hashes[asset])):
                raise Feature3PlanDenied("Current private bytes or independent rights unconfirmed")
            verified.append((asset,raw["image_sha256"],raw["rights_revision"]))
        # Model and tenant rights might change during actual private image
        # verification. Re-read all authoritative SQL rows; any divergence
        # denies preflight. Workers must check AGAIN after paid job claim.
        after=self._snapshot(shop,job,claimed_token)
        if after!=snapshot:
            raise Feature3PlanDenied("Source/lease/role changed during GPU preflight")
        # Re-run the independently authorized bytes/right revocation proof,
        # not just SQL metadata. Rights may be revoked without DB row drift.
        for asset,known_sha,known_revision in verified:
            fresh=self.proof(shop,dict(after["assets"][asset]))
            if (not isinstance(fresh,dict) or set(fresh)!={
                "shop_id","asset_id","image_sha256","rights_revision",
                "private_bytes_verified","independent_license_verified",
                "current_customer_approval","rights_revoked"
            } or fresh.get("shop_id")!=shop or fresh.get("asset_id")!=asset or
                fresh.get("image_sha256")!=known_sha or
                fresh.get("rights_revision")!=known_revision or
                fresh.get("private_bytes_verified") is not True or
                fresh.get("independent_license_verified") is not True or
                fresh.get("current_customer_approval") is not True or
                fresh.get("rights_revoked") is not False):
                raise Feature3PlanDenied("Current source rights changed after DB read")
        return {"shop_id":shop,"job_id":job,
                "source_asset_ids":snapshot["ids"],
                "source_sha256s":tuple(x[1] for x in verified),
                "rights_revisions":tuple(x[2] for x in verified),
                "preflight_verified":True,"provider_call_permitted":False,
                "gpu_started":False,"claim_performed":False,
                "paid_retry_authorized":False}

    def check(self, shop_id, job_id):
        """Existing GPU-OFF queue-inspection contract: zero claims."""
        return self._check(shop_id,job_id)

    def check_claimed(self, shop_id, job_id, claim_token, source_asset_ids,
                      read_prepaid_reservation):
        """Revalidate real one-shot RUNNING lease + sources without invoking GPU.

        Call only from a service-owned worker after a separately gated claim.
        This method does not claim, extend lease, bill, download model weights,
        ACK the queue, or authorize a provider. All rights and real image
        bytes are checked twice, with a full DB snapshot refresh in between.
        """
        shop,job,token=map(_uuid,(shop_id,job_id,claim_token))
        if not callable(read_prepaid_reservation):
            raise Feature3PlanDenied("Actual service-side current lease reader required")
        if (type(source_asset_ids) is not tuple or
                not 1<=len(source_asset_ids)<=12):
            raise Feature3PlanDenied("Canonical claimed source list required")
        ids=tuple(_uuid(item) for item in source_asset_ids)
        if ids!=tuple(sorted(set(ids))):
            raise Feature3PlanDenied("Claimed sources are duplicated or reordered")

        def live_lease():
            try:
                r=read_prepaid_reservation(shop,job,1,token)
            except Exception as exc:
                raise Feature3PlanDenied("Current one-shot lease unconfirmed") from exc
            if (not isinstance(r,dict) or set(r)!={
                    "reservation_id","shop_id","job_id","attempt",
                    "claim_token","reserved_usd"} or
                    r.get("shop_id")!=shop or r.get("job_id")!=job or
                    r.get("claim_token")!=token or
                    type(r.get("attempt")) is not int or r["attempt"]!=1):
                raise Feature3PlanDenied("Unconfirmed current reserved GPU lease")
            _uuid(r.get("reservation_id"))
            try:
                amount=Decimal(str(r["reserved_usd"]))
            except (InvalidOperation,KeyError,TypeError,ValueError) as exc:
                raise Feature3PlanDenied("Untrusted prepaid GPU amount") from exc
            if (type(r["reserved_usd"]) is bool or not amount.is_finite()
                    or amount<=0 or amount>Decimal("2.50")
                    or amount.as_tuple().exponent < -6):
                raise Feature3PlanDenied("Invalid bounded prepaid GPU amount")
            return {**r,"reserved_usd":str(amount)}
        before=live_lease()
        result=self._check(shop,job,claimed_token=token)
        if ids!=result["source_asset_ids"]:
            raise Feature3PlanDenied("Claimed GPU input sources changed")
        if live_lease()!=before:
            raise Feature3PlanDenied("Prepaid GPU lease changed during source verification")
        # This is proof of an existing claimed lease, not a new claim. Do NOT
        # interpret it as a provider authorization while feature is GPU-OFF.
        return {**result,"claim_observed":True,"current_lease_verified":True}


def make_claimed_gpu_off_rights_callback(*, plan_reader, service):
    """Existing worker current_rights signature -> real SQL/bytes recheck.

    The backend service supplies read_prepaid_reservation, which already
    checks future RUNNING lease, service-only reservation and prepaid cap.
    A fake/browser source verifier must never be passed to a live worker.
    """
    if (not callable(getattr(plan_reader,"check_claimed",None)) or
            not callable(getattr(service,"read_prepaid_reservation",None))):
        raise ValueError("Actual claimed source plan and prepaid SQL reader required")

    def current_rights(shop_id, job_id, token, source_asset_ids):
        result=plan_reader.check_claimed(
            shop_id,job_id,token,source_asset_ids,service.read_prepaid_reservation)
        return (result["current_lease_verified"] is True and
                result["claim_observed"] is True and
                result["provider_call_permitted"] is False and
                result["paid_retry_authorized"] is False)
    return current_rights
