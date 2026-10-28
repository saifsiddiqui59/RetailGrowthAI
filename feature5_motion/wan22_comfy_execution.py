"""Feature5 -> official pinned ComfyUI loopback API; default-disabled.

This is a local *submission boundary*, NOT a second job queue, reservation,
billing ledger, scheduler or private object-storage importer. Production must
run in a locked-down worker after the existing transactional Part3 claim,
reserved budget, Feature3 private input re-authorization and operator approvals.
No model, GPU, Azure or HTTP call occurs merely by importing this module.

ComfyUI pinned server.py endpoints: GET /object_info, POST /prompt,
GET /history/{prompt_id}. The server accepts caller-provided UUID prompt_id
but DOES NOT guarantee de-duplication; never retry an uncertain POST.
"""
from __future__ import annotations

import http.client
import hashlib
import json
import re
from dataclasses import dataclass

from .contracts import canonical_uuid
from .wan22_motion_adapter import WanShotPackage, WanCompatibilityError
from .infra.wan22_native_preflight import validate_native_graph_against_object_info

MAX_OBJECT_JSON=2*1024*1024
MAX_OTHER_JSON=512*1024
HISTORY=re.compile(r"^/history/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class UnknownComfyPaidAttempt(WanCompatibilityError):
    """POST may already have queued billable inference: reconcile, NEVER retry."""


class LoopbackComfyTransport:
    """No redirects, DNS, credentials, proxy, external URL, retries or websocket.

    One fixed loopback HTTP connection per call. The ComfyUI container must not
    expose its unauthenticated 8188 port outside its private network namespace.
    """
    def __init__(self, *, port=8188, timeout_seconds=5):
        if type(port) is not int or port!=8188 or type(timeout_seconds) not in (int,float) or not 1<=timeout_seconds<=10:
            raise WanCompatibilityError("Only bounded private local ComfyUI supported")
        self.timeout=timeout_seconds

    def __call__(self, method, path, payload=None):
        if not ((method=="GET" and path=="/object_info" and payload is None) or
                (method=="GET" and HISTORY.fullmatch(path) and payload is None) or
                (method=="POST" and path=="/prompt" and type(payload) is dict)):
            raise WanCompatibilityError("Forbidden ComfyUI transport endpoint")
        body=None
        if method=="POST":
            body=json.dumps(payload,separators=(",",":"),allow_nan=False).encode()
            if len(body)>MAX_OTHER_JSON:
                raise WanCompatibilityError("Oversized native Comfy submission")
        conn=http.client.HTTPConnection("127.0.0.1",8188,timeout=self.timeout)
        try:
            conn.request(method,path,body=body,
                         headers={"Content-Type":"application/json","Accept":"application/json"})
            reply=conn.getresponse()
            size=MAX_OBJECT_JSON if path=="/object_info" else MAX_OTHER_JSON
            raw=reply.read(size+1)
            if reply.status!=200 or len(raw)>size:
                raise WanCompatibilityError("Private ComfyUI response denied/oversized")
            data=json.loads(raw)
            if type(data) is not dict:
                raise WanCompatibilityError("Invalid private ComfyUI response")
            return data
        except (OSError,ValueError,UnicodeError,http.client.HTTPException) as exc:
            raise WanCompatibilityError("Private ComfyUI transport did not return valid JSON") from exc
        finally:
            conn.close()


@dataclass(frozen=True)
class SubmittedWanAttempt:
    prompt_id: str
    job_id: str
    shop_id: str
    status: str = "SUBMITTED_NOT_GENERATED_OR_APPROVED"
    gpu_success_proven: bool = False
    feature4_approved: bool = False


class WanPrivateComfyDispatcher:
    def __init__(self, transport=None, *, enabled=False):
        self.enabled=enabled
        self.transport=transport

    def submit_once(
        self, *, package, job_id, attempt_token,
        verify_existing_fenced_paid_claim, verify_current_private_first_frame,
        operator_image_legal_budget_approved=False,
        production_runtime_approved=False,
    ):
        """Return only queue receipt; must never issue a second paid attempt.

        verify_* callbacks MUST be wired to real server-side DB/media records
        by the coordinator. Test doubles only validate shape in unit tests.
        """
        if (self.enabled is not True or
            operator_image_legal_budget_approved is not True or
            production_runtime_approved is not True or
            not callable(self.transport) or
            not callable(verify_existing_fenced_paid_claim) or
            not callable(verify_current_private_first_frame)):
            raise WanCompatibilityError("Wan local paid submission disabled or not authorized")
        if (not isinstance(package,WanShotPackage) or
            package.provider!="wan22_ti2v_5b_comfy_v1" or
            package.task!="image_to_video" or
            package.status!="NOT_GENERATED_REVIEW_REQUIRED"):
            raise WanCompatibilityError("Only reviewed Feature2->Feature4 image-to-video packages")
        job=canonical_uuid(job_id)
        token=canonical_uuid(attempt_token)
        shop=canonical_uuid(package.lineage["shop_id"])
        source=canonical_uuid(package.lineage["source_asset_id"])
        # Preserve Feature2's actually signed positive/negative scene direction,
        # which may differ from the constructor's static default negative.
        # Trust neither an edited graph nor a recomputed hash by itself: the
        # independent existing transactional claim must fence BOTH digests.
        try:
            positive=package.graph["prompt"]["4"]["inputs"]["text"]
            negative=package.graph["prompt"]["5"]["inputs"]["text"]
            complete_sha=hashlib.sha256(json.dumps(
                {"positive":positive,"negative":negative},sort_keys=True,
                separators=(",",":"),allow_nan=False).encode()).hexdigest()
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            raise WanCompatibilityError("Malformed Feature2 model prompt bundle") from exc
        if (positive != package.prompt or
            complete_sha != package.prompt_sha256 or
            verify_existing_fenced_paid_claim(
                shop,job,token,package.lineage_sha256,package.prompt_sha256) is not True):
            raise WanCompatibilityError("Unreviewed creative digest or missing prepaid fenced attempt")
        # An authoritative F3 resolver must reauthorize rights and the actual
        # staged basename after the lease. A boolean cannot prove which local
        # file the supposedly approved model will consume.
        proof=verify_current_private_first_frame(
            shop,source,package.lineage["source_sha256"])
        if (type(proof) is not dict or set(proof) != {
            "shop_id","source_asset_id","source_sha256","staged_basename",
            "approved","private","commercial_rights","human_likeness_approved",
        } or proof["shop_id"]!=shop or proof["source_asset_id"]!=source or
            proof["source_sha256"]!=package.lineage["source_sha256"] or
            any(proof[key] is not True for key in (
                "approved","private","commercial_rights","human_likeness_approved"))):
            raise WanCompatibilityError("Missing current approved private staged Feature3 input")
        # Actual protected runtime /object_info, never browser supplied.
        object_info=self.transport("GET","/object_info",None)
        validate_native_graph_against_object_info(
            package.graph,object_info,expected_input_filename=proof["staged_basename"],
            expected_negative_prompt=negative)
        body={"prompt":package.graph["prompt"],"prompt_id":token}
        # The provider POST is allowed EXACTLY ONCE here. The Comfy server
        # accepts duplicate prompt IDs, so UUID alone does not deduplicate.
        # A missing/bad acknowledgement is UNKNOWN and must not be retried.
        try:
            ack=self.transport("POST","/prompt",body)
        except Exception as exc:
            raise UnknownComfyPaidAttempt("Uncertain Wan submission: reconcile existing claim, never retry") from exc
        if (type(ack) is not dict or
            ack.get("prompt_id")!=token or
            type(ack.get("node_errors")) is not dict or
            ack["node_errors"]):
            raise UnknownComfyPaidAttempt("ComfyUI submitted state unknown; reconcile before further actions")
        return SubmittedWanAttempt(token,job,shop)

    def read_history_once(self, receipt):
        """Read once; output remains untrusted until private byte import/probe."""
        if not isinstance(receipt,SubmittedWanAttempt) or not callable(self.transport):
            raise WanCompatibilityError("Unknown locally submitted Wan attempt")
        result=self.transport("GET","/history/"+receipt.prompt_id,None)
        row=result.get(receipt.prompt_id) if type(result) is dict else None
        if row is None:
            return {"state":"UNKNOWN_OR_PENDING","private_import_approved":False}
        if type(row) is not dict or type(row.get("status")) is not dict:
            raise WanCompatibilityError("Malformed native Comfy history")
        status=row["status"]
        if (status.get("completed") is True and
            status.get("status_str")=="success" and
            type(row.get("outputs")) is dict and
            "12" in row["outputs"]):
            return {"state":"COMFY_REPORTED_SUCCESS_PENDING_PRIVATE_MP4_PROBE",
                    "private_import_approved":False}
        return {"state":"UNKNOWN_OR_FAILED_REQUIRES_RECONCILIATION",
                "private_import_approved":False}
