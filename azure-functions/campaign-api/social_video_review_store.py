"""Private Part2 PostgREST bridge for *review only*, never a publish route.

Construction binds one exact authenticated operator/shop/job scope from the
server. This adapter implements the three independent authority protocols
needed by social_video_certification, using only explicit service-role RPCs.
Actual render SHA still must be recorded by a trusted Part1 finalize service,
and commercial rights must be checked by an independent reviewer before an
approval receipt is created. No direct public/client access.
"""
from __future__ import annotations
from datetime import datetime
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from tenant_store import canonical_uuid, StorageUnavailable


_ALLOW = frozenset({
    "p2_social_video_review_candidate",
    "p2_social_video_render_receipt",
    "p2_social_video_rights_for_review",
    "p2_record_social_media_review",
    "p2_bind_social_video_review",
})


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _when(value):
    if not isinstance(value, str):
        raise StorageUnavailable("invalid private video timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed
    except ValueError:
        raise StorageUnavailable("invalid private video timestamp") from None


class ScopedSocialVideoReviewStore:
    """All methods are bound to the SAME trusted shop, job and actor."""

    def __init__(self, origin, service_secret, *, shop_id, job_id, reviewer_id,
                 transport=None):
        try:
            parsed = urlsplit(origin)
            if (not isinstance(origin, str) or origin != origin.strip() or
                    any(ord(c) <= 32 or ord(c) == 127 for c in origin) or
                    parsed.scheme != "https" or not parsed.hostname or
                    parsed.port not in (None, 443) or parsed.username or
                    parsed.password or parsed.path not in ("", "/") or
                    parsed.query or parsed.fragment):
                raise ValueError()
            self.headers = backend_headers(service_secret)
            self.sid = canonical_uuid(shop_id)
            self.jid = canonical_uuid(job_id)
            self.actor = canonical_uuid(reviewer_id)
        except (TypeError, ValueError):
            raise ValueError("untrusted private media review configuration") from None
        self.origin = origin.rstrip("/")
        self.transport = transport or build_opener(_NoRedirect()).open

    def _scope(self, sid, jid=None, actor=None):
        if canonical_uuid(sid) != self.sid or (
            jid is not None and canonical_uuid(jid) != self.jid) or (
            actor is not None and canonical_uuid(actor) != self.actor):
            raise StorageUnavailable("untrusted video review scope")

    def _rpc(self, name, params):
        if name not in _ALLOW:
            raise ValueError("unapproved private video review RPC")
        url = self.origin + "/rest/v1/rpc/" + name
        req = Request(url, method="POST",
            headers={**self.headers, "Content-Type": "application/json",
                     "Accept": "application/json"},
            data=json.dumps(params, separators=(",", ":")).encode("utf-8"))
        try:
            with self.transport(req, timeout=10) as response:
                if (response.geturl() != url or response.status < 200 or
                        response.status >= 300):
                    raise StorageUnavailable("private video RPC rejected")
                content = response.read(65537)
                if len(content) > 65536:
                    raise StorageUnavailable("private video RPC oversized")
                return json.loads(content) if content else None
        except (HTTPError, URLError, OSError, UnicodeError,
                json.JSONDecodeError, TypeError):
            raise StorageUnavailable("private video RPC unavailable") from None

    def get_source(self, sid, jid, actor):
        self._scope(sid, jid, actor)
        row = self._rpc("p2_social_video_review_candidate",
            {"p_shop":self.sid,"p_job":self.jid,"p_actor":self.actor})
        if row is None:
            return None
        if not isinstance(row, dict) or "scheduled_at" not in row:
            raise StorageUnavailable("invalid service-side media candidate")
        row = dict(row)
        row["scheduled_at"] = _when(row["scheduled_at"])
        return row

    def get_render_receipt(self, sid, aid):
        self._scope(sid)
        aid = canonical_uuid(aid)
        row = self._rpc("p2_social_video_render_receipt",
            {"p_shop":self.sid,"p_job":self.jid,"p_actor":self.actor})
        if row is not None and (not isinstance(row, dict) or
                row.get("media_asset_id") != aid):
            raise StorageUnavailable("private receipt mismatched asset")
        return row

    def get_clearance(self, sid, aid, actor, revision):
        self._scope(sid, actor=actor)
        aid = canonical_uuid(aid)
        if type(revision) is not int or revision < 1:
            raise StorageUnavailable("invalid review revision")
        row = self._rpc("p2_social_video_rights_for_review",
            {"p_shop":self.sid,"p_job":self.jid,"p_actor":self.actor,
             "p_revision":revision})
        if row is None:
            return None
        if not isinstance(row, dict) or row.get("media_asset_id") != aid:
            raise StorageUnavailable("private rights mismatched asset")
        row = dict(row)
        row["rights_expires_at"] = _when(row.get("rights_expires_at"))
        return row

    def record_review(self, sid, aid, actor, source_sha, evidence_sha,
                      kind, profile, expires):
        self._scope(sid, actor=actor)
        return self._rpc("p2_record_social_media_review", {
            "p_shop":self.sid,"p_asset":canonical_uuid(aid),
            "p_actor":self.actor,"p_source_sha":source_sha,
            "p_evidence_sha":evidence_sha,"p_kind":kind,
            "p_probe":profile,"p_expires":expires.isoformat()
        }) is True

    def bind_review(self, sid, jid, actor, revision, source_sha):
        self._scope(sid, jid, actor)
        return self._rpc("p2_bind_social_video_review", {
            "p_shop":self.sid,"p_job":self.jid,"p_actor":self.actor,
            "p_revision":revision,"p_sha":source_sha
        }) is True
