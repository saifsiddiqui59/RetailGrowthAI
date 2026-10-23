"""Offline-reviewable Meta Instagram Reel and YouTube resumable upload flows.

NO real provider transport is created here. A separately approved worker must
inject an authenticated outbound client, licensed/verified tenant media reader,
and a durable private storage state machine. Never auto-retry a possibly
successful media_publish or final binary PUT without remote reconciliation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import re

from social_dispatch import Delivery, ProviderFailure, message_uuid
from social_providers import (
    ProviderRejected, instagram_reel_container_request,
    instagram_container_status_request, instagram_publish_request,
    youtube_resumable_init_request, youtube_upload_location,
)

_ID = re.compile(r"[0-9]{1,32}\Z")
_YOUTUBE_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")


@dataclass(frozen=True)
class BinaryUploadRequest:
    method: str
    url: str
    headers: dict = field(repr=False)
    data: bytes = field(repr=False)


def _id(value):
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ProviderFailure("INVALID_PROVIDER_ID", definitely_not_sent=True)
    return value


def _receipt_or_uncertain(status, body, *, key="id", provider="instagram"):
    if not isinstance(body, dict):
        raise ProviderFailure("AMBIGUOUS_PROVIDER_RECEIPT")
    value = body.get(key)
    if provider == "instagram":
        if not isinstance(value, str) or _ID.fullmatch(value) is None:
            raise ProviderFailure("AMBIGUOUS_PROVIDER_RECEIPT")
    else:
        if not isinstance(value, str) or _YOUTUBE_ID.fullmatch(value) is None:
            raise ProviderFailure("AMBIGUOUS_PROVIDER_RECEIPT")
    if status not in ((200, 201) if provider == "youtube" else (200,)):
        raise ProviderFailure("AMBIGUOUS_PROVIDER_RECEIPT")
    return value


class InstagramReelUpload:
    """Explicit container stages, durable create-post intent and no duplicate POSTS."""

    def __init__(self, *, transport, storage, graph_version, supabase_origin):
        self.transport = transport
        self.storage = storage
        self.graph_version = graph_version
        self.supabase_origin = supabase_origin

    def create_container(self, *, job_id, ig_account_id, token, video_url, caption):
        jid = message_uuid(job_id)
        account = _id(ig_account_id)
        try:
            request = instagram_reel_container_request(
                ig_user_id=account,token=token,video_url=video_url,
                caption=caption,supabase_origin=self.supabase_origin,
                graph_version=self.graph_version)
        except ProviderRejected:
            raise ProviderFailure("UNAUTHORIZED_MEDIA", definitely_not_sent=True) from None
        # Durable CAS state prevents two independent workers creating containers.
        if self.storage.begin_container(jid, account) is not True:
            raise ProviderFailure("CONTAINER_ALREADY_STARTED", definitely_not_sent=True)
        try:
            status, body, _ = self.transport(request)
            container = _receipt_or_uncertain(status, body)
            if self.storage.save_container(jid,account,container) is not True:
                raise ProviderFailure("CONTAINER_RECEIPT_NOT_DURABLE")
            return container
        except ProviderFailure:
            raise
        except Exception:
            raise ProviderFailure("CONTAINER_RESULT_UNCERTAIN") from None

    def status(self, *, job_id, ig_account_id, token):
        jid = message_uuid(job_id)
        account = _id(ig_account_id)
        container = _id(self.storage.get_container(jid, account))
        request = instagram_container_status_request(
            container_id=container, token=token,
            graph_version=self.graph_version)
        try:
            code, body, _ = self.transport(request)
            state = body.get("status_code") if isinstance(body, dict) else None
            if code != 200 or state not in ("FINISHED", "IN_PROGRESS", "ERROR", "EXPIRED", "PUBLISHED"):
                raise ValueError()
            if state in ("ERROR", "EXPIRED"):
                raise ProviderFailure("CONTAINER_PROCESSING_FAILED", definitely_not_sent=True)
            return state
        except ProviderFailure:
            raise
        except Exception:
            raise ProviderFailure("CONTAINER_STATUS_UNKNOWN") from None

    def publish_finished(self, *, job_id, ig_account_id, token):
        jid = message_uuid(job_id)
        account = _id(ig_account_id)
        container = _id(self.storage.get_container(jid,account))
        state = self.status(job_id=jid,ig_account_id=account,token=token)
        if state != "FINISHED":
            raise ProviderFailure("CONTAINER_NOT_FINISHED", definitely_not_sent=True)
        if self.storage.record_publish_intent(jid,container) is not True:
            # May already have been sent. Must reconcile by container/media ID.
            raise ProviderFailure("PUBLISH_INTENT_ALREADY_RECORDED")
        try:
            request = instagram_publish_request(
                ig_user_id=account,container_id=container,
                container_status="FINISHED",token=token,
                graph_version=self.graph_version)
            status,body,_ = self.transport(request)
            post_id = _receipt_or_uncertain(status,body)
            if self.storage.record_publish_receipt(jid,container,post_id) is not True:
                raise ProviderFailure("PUBLISH_RECEIPT_NOT_DURABLE")
            return Delivery(remote_id=post_id,status="PUBLISHED")
        except ProviderFailure:
            raise
        except Exception:
            raise ProviderFailure("INSTAGRAM_PUBLISH_UNCERTAIN") from None


class YouTubeResumableUpload:
    """Persist session before binary PUT; probe ambiguous PUT, never blind restart."""

    def __init__(self, *, transport, storage):
        self.transport = transport
        self.storage = storage

    def initialize(self, *, job_id, token, title, description, size_bytes):
        jid = message_uuid(job_id)
        try:
            req = youtube_resumable_init_request(
                token=token,title=title,description=description,
                size_bytes=size_bytes)
        except ProviderRejected:
            raise ProviderFailure("INVALID_MEDIA", definitely_not_sent=True) from None
        if self.storage.begin_upload(jid,size_bytes) is not True:
            raise ProviderFailure("UPLOAD_ALREADY_STARTED", definitely_not_sent=True)
        try:
            status,_,headers = self.transport(req)
            location = headers.get("location") if isinstance(headers,dict) else None
            if status not in (200,201) or not isinstance(location,str):
                raise ValueError()
            session = youtube_upload_location(location)
            if self.storage.save_session(jid,session) is not True:
                raise ProviderFailure("UPLOAD_SESSION_NOT_DURABLE")
            # Session is a bearer secret, only stored privately/encrypted.
            return "SESSION_STORED"
        except ProviderFailure:
            raise
        except Exception:
            raise ProviderFailure("UPLOAD_INITIALIZATION_UNCERTAIN") from None

    def upload_once(self, *, job_id, token, video_bytes):
        jid = message_uuid(job_id)
        if (not isinstance(video_bytes,bytes) or not video_bytes
                or len(video_bytes)>256*1024**3):
            raise ProviderFailure("INVALID_MEDIA", definitely_not_sent=True)
        session = youtube_upload_location(self.storage.get_session(jid))
        if self.storage.record_binary_intent(jid,len(video_bytes)) is not True:
            raise ProviderFailure("BINARY_SEND_MAY_HAVE_OCCURRED")
        req=BinaryUploadRequest(
            method="PUT",url=session,
            headers={"Authorization":"Bearer "+token,
                "Content-Length":str(len(video_bytes)),
                "Content-Type":"video/mp4"},
            data=video_bytes)
        try:
            status,body,_=self.transport(req)
            rid=_receipt_or_uncertain(status,body,provider="youtube")
            if self.storage.record_upload_receipt(jid,rid) is not True:
                raise ProviderFailure("UPLOAD_RECEIPT_NOT_DURABLE")
            return Delivery(remote_id=rid,status="PUBLISHED")
        except ProviderFailure:
            raise
        except Exception:
            raise ProviderFailure("YOUTUBE_UPLOAD_UNCERTAIN") from None

    def probe_interrupted(self, *, job_id, token, size_bytes):
        """Status-only request; never send the media again based on a guess."""
        jid=message_uuid(job_id)
        if type(size_bytes) is not int or size_bytes<=0:
            raise ProviderFailure("INVALID_MEDIA", definitely_not_sent=True)
        session=youtube_upload_location(self.storage.get_session(jid))
        req=BinaryUploadRequest("PUT",session,{
            "Authorization":"Bearer "+token,"Content-Length":"0",
            "Content-Range":f"bytes */{size_bytes}"},b"")
        try:
            code,body,headers=self.transport(req)
            if code in (200,201):
                rid=_receipt_or_uncertain(code,body,provider="youtube")
                if self.storage.record_upload_receipt(jid,rid) is not True:
                    raise ProviderFailure("UPLOAD_RECEIPT_NOT_DURABLE")
                return Delivery(remote_id=rid,status="PUBLISHED")
            if code==308 and isinstance(headers,dict):
                # Do not auto-send remaining bytes: operator-owned resume path
                # must verify stored session, offset and exact media digest.
                remote_range=headers.get("range")
                if remote_range is not None and not re.fullmatch(
                    r"bytes=0-[0-9]{1,18}",remote_range):
                    raise ValueError()
                return "INCOMPLETE_RECONCILE_REQUIRED"
            raise ValueError()
        except ProviderFailure:
            raise
        except Exception:
            raise ProviderFailure("UPLOAD_STATUS_UNKNOWN") from None
