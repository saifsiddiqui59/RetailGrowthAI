"""Explicit Part 2 video HTTP transport assembly; NO Azure registration.

An operator must individually approve the existing six server release
switches, this seventh network transport switch, the credentials, staged
migrations and separate DEV canary. Importing or constructing this module
never sends a provider request. Network writes require a reviewed active
private SENDING claim and the existing durable provider intent CAS.
"""
from __future__ import annotations

from social_media_transport import MediaNetworkTransport
from social_video_worker_factory import (
    VideoWorkerDisabled, _REQUIRED_SWITCHES, build_guarded_video_sender,
)

_NETWORK_SWITCH = "RETAIL_PART2_VIDEO_NETWORK_TRANSPORT_ENABLED"


def build_guarded_video_network_sender(
    config, *, job_id, claim_token, storage_transport=None,
    provider_opener=None, probe=None, clock=None, enabled=False,
):
    """Compose reviewed official-provider transport ONLY behind seven gates.

    Actual operation requires the separately reviewed Azure job/queue, auth,
    licensed original P1 media SHA, quotas and service-only claim. There is no
    default queue function, retry loop, public API or provider POST here.
    """
    if (enabled is not True or not hasattr(config, "get")
            or any(config.get(flag) != "true" for flag in
                   (*_REQUIRED_SWITCHES, _NETWORK_SWITCH))):
        raise VideoWorkerDisabled("Part2 video provider network remains disabled")
    if provider_opener is not None and not callable(provider_opener):
        raise VideoWorkerDisabled("invalid reviewed provider opener")
    # The transport has a host/path/method/header allowlist, HTTPS only,
    # no redirects, bounded bodies and no automatic 5xx/timeout replay.
    provider_transport = MediaNetworkTransport(
        enabled=True, opener=provider_opener)
    return build_guarded_video_sender(
        config, job_id=job_id, claim_token=claim_token,
        storage_transport=storage_transport,
        provider_transport=provider_transport,
        probe=probe, clock=clock,
    )
