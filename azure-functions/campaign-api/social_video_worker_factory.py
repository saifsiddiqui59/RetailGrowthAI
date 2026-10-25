"""No-provider-side-effect composition of the Part2 reviewed video pipeline.

This factory deliberately has NO Azure registration, no provider HTTP client
and no default social posting transport. All six explicit server-side release
switches, operator-owned encryption configuration and an injected reviewed
provider transport are required; importing the module never does I/O.
The caller must first obtain the *real* p2_claim_social_publish lease, mark
it EXTERNAL_INFLIGHT, then use the same job+claim for the entire workflow.
No browser or queue may provide a token, rights record, URL, or SHA.
Construction performs one private service-role claim lookup to derive shop scope,
but never downloads media, registers Azure triggers or sends provider requests.
"""
from __future__ import annotations

import base64
import re

from social_oauth import TokenVault
from social_private_render_reader import SocialPrivateRenderReader
from social_export_claim_authority import ScopedInstagramExportAuthority
from social_immutable_export import ImmutableSocialExportWriter
from social_video_claim_authority import ScopedVideoClaimAuthority
from social_video_upload_storage import ScopedVideoUploadStorage
from social_media_uploads import InstagramReelUpload, YouTubeResumableUpload
from social_video_send_orchestrator import ReviewedVideoSendOrchestrator

_REQUIRED_SWITCHES = (
    "RETAIL_PART2_SOCIAL_ENABLED",
    "RETAIL_PART2_PUBLISH_WORKER_ENABLED",
    "RETAIL_PART2_OUTBOUND_PUBLISH_ENABLED",
    "RETAIL_PART2_VIDEO_ENABLED",
    "RETAIL_PART2_VIDEO_WORKER_ENABLED",
    "RETAIL_PART2_VIDEO_PROVIDER_ENABLED",
)


class VideoWorkerDisabled(ValueError):
    pass


class _ProviderFactory:
    def __init__(self, *, origin, service_key, vault, claim_token,
                 provider_transport, storage_transport, graph_version):
        self.origin=origin
        self.key=service_key
        self.vault=vault
        self.lease=claim_token
        self.provider_transport=provider_transport
        self.storage_transport=storage_transport
        self.graph_version=graph_version

    def build(self,context):
        # The orchestrator supplies media_size from the independently hashed,
        # FFprobed PRIVATE P1 file, never from queue/user JSON.
        size=context.get("media_size")
        if type(size) is not int or not 0<size<=80*1024*1024:
            raise VideoWorkerDisabled("verified video bytes missing")
        state=ScopedVideoUploadStorage(
            origin=self.origin,service_key=self.key,
            shop_id=context["shop_id"],job_id=context["job_id"],
            claim_token=self.lease,provider=context["provider"],
            social_account_id=context["social_account_id"],
            provider_account_id=context["provider_account_id"],
            source_sha256=context["source_sha256"],media_size=size,
            vault=self.vault,enabled=True,transport=self.storage_transport)
        if context["provider"]=="instagram":
            return InstagramReelUpload(
                transport=self.provider_transport,storage=state,
                graph_version=self.graph_version,supabase_origin=self.origin)
        if context["provider"]=="youtube":
            return YouTubeResumableUpload(
                transport=self.provider_transport,storage=state)
        raise VideoWorkerDisabled("provider not authorized for video worker")


def build_guarded_video_sender(config, *, job_id, claim_token,
                              storage_transport=None,
                              provider_transport=None,
                              probe=None, clock=None):
    """Create guarded sender: only one private service-role claim lookup.

    Requires a reviewed, operator-owned private worker release. The explicit
    provider_transport dependency avoids accidentally enabling real network
    posts just by setting environment variables. Does not claim that rights,
    plan quotas or real account OAuth grants are configured.
    """
    if (not hasattr(config,"get") or any(
            config.get(flag)!="true" for flag in _REQUIRED_SWITCHES)):
        raise VideoWorkerDisabled("Part2 video release switches disabled")
    if provider_transport is None or not callable(provider_transport):
        raise VideoWorkerDisabled("reviewed provider transport missing")
    try:
        origin=config["RETAIL_SUPABASE_URL"]
        secret=config["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
        encoded=config["RETAIL_PART2_VAULT_KEY_B64"]
        version=int(config["RETAIL_PART2_VAULT_VERSION"])
        graph_version=config["RETAIL_META_GRAPH_VERSION"]
        if not isinstance(graph_version,str) or not re.fullmatch(
                r"v[0-9]{1,2}[.][0-9]{1,2}",graph_version):
            raise ValueError()
        vault=TokenVault(base64.b64decode(encoded,validate=True),version)
        claim=ScopedVideoClaimAuthority(
            origin=origin,service_key=secret,
            vault=vault,job_id=job_id,claim_token=claim_token,
            transport=storage_transport,clock=clock,enabled=True)
        reader=SocialPrivateRenderReader(origin,secret,transport=storage_transport)
    except (KeyError,TypeError,ValueError):
        raise VideoWorkerDisabled("invalid reviewed video worker configuration") from None
    # A private service-role read resolves the shop solely from DB authority.
    # It never posts to a social provider or mutates public account resources.
    try:
        context=claim.load(job_id,claim_token)
        sid=context["shop_id"]
        export_authority=ScopedInstagramExportAuthority(
            origin=origin,service_key=secret,shop_id=sid,
            job_id=job_id,claim_token=claim_token,transport=storage_transport)
        exporter=ImmutableSocialExportWriter(
            origin=origin,service_key=secret,claim_authority=export_authority,
            transport=storage_transport,enabled=True)
        factory=_ProviderFactory(
            origin=origin,service_key=secret,vault=vault,
            claim_token=claim_token,provider_transport=provider_transport,
            storage_transport=storage_transport,graph_version=graph_version)
        options={"claims":claim,"private_reader":reader,
                 "upload_factory":factory,"instagram_export":exporter,
                 "clock":clock,"enabled":True}
        if probe is not None:options["probe"]=probe
        return ReviewedVideoSendOrchestrator(**options)
    except Exception:
        raise VideoWorkerDisabled("verified video worker authority unavailable") from None
