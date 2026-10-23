"""Optional, fail-closed Alibaba Model Studio Wan 2.7 async adapter.

This adapter deliberately does NOT create cloud resources, store outputs, manage
subscriptions, or execute a request unless the owner enables its server-only gate.
Only internal workers may call submit/poll after durable DB reservation.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

TASK_ID = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
MODEL_BY_MODE = {
    "text": "wan2.7-t2v-2026-06-12",
    "image": "wan2.7-i2v-2026-04-25",
}
REGION_SUFFIX = {
    "singapore": ".ap-southeast-1.maas.aliyuncs.com",
    "beijing": ".cn-beijing.maas.aliyuncs.com",
}
CREATION_PATH = "/api/v1/services/aigc/video-generation/video-synthesis"


class PremiumVideoDisabled(RuntimeError):
    """No external request is allowed without a reviewed enablement gate."""


class PremiumVideoProviderError(RuntimeError):
    """Sanitized error; raw provider payloads/URLs must not be returned to users."""


@dataclass(frozen=True)
class WanRequest:
    mode: str
    prompt: str
    duration_seconds: int = 5
    resolution: str = "720P"
    ratio: str = "9:16"
    # Server-derived, short-lived SUPABASE SIGNED private storage URL only.
    # Never permit client-supplied URLs or anonymous/public bucket URLs.
    signed_first_frame: str | None = None
    shop_id: str | None = None

    def __post_init__(self):
        if self.mode not in MODEL_BY_MODE:
            raise ValueError("Unsupported premium video mode")
        if not isinstance(self.prompt, str) or not 1 <= len(self.prompt.strip()) <= 2000:
            raise ValueError("Video prompt must be 1-2000 characters")
        if type(self.duration_seconds) is not int or not 2 <= self.duration_seconds <= 15:
            raise ValueError("Wan 2.7 clips must be 2-15 seconds")
        if self.resolution not in ("720P", "1080P") or self.ratio not in (
            "9:16", "16:9", "1:1", "4:3", "3:4"
        ):
            raise ValueError("Unsupported Wan 2.7 resolution or aspect ratio")
        if self.mode == "image" and not (self.shop_id and self.signed_first_frame):
            raise ValueError("Image mode requires a server-authorized tenant image")
        if self.mode == "text" and self.signed_first_frame is not None:
            raise ValueError("Text mode cannot include an image URL")


def validate_private_frame(url: str, *, shop_id: str, supabase_origin: str):
    """Verify host/path only. Caller MUST check tenant DB ownership and rights."""
    if not isinstance(url, str) or not isinstance(shop_id, str):
        raise ValueError("Invalid private image reference")
    permitted = urlparse(supabase_origin)
    candidate = urlparse(url)
    if (permitted.scheme != "https" or
        not re.fullmatch(r"[a-z0-9]{20}\.supabase\.co", permitted.hostname or "") or
        candidate.scheme != "https" or candidate.netloc != permitted.netloc or
        candidate.username or candidate.password or candidate.fragment or
        not candidate.path.startswith(
            "/storage/v1/object/sign/retailgrowth-media/" + shop_id + "/"
        ) or not any(k == "token" and v for k, v in
                     __import__("urllib.parse", fromlist=["parse_qsl"]).parse_qsl(candidate.query)) or
        ".." in candidate.path or "%2f" in candidate.path.lower()):
        raise ValueError("Only signed tenant-private media links are supported")
    return url


def campaign_video_prompt(day: dict, *, approved_offer: str | None = None) -> str:
    """Compose a bounded storyboard prompt; never invent product claims/discounts."""
    if not isinstance(day, dict) or not isinstance(day.get("topic"), str):
        raise ValueError("A reviewed campaign day is required")
    topic = day["topic"].strip()
    if not 1 <= len(topic) <= 240:
        raise ValueError("Topic is missing or too long")
    reel = day.get("instagram", {}).get("reel", {})
    cta = reel.get("cta", "")
    if not isinstance(cta, str) or len(cta) > 140:
        raise ValueError("Invalid reviewed CTA")
    offer = ""
    if approved_offer:
        if not isinstance(approved_offer, str) or len(approved_offer) > 200:
            raise ValueError("Invalid approved offer")
        offer = " Approved promotional detail only: " + approved_offer.strip() + "."
    return (
        "Create a brand-safe vertical marketing video. Subject: " + topic +
        ". Use realistic visuals, clear framing and natural motion. " +
        "Do not invent prices, discounts, endorsements, people, logos or guarantees. " +
        "Call to action: " + cta.strip() + "." + offer
    )[:1500]


class AlibabaWanProvider:
    """Strict server-only async interface to approved Alibaba workspace domain.

    transport(method, url, headers, payload) -> parsed JSON (injectable offline).
    No automatic retry on POST: an uncertain acceptance can incur duplicate cost.
    """

    def __init__(self, *, workspace_origin="", api_key="", region="singapore",
                 enabled=False, approved_max_usd=0.0,
                 supabase_origin="", transport=None):
        self.origin = workspace_origin.rstrip("/")
        self.api_key = api_key
        self.region = region
        self.enabled = enabled
        self.approved_max_usd = approved_max_usd
        self.supabase_origin = supabase_origin
        self.transport = transport or self._request

    @classmethod
    def from_environment(cls):
        return cls(
            workspace_origin=os.getenv("RETAIL_WAN_WORKSPACE_ORIGIN", ""),
            api_key=os.getenv("RETAIL_WAN_API_KEY", ""),
            region=os.getenv("RETAIL_WAN_REGION", "singapore"),
            enabled=os.getenv("RETAIL_PREMIUM_VIDEO_ENABLED", "false").lower() == "true",
            approved_max_usd=float(os.getenv("RETAIL_WAN_APPROVED_PER_JOB_USD", "0")),
            supabase_origin=os.getenv("RETAIL_SUPABASE_URL", ""),
        )

    def _check(self):
        if not self.enabled:
            raise PremiumVideoDisabled("Premium video requires explicit approval")
        suffix = REGION_SUFFIX.get(self.region)
        host = urlparse(self.origin)
        if (not suffix or host.scheme != "https" or host.username or host.password or
            host.port or host.path not in ("", "/") or host.query or host.fragment or
            not host.hostname or not re.fullmatch(
                r"[a-zA-Z0-9-]{2,80}" + re.escape(suffix), host.hostname
            )):
            raise PremiumVideoDisabled("Unapproved Wan workspace endpoint")
        if not isinstance(self.api_key, str) or len(self.api_key) < 16:
            raise PremiumVideoDisabled("Wan API key missing")
        if self.approved_max_usd <= 0:
            raise PremiumVideoDisabled("Per-job provider cost cap not approved")

    @staticmethod
    def estimated_usd(spec: WanRequest) -> float:
        # Fixed STANDARD Singapore price only: other regions must reapprove.
        # Source: Alibaba Model Studio price list, 2026-10-22.
        return round(spec.duration_seconds * (0.10 if spec.resolution == "720P" else 0.15), 2)

    @staticmethod
    def _request(method, url, headers, payload):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                if response.status not in (200, 201, 202):
                    raise PremiumVideoProviderError("Unexpected Wan response")
                return json.loads(response.read(100_000))
        except (OSError, ValueError) as exc:
            raise PremiumVideoProviderError("Wan service request unsuccessful") from exc

    def submit(self, spec: WanRequest):
        self._check()
        if self.region != "singapore":
            raise PremiumVideoDisabled("Other region pricing not approved")
        if self.estimated_usd(spec) > self.approved_max_usd:
            raise PremiumVideoDisabled("Requested clip exceeds approved cost ceiling")
        body = {
            "model": MODEL_BY_MODE[spec.mode],
            "input": {"prompt": spec.prompt.strip()},
            "parameters": {
                "resolution": spec.resolution,
                "duration": spec.duration_seconds,
                "prompt_extend": False,
                "watermark": True,
            },
        }
        if spec.mode == "text":
            body["parameters"]["ratio"] = spec.ratio
        else:
            body["input"]["media"] = [{
                "type": "first_frame",
                "url": validate_private_frame(spec.signed_first_frame,
                    shop_id=spec.shop_id, supabase_origin=self.supabase_origin)
            }]
        result = self.transport("POST", self.origin + CREATION_PATH, {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }, body)
        task = result.get("output", {}) if isinstance(result, dict) else {}
        value = task.get("task_id")
        if not isinstance(value, str) or not TASK_ID.fullmatch(value):
            raise PremiumVideoProviderError("Wan did not confirm task ID")
        return {"provider": "alibaba-wan", "model": body["model"],
                "task_id": value, "status": "PENDING"}

    def _poll_result(self, task_id: str, *, include_private=False):
        """Worker-only result with private provider URL; NEVER send to browser.

        The importer still must enforce its independently approved exact host
        allowlist and verify MP4 bytes before registering tenant output.
        """
        self._check()
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            raise ValueError("Invalid provider task ID")
        result = self.transport("GET",
            self.origin + "/api/v1/tasks/" + task_id,
            {"Authorization": "Bearer " + self.api_key}, None)
        output = result.get("output", {}) if isinstance(result, dict) else {}
        if output.get("task_id") != task_id or output.get("task_status") not in (
            "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELED", "UNKNOWN"
        ):
            raise PremiumVideoProviderError("Invalid Wan task result")
        public = {"task_id": task_id, "status": output["task_status"]}
        if public["status"] == "SUCCEEDED" and include_private:
            link = output.get("video_url")
            if not isinstance(link, str) or len(link) > 4096:
                raise PremiumVideoProviderError("Wan output link unavailable")
            parsed = urlparse(link)
            if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username or parsed.password or parsed.fragment or
                not parsed.path or not parsed.hostname.endswith(".aliyuncs.com")):
                raise PremiumVideoProviderError("Wan output link untrusted")
            public["private_provider_url"] = link
        return public

    def poll_private(self, task_id: str):
        """Worker-only: returns URL for allowlisted private importer."""
        return self._poll_result(task_id, include_private=True)

    def poll(self, task_id: str):
        """Sanitized public status, regardless of any untrusted URL in reply."""
        result = self._poll_result(task_id, include_private=False)
        return {"task_id": result["task_id"], "status": result["status"]}
