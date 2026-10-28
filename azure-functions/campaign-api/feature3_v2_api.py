"""Feature #3 v2 signed-in HTTP boundary, disabled until reviewed migration.

No v1 poster behavior changes. Save only a private DRAFT design; no
render, publish, imported source approval, paid GPU or signed media URL.
"""
from __future__ import annotations

from tenant_store import canonical_uuid, StorageUnavailable
from security import AuthenticationError


class Feature3V2API:
    def __init__(self, tenant_store, design_store, *, model_review_enabled=False):
        self.tenant = tenant_store
        self.designs = design_store
        # Independent Gate B: source review SQL must be deployed and tested
        # before any hosted POST approval/revocation is allowed.
        self.model_review_enabled = model_review_enabled is True

    def _campaign_day(self, token, user_id, cid, did, *, write=False):
        campaign = self.tenant.campaign(token, user_id, cid)
        if campaign is None:
            return None
        sid = canonical_uuid(campaign["shop_id"])
        if not self.tenant.member(token, user_id, sid, write=write):
            return None
        if not any(d.get("id") == did and d.get("shop_id") == sid and
                   d.get("campaign_id", cid) == cid and
                   (not write or d.get("review_status") == "DRAFT")
                   for d in campaign.get("days", [])):
            return None
        if write and campaign.get("status") != "DRAFT":
            return None
        return sid

    def models(self, token, user_id, shop_id):
        sid = canonical_uuid(shop_id)
        if not self.tenant.member(token, user_id, sid):
            return 404, {"error": "NOT_FOUND"}
        entries = self.designs.list_models(token, sid, self.tenant)
        return 200, {"shop_id": sid, "models": entries,
                     "private_images_must_be_loaded_separately": True}


    def register_model_original(self, token, user_id, shop_id, body):
        """Register previously uploaded private model-library PNG, not rights."""
        if not self.model_review_enabled:
            return 503, {"error": "FEATURE3_MODEL_REVIEW_DISABLED"}
        sid = canonical_uuid(shop_id)
        if not self.tenant.member(token, user_id, sid, write=True):
            return 404, {"error": "NOT_FOUND"}
        keys = {"model_id", "image_sha256", "license_name",
                "license_url", "attribution"}
        if not isinstance(body, dict) or set(body) != keys:
            return 400, {"error": "INVALID_REQUEST"}
        result = self.designs.register_model_original(token, sid, body)
        if result is None:
            return 409, {"error": "MODEL_ORIGINAL_STALE_OR_DENIED"}
        return 201, result

    def import_model(self, token, user_id, shop_id, body):
        """Only signed active OWNER/EDITOR can REGISTER an unapproved model.

        This never creates media bytes, claims license/likeness proof or
        circumvents a second independent human-review and evidence audit.
        """
        if not self.model_review_enabled:
            return 503, {"error": "FEATURE3_MODEL_REVIEW_DISABLED"}
        sid = canonical_uuid(shop_id)
        if not self.tenant.member(token, user_id, sid, write=True):
            return 404, {"error": "NOT_FOUND"}
        required = {"model_id", "media_asset_id", "source_kind", "label",
                    "image_sha256", "license_id", "license_evidence_sha256",
                    "attribution", "approved_uses"}
        if not isinstance(body, dict) or set(body) != required:
            return 400, {"error": "INVALID_REQUEST"}
        result = self.designs.import_pending_model(token, sid, body)
        if result is None:
            return 409, {"error": "MODEL_IMPORT_STALE_OR_DENIED"}
        return 201, {"shop_id": sid, "model_id": result["model_id"],
                     "media_asset_id": result["media_asset_id"],
                     "status": "PENDING_REVIEW", "rights_revision": 1,
                     "rights_verified": False, "evidence_verified": False,
                     "gpu_authorized": False, "generation_executed": False}

    def review_model(self, token, user_id, shop_id, model_id, body, *, action):
        """Authenticated human decision transport: NO GPU or image generation.

        The HTTP router first verifies a real signed Supabase user JWT.
        TenantStore checks a current active OWNER/EDITOR; the SQL review
        RPC separately derives auth.uid() from the SAME user token and
        compares current status, evidence, rights revision and audit row.
        """
        if not self.model_review_enabled:
            return 503, {"error": "FEATURE3_MODEL_REVIEW_DISABLED"}
        sid, mid = canonical_uuid(shop_id), canonical_uuid(model_id)
        if not self.tenant.member(token, user_id, sid, write=True):
            return 404, {"error": "NOT_FOUND"}
        if not isinstance(body, dict):
            return 400, {"error": "INVALID_REQUEST"}
        if action == "review":
            required = {"decision", "expected_revision", "image_sha256",
                        "evidence_revision", "checks", "notes"}
            if set(body) != required:
                return 400, {"error": "INVALID_REQUEST"}
            result = self.designs.review_model(
                token, sid, mid, decision=body["decision"],
                expected_revision=body["expected_revision"],
                image_sha256=body["image_sha256"],
                evidence_revision=body["evidence_revision"],
                checks=body["checks"], notes=body["notes"],
            )
        elif action == "revoke":
            required = {"expected_revision", "image_sha256", "reason"}
            if set(body) != required:
                return 400, {"error": "INVALID_REQUEST"}
            result = self.designs.revoke_model(
                token, sid, mid, expected_revision=body["expected_revision"],
                image_sha256=body["image_sha256"], reason=body["reason"],
            )
        else:
            return 404, {"error": "NOT_FOUND"}
        if result is None:
            # Deliberately hide whether model is absent, foreign, reviewed,
            # revoked or concurrently changed; do NOT retry a mutation.
            return 409, {"error": "MODEL_REVIEW_STALE_OR_DENIED"}
        return 200, {
            "shop_id": sid, "model_id": mid,
            "status": result["status"],
            "rights_revision": result["rights_revision"],
            "review_event_id": result["review_event_id"],
            "audit_persisted": True,
            "gpu_enabled": False,
            "generation_executed": False,
        }

    def source_asset(self, token, user_id, shop_id, asset_id):
        """Read only a registered current-tenant private source metadata proof.

        It does NOT assert model/likeness approval, image SHA or that the
        Storage object can be read. A separate signed private binary read is
        required before the output can enter an image-conditioned model.
        """
        sid, aid = canonical_uuid(shop_id), canonical_uuid(asset_id)
        if not self.tenant.member(token, user_id, sid, write=True):
            return 404, {"error": "NOT_FOUND"}
        receipt = self.tenant.feature3_source_asset(token, sid, aid)
        if not isinstance(receipt, dict) or not (
            isinstance(receipt.get("mime_type"), str) and
            receipt.get("mime_type") in ("image/png", "image/jpeg", "image/webp") and
            receipt.get("license_name") in ("owned", "cc0", "commercial", "royalty_free")
        ):
            return 404, {"error": "NOT_FOUND"}
        return 200, {"shop_id": sid, "media_asset_id": aid,
                     "mime_type": receipt["mime_type"],
                     "license_name": receipt["license_name"],
                     "registered": True, "private_bytes_verified": False,
                     "model_reviewed": False, "gpu_eligible": False}

    def gpu_jobs(self, token, user_id, shop_id):
        """Only current-member, JWT/RLS-scoped metadata; no job claim."""
        sid = canonical_uuid(shop_id)
        if not self.tenant.member(token, user_id, sid):
            return 404, {"error": "NOT_FOUND"}
        return 200, {"shop_id": sid,
                     "jobs": self.tenant.feature3_gpu_jobs(token, sid),
                     "gpu_submission_enabled": False}

    def gpu_download(self, token, user_id, shop_id, job_id):
        """Authenticated download for successful, registered, private v2 GPU PNG.

        No direct client output IDs, Storage paths, approval or GPU activation.
        The real JWT must pass shop membership and both row-level reads.
        """
        sid, jid = canonical_uuid(shop_id), canonical_uuid(job_id)
        if not self.tenant.member(token, user_id, sid):
            return 404, {"error": "NOT_FOUND"}
        job = self.tenant.feature3_gpu_job(token, sid, jid)
        if job is None:
            return 404, {"error": "NOT_FOUND"}
        if job["status"] != "SUCCEEDED" or not job.get("output_asset_id"):
            return 409, {"error": "OUTPUT_NOT_READY"}
        asset = self.tenant.feature3_generated_asset(
            token, sid, jid, job["output_asset_id"])
        if asset is None:
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        return 200, {"job_id": jid, "media_asset_id": job["output_asset_id"],
                     "url": self.tenant.sign_download(
                         token, sid, asset["object_path"]),
                     "expires_in_seconds": 60, "approved_model": False}

    def day(self, token, user_id, campaign_id, day_id, method, body=None):
        cid, did = canonical_uuid(campaign_id), canonical_uuid(day_id)
        if method not in ("GET", "POST"):
            return 405, {"error": "METHOD_NOT_ALLOWED"}
        sid = self._campaign_day(token, user_id, cid, did, write=method == "POST")
        if sid is None:
            return 404, {"error": "NOT_FOUND"}
        if method == "GET":
            return 200, {"shop_id": sid, "campaign_id": cid, "day_id": did,
                         "designs": self.designs.list_day_designs(token, sid, cid, did)}
        if not isinstance(body, dict) or not {"design", "expected_revision"} <= set(body) or \
                set(body) - {"design", "expected_revision", "design_id", "variation_of"}:
            return 400, {"error": "INVALID_REQUEST"}
        design = body["design"]
        if not isinstance(design, dict) or set(design) != {
                "schema", "shop_id", "format", "template", "background", "layers"
        } or design.get("schema") != "retailgrowth.poster.v2" or design.get("shop_id") != sid:
            return 400, {"error": "INVALID_REQUEST"}
        expected = body["expected_revision"]
        if type(expected) is not int or not 0 <= expected <= 1000000:
            return 400, {"error": "INVALID_REQUEST"}
        draft_id = body.get("design_id")
        variation = body.get("variation_of")
        if draft_id is not None:
            canonical_uuid(draft_id)
        if variation is not None:
            canonical_uuid(variation)
        if (draft_id is not None and expected == 0) or \
                (draft_id is None and expected != 0) or \
                (variation is not None and draft_id is not None):
            return 400, {"error": "INVALID_REQUEST"}
        result = self.designs.save_design(
            token, sid, cid, did, design, design_id=draft_id,
            expected_revision=expected, variation_of=variation,
        )
        if result is None:
            return 409, {"error": "DESIGN_STALE_OR_ACCESS_DENIED"}
        return (201 if draft_id is None else 200), {
            **result, "shop_id": sid, "campaign_id": cid, "day_id": did,
            "status": "DRAFT", "rendered": False,
        }
