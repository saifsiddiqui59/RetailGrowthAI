# Original Part 3 Premium Wan draft #125 — exact 49-path source patch archive (2026-11-19)

Historical draft [#125](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/125), exact HEAD `3d985127e495d839e3e1f657080cbd8885561e6e`. Source tree/patches are from October 2026 **OLD Part 3 proposal**, explicitly marked DO NOT MERGE until protected gates. This file preserves EVERY GitHub changed-file diff hunk without importing runtime source, provider, routes, security workflows, SQL migration or frontend into main.

## Safety / unfinished work
- The old Part3 PR includes gated Wan provider/jobs, private imports, premium queue/outbox, cancelled job contracts, FFmpeg mixing, frontend/Functions interfaces and proposed SQL. These are NOT accepted hosted subscriptions, cost or licensing permissions; source recovery must be cherry-picked under current interfaces.
- Current Feature5 parent #323 and stacked #465 and Feature4 parent #322 remain live; original Part3 source task/contract requirements are to be reconciled in those issue/feature ledgers, not marked DONE by archival.
- `main` now includes newer JWT/RLS, entitlement, worker queues and integrations; merging this old 49-path draft directly would overwrite new guards/workflows and unrelated canonical docs. Keep original PR link and exact patches here; any future selective port MUST be against current main with security/cross-feature review, exact-head 4/4, fresh-main 4/4.
- All GPU and paid providers OFF; no Azure/Supabase/PROD/SQL mutations, no wine shop resources.

## Changed paths
- `.github/workflows/frontend-bootstrap.yml`
- `.github/workflows/part3-integration-ci.yml`
- `ai-agents/PART3_PROVIDER_HANDOFF.md`
- `ai-agents/src/ai_agents/premium_video.py`
- `ai-agents/tests/test_premium_video.py`
- `azure-functions/campaign-api/PART3_CANCELLATION_HANDOFF.md`
- `azure-functions/campaign-api/PART3_JOB_HANDOFF.md`
- `azure-functions/campaign-api/PART3_PRIVATE_IMPORT_HANDOFF.md`
- `azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql`
- `azure-functions/campaign-api/premium_cancel.py`
- `azure-functions/campaign-api/premium_http.py`
- `azure-functions/campaign-api/premium_outbox.py`
- `azure-functions/campaign-api/premium_poll_completion.py`
- `azure-functions/campaign-api/premium_private_import.py`
- `azure-functions/campaign-api/premium_queue.py`
- `azure-functions/campaign-api/premium_video_jobs.py`
- `azure-functions/campaign-api/premium_worker.py`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/PART3_IMPLEMENTATION.md`
- `docs/PART3_PROVIDER_RESEARCH.md`
- `docs/PROJECT_STATE.md`
- `docs/WORK_LOG.md`
- `docs/part3/APPROVED_CONTENT_GATE.md`
- `docs/part3/DURABLE_QUEUE_HANDOFF.md`
- `docs/part3/FFMPEG_ASSEMBLY_HANDOFF.md`
- `docs/part3/IMPLEMENTATION_AND_GATES.md`
- `docs/part3/MEDIA_FENCE_HARDENING.md`
- `docs/part3/POLL_COMPLETION_HANDOFF.md`
- `docs/part3/PREMIUM_HTTP_HANDOFF.md`
- `docs/part3/PROVIDERS_AND_COSTS.md`
- `docs/part3/QUALIFICATION.md`
- `docs/part3/REAL_COMPOSITION_SMOKE.md`
- `frontend/src/features/campaigns/CampaignDashboard.jsx`
- `frontend/src/features/premium-video/PART3_UI_HANDOFF.md`
- `frontend/src/features/premium-video/PremiumVideoPanel.jsx`
- `frontend/src/features/premium-video/premium-video-model.mjs`
- `tests/ai/test_premium_wan_provider.py`
- `tests/api/test_premium_cancel.py`
- `tests/api/test_premium_http.py`
- `tests/api/test_premium_video_jobs.py`
- `tests/media/test_premium_clip_compose.py`
- `tests/media/test_premium_compose_real.py`
- `tests/reliability/test_premium_outbox.py`
- `tests/reliability/test_premium_poll_completion.py`
- `tests/reliability/test_premium_private_import.py`
- `tests/reliability/test_premium_worker.py`
- `tests/security/premium_video_ui.test.mjs`
- `video-engine/premium_compose.py`

## All original PR #125 per-file GitHub patches

### .github/workflows/frontend-bootstrap.yml
~~~~diff
@@ -5,7 +5,8 @@ on:
   push:
     branches: [main, 'feat/**', 'chore/**']
   pull_request:
-    branches: [main]
+    # Part 3 internal PRs must pass the existing four security/render/build jobs.
+    branches: [main, 'feat/part3-integration']
   workflow_dispatch:
 
 permissions:
~~~~

### .github/workflows/part3-integration-ci.yml
~~~~diff
@@ -0,0 +1,62 @@
+name: RetailGrowthAI Part 3 Internal CI
+
+# Additive check isolated to the Part 3 branch. Never use deployment secrets.
+on:
+  pull_request:
+    branches: ['feat/part3-integration']
+  push:
+    branches: ['feat/part3-integration', 'feat/p3-*']
+
+permissions:
+  contents: read
+
+concurrency:
+  group: p3-ci-${{ github.ref }}
+  cancel-in-progress: true
+
+jobs:
+  provider-and-jobs:
+    name: Premium provider and job mocks
+    runs-on: ubuntu-24.04
+    timeout-minutes: 10
+    steps:
+      - uses: actions/checkout@v7
+        with:
+          persist-credentials: false
+      - uses: astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884
+        with:
+          version: '0.13.1'
+      - run: uv python install 3.13
+      - run: uv sync --project ai-agents
+      - name: Offline provider and durable job tests
+        shell: bash
+        run: |
+          set -euo pipefail
+          cases=()
+          [ ! -f ai-agents/tests/test_premium_video.py ] || cases+=(ai-agents/tests/test_premium_video.py)
+          [ ! -f tests/api/test_premium_video_jobs.py ] || cases+=(tests/api/test_premium_video_jobs.py)
+          if [ "${#cases[@]}" -eq 0 ]; then
+            echo "No Part 3 test files in this independently owned branch"
+          else
+            uv run --project ai-agents --with pytest --with "PyJWT[crypto]==2.10.1" -- python -m pytest -q "${cases[@]}"
+          fi
+  premium-frontend:
+    name: Premium control safety test
+    runs-on: ubuntu-24.04
+    timeout-minutes: 5
+    steps:
+      - uses: actions/checkout@v7
+        with:
+          persist-credentials: false
+      - uses: actions/setup-node@v7
+        with:
+          node-version: '22'
+          package-manager-cache: false
+      - name: Offline premium UI security assertions
+        shell: bash
+        run: |
+          if [ -f tests/security/premium_video_ui.test.mjs ]; then
+            node --test tests/security/premium_video_ui.test.mjs
+          else
+            echo "Premium UI test belongs to another task branch"
+          fi
~~~~

### ai-agents/PART3_PROVIDER_HANDOFF.md
~~~~diff
@@ -0,0 +1,5 @@
+# Part 3 provider handoff
+
+Wan 2.7 asynchronous text/image adapter, offline tests and campaign prompt builder are source-only. Enabled=false by default, no paid API calls, no token committed. Real approval requires Model Studio Singapore workspace, reviewed output rights, image transfer consent, billing cap, authenticated credit reservation, durable submission attempt and private importer. Wan 3.0 is separately supported by the vendor but not implemented in this narrow adapter. Public v1 campaign/render API remains unchanged.
+
+Full existing 4-job Part 1 CI and dedicated 2-job Part 3 CI must pass on this PR before integration merge.
~~~~

### ai-agents/src/ai_agents/premium_video.py
~~~~diff
@@ -0,0 +1,245 @@
+"""Optional, fail-closed Alibaba Model Studio Wan 2.7 async adapter.
+
+This adapter deliberately does NOT create cloud resources, store outputs, manage
+subscriptions, or execute a request unless the owner enables its server-only gate.
+Only internal workers may call submit/poll after durable DB reservation.
+"""
+from __future__ import annotations
+
+import json
+import os
+import re
+from dataclasses import dataclass
+from urllib.parse import urlparse
+from urllib.request import Request, urlopen
+
+TASK_ID = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
+MODEL_BY_MODE = {
+    "text": "wan2.7-t2v-2026-06-12",
+    "image": "wan2.7-i2v-2026-04-25",
+}
+REGION_SUFFIX = {
+    "singapore": ".ap-southeast-1.maas.aliyuncs.com",
+    "beijing": ".cn-beijing.maas.aliyuncs.com",
+}
+CREATION_PATH = "/api/v1/services/aigc/video-generation/video-synthesis"
+
+
+class PremiumVideoDisabled(RuntimeError):
+    """No external request is allowed without a reviewed enablement gate."""
+
+
+class PremiumVideoProviderError(RuntimeError):
+    """Sanitized error; raw provider payloads/URLs must not be returned to users."""
+
+
+@dataclass(frozen=True)
+class WanRequest:
+    mode: str
+    prompt: str
+    duration_seconds: int = 5
+    resolution: str = "720P"
+    ratio: str = "9:16"
+    # Server-derived, short-lived SUPABASE SIGNED private storage URL only.
+    # Never permit client-supplied URLs or anonymous/public bucket URLs.
+    signed_first_frame: str | None = None
+    shop_id: str | None = None
+
+    def __post_init__(self):
+        if self.mode not in MODEL_BY_MODE:
+            raise ValueError("Unsupported premium video mode")
+        if not isinstance(self.prompt, str) or not 1 <= len(self.prompt.strip()) <= 2000:
+            raise ValueError("Video prompt must be 1-2000 characters")
+        if type(self.duration_seconds) is not int or not 2 <= self.duration_seconds <= 15:
+            raise ValueError("Wan 2.7 clips must be 2-15 seconds")
+        if self.resolution not in ("720P", "1080P") or self.ratio not in (
+            "9:16", "16:9", "1:1", "4:3", "3:4"
+        ):
+            raise ValueError("Unsupported Wan 2.7 resolution or aspect ratio")
+        if self.mode == "image" and not (self.shop_id and self.signed_first_frame):
+            raise ValueError("Image mode requires a server-authorized tenant image")
+        if self.mode == "text" and self.signed_first_frame is not None:
+            raise ValueError("Text mode cannot include an image URL")
+
+
+def validate_private_frame(url: str, *, shop_id: str, supabase_origin: str):
+    """Verify host/path only. Caller MUST check tenant DB ownership and rights."""
+    if not isinstance(url, str) or not isinstance(shop_id, str):
+        raise ValueError("Invalid private image reference")
+    permitted = urlparse(supabase_origin)
+    candidate = urlparse(url)
+    if (permitted.scheme != "https" or
+        not re.fullmatch(r"[a-z0-9]{20}\.supabase\.co", permitted.hostname or "") or
+        candidate.scheme != "https" or candidate.netloc != permitted.netloc or
+        candidate.username or candidate.password or candidate.fragment or
+        not candidate.path.startswith(
+            "/storage/v1/object/sign/retailgrowth-media/" + shop_id + "/"
+        ) or not any(k == "token" and v for k, v in
+                     __import__("urllib.parse", fromlist=["parse_qsl"]).parse_qsl(candidate.query)) or
+        ".." in candidate.path or "%2f" in candidate.path.lower()):
+        raise ValueError("Only signed tenant-private media links are supported")
+    return url
+
+
+def campaign_video_prompt(day: dict, *, approved_offer: str | None = None) -> str:
+    """Compose a bounded storyboard prompt; never invent product claims/discounts."""
+    if not isinstance(day, dict) or not isinstance(day.get("topic"), str):
+        raise ValueError("A reviewed campaign day is required")
+    topic = day["topic"].strip()
+    if not 1 <= len(topic) <= 240:
+        raise ValueError("Topic is missing or too long")
+    reel = day.get("instagram", {}).get("reel", {})
+    cta = reel.get("cta", "")
+    if not isinstance(cta, str) or len(cta) > 140:
+        raise ValueError("Invalid reviewed CTA")
+    offer = ""
+    if approved_offer:
+        if not isinstance(approved_offer, str) or len(approved_offer) > 200:
+            raise ValueError("Invalid approved offer")
+        offer = " Approved promotional detail only: " + approved_offer.strip() + "."
+    return (
+        "Create a brand-safe vertical marketing video. Subject: " + topic +
+        ". Use realistic visuals, clear framing and natural motion. " +
+        "Do not invent prices, discounts, endorsements, people, logos or guarantees. " +
+        "Call to action: " + cta.strip() + "." + offer
+    )[:1500]
+
+
+class AlibabaWanProvider:
+    """Strict server-only async interface to approved Alibaba workspace domain.
+
+    transport(method, url, headers, payload) -> parsed JSON (injectable offline).
+    No automatic retry on POST: an uncertain acceptance can incur duplicate cost.
+    """
+
+    def __init__(self, *, workspace_origin="", api_key="", region="singapore",
+                 enabled=False, approved_max_usd=0.0,
+                 supabase_origin="", transport=None):
+        self.origin = workspace_origin.rstrip("/")
+        self.api_key = api_key
+        self.region = region
+        self.enabled = enabled
+        self.approved_max_usd = approved_max_usd
+        self.supabase_origin = supabase_origin
+        self.transport = transport or self._request
+
+    @classmethod
+    def from_environment(cls):
+        return cls(
+            workspace_origin=os.getenv("RETAIL_WAN_WORKSPACE_ORIGIN", ""),
+            api_key=os.getenv("RETAIL_WAN_API_KEY", ""),
+            region=os.getenv("RETAIL_WAN_REGION", "singapore"),
+            enabled=os.getenv("RETAIL_PREMIUM_VIDEO_ENABLED", "false").lower() == "true",
+            approved_max_usd=float(os.getenv("RETAIL_WAN_APPROVED_PER_JOB_USD", "0")),
+            supabase_origin=os.getenv("RETAIL_SUPABASE_URL", ""),
+        )
+
+    def _check(self):
+        if not self.enabled:
+            raise PremiumVideoDisabled("Premium video requires explicit approval")
+        suffix = REGION_SUFFIX.get(self.region)
+        host = urlparse(self.origin)
+        if (not suffix or host.scheme != "https" or host.username or host.password or
+            host.port or host.path not in ("", "/") or host.query or host.fragment or
+            not host.hostname or not re.fullmatch(
+                r"[a-zA-Z0-9-]{2,80}" + re.escape(suffix), host.hostname
+            )):
+            raise PremiumVideoDisabled("Unapproved Wan workspace endpoint")
+        if not isinstance(self.api_key, str) or len(self.api_key) < 16:
+            raise PremiumVideoDisabled("Wan API key missing")
+        if self.approved_max_usd <= 0:
+            raise PremiumVideoDisabled("Per-job provider cost cap not approved")
+
+    @staticmethod
+    def estimated_usd(spec: WanRequest) -> float:
+        # Fixed STANDARD Singapore price only: other regions must reapprove.
+        # Source: Alibaba Model Studio price list, 2026-10-22.
+        return round(spec.duration_seconds * (0.10 if spec.resolution == "720P" else 0.15), 2)
+
+    @staticmethod
+    def _request(method, url, headers, payload):
+        data = json.dumps(payload).encode() if payload is not None else None
+        request = Request(url, data=data, method=method, headers=headers)
+        try:
+            with urlopen(request, timeout=20) as response:
+                if response.status not in (200, 201, 202):
+                    raise PremiumVideoProviderError("Unexpected Wan response")
+                return json.loads(response.read(100_000))
+        except (OSError, ValueError) as exc:
+            raise PremiumVideoProviderError("Wan service request unsuccessful") from exc
+
+    def submit(self, spec: WanRequest):
+        self._check()
+        if self.region != "singapore":
+            raise PremiumVideoDisabled("Other region pricing not approved")
+        if self.estimated_usd(spec) > self.approved_max_usd:
+            raise PremiumVideoDisabled("Requested clip exceeds approved cost ceiling")
+        body = {
+            "model": MODEL_BY_MODE[spec.mode],
+            "input": {"prompt": spec.prompt.strip()},
+            "parameters": {
+                "resolution": spec.resolution,
+                "duration": spec.duration_seconds,
+                "prompt_extend": False,
+                "watermark": True,
+            },
+        }
+        if spec.mode == "text":
+            body["parameters"]["ratio"] = spec.ratio
+        else:
+            body["input"]["media"] = [{
+                "type": "first_frame",
+                "url": validate_private_frame(spec.signed_first_frame,
+                    shop_id=spec.shop_id, supabase_origin=self.supabase_origin)
+            }]
+        result = self.transport("POST", self.origin + CREATION_PATH, {
+            "Authorization": "Bearer " + self.api_key,
+            "Content-Type": "application/json",
+            "X-DashScope-Async": "enable",
+        }, body)
+        task = result.get("output", {}) if isinstance(result, dict) else {}
+        value = task.get("task_id")
+        if not isinstance(value, str) or not TASK_ID.fullmatch(value):
+            raise PremiumVideoProviderError("Wan did not confirm task ID")
+        return {"provider": "alibaba-wan", "model": body["model"],
+                "task_id": value, "status": "PENDING"}
+
+    def _poll_output(self, task_id: str):
+        """Request exactly one task status; never expose provider payload publicly."""
+        self._check()
+        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
+            raise ValueError("Invalid provider task ID")
+        result = self.transport("GET",
+            self.origin + "/api/v1/tasks/" + task_id,
+            {"Authorization": "Bearer " + self.api_key}, None)
+        output = result.get("output", {}) if isinstance(result, dict) else {}
+        if not isinstance(output, dict) or output.get("task_id") != task_id or (
+            output.get("task_status") not in
+            ("PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELED", "UNKNOWN")
+        ):
+            raise PremiumVideoProviderError("Invalid Wan task result")
+        return output
+
+    def poll(self, task_id: str):
+        """Safe browser/worker-facing status: provider URLs never leave the server."""
+        output = self._poll_output(task_id)
+        return {"task_id": task_id, "status": output["task_status"]}
+
+    def poll_private(self, task_id: str):
+        """INTERNAL WORKER ONLY. Return expiring URL solely for private importer.
+
+        Callers MUST check DB-fenced tenant claim, validate the provider URL,
+        download with redirects disabled, probe and upload to private storage.
+        Never include this result in HTTP responses, logs, queue messages or DB.
+        """
+        output = self._poll_output(task_id)
+        status = output["task_status"]
+        safe = {"task_id": task_id, "status": status}
+        if status == "SUCCEEDED":
+            url = output.get("video_url")
+            if not isinstance(url, str) or not 1 <= len(url) <= 2048:
+                raise PremiumVideoProviderError("Wan success missing private output")
+            # Host, signature expiry and media bytes are validated by the
+            # dedicated importer, not trusted from the provider status alone.
+            safe["video_url"] = url
+        return safe
~~~~

### ai-agents/tests/test_premium_video.py
~~~~diff
@@ -0,0 +1,180 @@
+"""Offline-only Wan 2.7 adapter tests. Never use real provider credentials."""
+import os
+from dataclasses import replace
+import pytest
+from ai_agents.premium_video import (
+    AlibabaWanProvider, PremiumVideoDisabled, PremiumVideoProviderError,
+    WanRequest, campaign_video_prompt, validate_private_frame,
+)
+
+SHOP = "123e4567-e89b-42d3-a456-426614174000"
+ORIGIN = "https://jeearzffnjbvghwjjjrf.supabase.co"
+FRAME = (ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" +
+         SHOP + "/uploads/first-frame.png?token=temporary-test-signature")
+WAN = "https://ws123.ap-southeast-1.maas.aliyuncs.com"
+
+
+def make_provider(recorder, *, enabled=False, limit=1):
+    def mock(method, url, headers, payload):
+        recorder.append((method, url, headers, payload))
+        if method == "POST":
+            return {"output": {"task_id": "abc-defghi-123456", "task_status": "PENDING"}}
+        return {"output": {"task_id": "abc-defghi-123456", "task_status": "SUCCEEDED",
+                           "video_url": "https://provider.example/private-token"}}
+    return AlibabaWanProvider(workspace_origin=WAN, api_key="fake-test-only-credential",
+                              region="singapore", enabled=enabled,
+                              approved_max_usd=limit, supabase_origin=ORIGIN,
+                              transport=mock)
+
+
+def test_disabled_is_default_and_never_calls_paid_api(monkeypatch):
+    for key in ("RETAIL_PREMIUM_VIDEO_ENABLED", "RETAIL_WAN_APPROVED_PER_JOB_USD"):
+        monkeypatch.delenv(key, raising=False)
+    provider = AlibabaWanProvider.from_environment()
+    with pytest.raises(PremiumVideoDisabled):
+        provider.submit(WanRequest("text", "New collection"))
+    assert not provider.enabled
+
+
+def test_enabled_still_requires_budget_credential_and_trusted_endpoint():
+    calls = []
+    for origin, key, limit in [(WAN, "", 1), (WAN, "fake-test-only-credential", 0),
+                               ("https://attacker.example", "fake-test-only-credential", 1),
+                               ("https://ws123.ap-southeast-1.maas.aliyuncs.com.evil.example",
+                                "fake-test-only-credential", 1)]:
+        provider = make_provider(calls, enabled=True, limit=limit)
+        provider.origin = origin
+        provider.api_key = key
+        with pytest.raises(PremiumVideoDisabled):
+            provider.submit(WanRequest("text", "Scenic promo"))
+    assert calls == []
+
+
+@pytest.mark.parametrize("duration", [0, 1, 16, True, 1.5])
+def test_invalid_duration_rejected_before_network(duration):
+    with pytest.raises(ValueError):
+        WanRequest("text", "Scenic promo", duration_seconds=duration)
+
+
+def test_text_to_video_payload_async_bounded_and_no_url_exposure():
+    calls = []
+    provider = make_provider(calls, enabled=True, limit=1)
+    result = provider.submit(WanRequest("text", "Realistic boutique campaign",
+                                        duration_seconds=10, resolution="720P"))
+    assert result == {"provider": "alibaba-wan", "model": "wan2.7-t2v-2026-06-12",
+                      "task_id": "abc-defghi-123456", "status": "PENDING"}
+    method, url, headers, body = calls[0]
+    assert method == "POST" and url.endswith("/video-synthesis")
+    assert headers["X-DashScope-Async"] == "enable"
+    assert body["parameters"]["duration"] == 10
+    assert body["parameters"]["ratio"] == "9:16"
+    assert body["parameters"]["watermark"] is True
+    assert body["model"] == "wan2.7-t2v-2026-06-12"
+    assert provider.estimated_usd(WanRequest("text", "clip", 10)) == 1.0
+    assert provider.estimated_usd(WanRequest("text", "clip", 10, "1080P")) == 1.5
+
+
+def test_cost_gate_blocks_before_provider_call():
+    calls = []
+    with pytest.raises(PremiumVideoDisabled, match="cost ceiling"):
+        make_provider(calls, enabled=True, limit=0.7).submit(
+            WanRequest("text", "Ad", duration_seconds=10))
+    assert calls == []
+
+
+def test_image_to_video_requires_shop_signed_path_and_omits_ratio():
+    calls = []
+    provider = make_provider(calls, enabled=True, limit=2)
+    request = WanRequest("image", "Animate still image", 5, "1080P",
+                         signed_first_frame=FRAME, shop_id=SHOP)
+    result = provider.submit(request)
+    assert result["model"] == "wan2.7-i2v-2026-04-25"
+    body = calls[0][-1]
+    assert body["input"]["media"] == [{"type": "first_frame", "url": FRAME}]
+    assert "ratio" not in body["parameters"]
+
+
+@pytest.mark.parametrize("url", [
+    "http://jeearzffnjbvghwjjjrf.supabase.co/storage/v1/object/sign/retailgrowth-media/x",
+    "https://attacker.example/storage/v1/object/sign/retailgrowth-media/x?token=x",
+    ORIGIN + "/storage/v1/object/public/retailgrowth-media/" + SHOP + "/a.png",
+    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/../../other.png?token=x",
+    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a.png",
+    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/other-shop/a.png?token=x",
+    ORIGIN + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a%2Fb.png?token=x",
+    ORIGIN.replace(".co", ".co.evil.example") + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a.png?token=x",
+])
+def test_private_frame_rejects_unsafe_paths(url):
+    with pytest.raises(ValueError):
+        validate_private_frame(url, shop_id=SHOP, supabase_origin=ORIGIN)
+
+
+def test_no_external_video_url_released_from_poll():
+    calls = []
+    provider = make_provider(calls, enabled=True)
+    assert provider.poll("abc-defghi-123456") == {
+        "task_id": "abc-defghi-123456", "status": "SUCCEEDED"
+    }
+    assert len(calls) == 1 and calls[0][0] == "GET"
+    with pytest.raises(ValueError):
+        provider.poll("../private-resource")
+
+
+def test_untrusted_provider_response_fail_closed():
+    calls = []
+    provider = make_provider(calls, enabled=True)
+    provider.transport = lambda *args: {"output": {"task_id": "bad id"}}
+    with pytest.raises(PremiumVideoProviderError):
+        provider.submit(WanRequest("text", "Promo"))
+
+
+def test_campaign_prompt_never_adds_unapproved_discount():
+    draft = {"topic": "Autumn clothing", "instagram": {"reel": {"cta": "Explore today"}}}
+    prompt = campaign_video_prompt(draft)
+    assert "Autumn clothing" in prompt
+    assert "Explore today" in prompt
+    assert "20% off" not in prompt
+    assert "20% off" in campaign_video_prompt(draft, approved_offer="20% off on coats")
+
+
+def test_invalid_input_never_reaches_transport():
+    calls = []
+    provider = make_provider(calls, enabled=True, limit=3)
+    with pytest.raises(ValueError):
+        provider.submit(WanRequest("image", "Illustrate", signed_first_frame=FRAME,
+                                   shop_id="another-shop"))
+    assert calls == []
+
+
+def test_private_poll_returns_vendor_link_only_inside_explicit_worker_method():
+    calls = []
+    provider = make_provider(calls, enabled=True)
+    expected_url = ("https://dashscope-a717.oss-accelerate.aliyuncs.com/"
+                    "clip.mp4?Expires=9999999999")
+
+    def responder(method, url, headers, payload):
+        calls.append((method, url))
+        return {"output": {"task_id": "abc-defghi-123456",
+                           "task_status": "SUCCEEDED",
+                           "video_url": expected_url,
+                           "orig_prompt": "should never leak"}}
+
+    provider.transport = responder
+    public = provider.poll("abc-defghi-123456")
+    private = provider.poll_private("abc-defghi-123456")
+    assert public == {"task_id": "abc-defghi-123456", "status": "SUCCEEDED"}
+    assert private == {**public, "video_url": expected_url}
+    assert "orig_prompt" not in private and "video_url" not in public
+    assert [x[0] for x in calls] == ["GET", "GET"]
+
+
+def test_private_poll_rejects_success_without_media_and_never_leaks_error_text():
+    calls = []
+    provider = make_provider(calls, enabled=True)
+    provider.transport = lambda *args: {
+        "output": {"task_id": "abc-defghi-123456", "task_status": "SUCCEEDED"}}
+    with pytest.raises(PremiumVideoProviderError, match="missing private output"):
+        provider.poll_private("abc-defghi-123456")
+    provider.enabled = False
+    with pytest.raises(PremiumVideoDisabled):
+        provider.poll_private("abc-defghi-123456")
~~~~

### azure-functions/campaign-api/PART3_CANCELLATION_HANDOFF.md
~~~~diff
@@ -0,0 +1,23 @@
+# Part 3 — premium-video cancellation boundary (source only)
+
+This workstream adds `PremiumCancelBoundary` and offline mocked race/authorization tests. It is intentionally **not registered** with Azure Functions and no SQL migration is applied. Every existing FFmpeg/campaign flow is unaffected; premium mode remains disabled by default and no Wan API request, customer charge, queue, or infrastructure deployment is performed.
+
+## Safe cancellation contract
+
+- **Only QUEUED before submission** may be canceled. Any `SUBMITTING`, `PENDING`, `RUNNING`, `IMPORTING`, `SUCCEEDED`, `FAILED`, `UNKNOWN`, or observed provider task/lease is **not** safely refundable without provider reconciliation.
+- Authorize with the existing user JWT/RLS and active shop OWNER/EDITOR permission. Return 404 for foreign/removed-member jobs.
+- Future `store.cancel_unsubmitted_atomic(job_id, shop_id, user_id)` must be ONE audited, service-only PostgreSQL transaction. Row-lock both the premium job and existing subscription ledger reservation; verify current membership/shop, `status='QUEUED'`, `provider_task_id IS NULL`, `attempt_token IS NULL`, and absence of a committed provider submission; transition to CANCELED and release **only that reservation** in the same transaction. The operation loses to the worker's `QUEUED -> SUBMITTING` CAS if submission has begun.
+- Return a typed exact receipt confirming same job/shop, canceled status, ledger credit released and provider submission never started. Missing/mismatched receipt fails closed (503). None/race returns 409 for reconciliation; no credit or cancellation success is assumed.
+- Repeated cancellation returns 200 only when a persisted cancellation receipt proves release. Otherwise 409. No provider cancellation or assumed refund is invoked.
+- No new billing ledger, no client price/URL/provider-ID input, no PII/provider URLs in safe responses.
+- Existing Part1 trial/premium allowances remain ZERO pending owner provider, region, terms and spending approvals.
+
+## Activation dependencies
+
+1. Reviewed NEW migration/RPC with adversarial PostgreSQL transaction tests for cancel-vs-submit races and idempotency; must integrate with source-only proposed premium schema and **existing** `shop_usage_reservations` without replaying previously applied migrations.
+2. Add a narrow authenticated `POST /api/premium-video-jobs/{job_id}/cancel` route only after safe live transactional RPC, protected deployment and human approval. Shared API contracts/Part1 UI changes require Coordinator review.
+3. Verify hosted DEV tenant denials, provider task unknown states, canceled reservation counters, and no double refunds. No production activation or paid generation without explicit owner authorization.
+
+## Current test scope
+
+`tests/api/test_premium_cancel.py` is discovered by the existing Python CI job; tests cover disabled path, member denials, unsubmitted vs uncertain statuses, foreign job, incomplete credits, losing CAS race and idempotent cancellation response. Mock behavior is **not evidence of a deployed atomic database RPC**.
~~~~

### azure-functions/campaign-api/PART3_JOB_HANDOFF.md
~~~~diff
@@ -0,0 +1,5 @@
+# Part 3 jobs handoff
+
+Source-only, NOT activated or deployed. New 20261023180000 migration uses original shop_subscriptions and shop_usage_reservations (no second billing), with zero premium seconds/USD defaults. It has not been applied to hosted RetailGrowthAI DEV. Job coordinator and lease-fenced worker are NOT registered with live function_app or existing Azure queue; atomic submission outbox and verified private provider-media importer are incomplete. Never enable the feature switch or run billable jobs until those operations and concurrency tests are complete. Existing FFmpeg path is untouched.
+
+Full existing 4-job Part 1 CI and dedicated 2-job Part 3 CI must pass on this PR before integration merge.
~~~~

### azure-functions/campaign-api/PART3_PRIVATE_IMPORT_HANDOFF.md
~~~~diff
@@ -0,0 +1,3 @@
+# Part 3 private output import handoff
+
+Source-only worker module; no Azure function route/trigger registered. Uses strict reviewed Alibaba CDN hostname, HTTPS, no redirects, 80 MB streaming bound, MP4 ftyp signature, ffprobe H.264/duration/size tests, tenant-private existing Storage upload and database lease-fenced finalization callback. Customer never receives provider URL. No automatic deletion of partially uploaded output; add exact tenant orphan reconciliation before enabling. No paid API, no hosted storage, no privileged keys.
~~~~

### azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql
~~~~diff
@@ -0,0 +1,158 @@
+-- STAGED FOR COORDINATOR SCHEMA REVIEW. NOT AN APPLICABLE SUPABASE MIGRATION.
+-- Move to supabase/migrations only after matching DB history and updating
+-- the existing guarded release plan; DO NOT apply it to hosted DEV directly.
+-- Part 3 source-only additive migration. NOT authorized/applied to hosted DEV.
+-- Extends the EXISTING Part 1 subscription meter. No payment provider and no
+-- second billing system. All premium allowances default to ZERO (fail closed).
+begin;
+
+alter table public.shop_subscriptions
+  add column premium_video_seconds integer not null default 0
+    check (premium_video_seconds between 0 and 3600),
+  add column premium_video_budget_usd numeric(12,4) not null default 0
+    check (premium_video_budget_usd between 0 and 10000);
+
+-- Existing rows stay operation=campaign/render with units=1.
+alter table public.shop_usage_reservations
+  add column units integer not null default 1 check (units between 1 and 3600);
+alter table public.shop_usage_reservations
+  drop constraint shop_usage_reservations_operation_check;
+alter table public.shop_usage_reservations
+  add constraint shop_usage_reservations_operation_check
+  check (operation in ('campaign','render','premium_video'));
+
+create table public.premium_video_jobs (
+  id uuid primary key,
+  shop_id uuid not null references public.shops(id) on delete cascade,
+  campaign_id uuid not null references public.campaigns(id) on delete cascade,
+  day_id uuid not null references public.campaign_days(id) on delete cascade,
+  requested_by uuid not null references auth.users(id),
+  input_asset_id uuid references public.media_assets(id),
+  mode text not null check (mode in ('text','image')),
+  model_id text not null check (model_id in (
+    'wan2.7-t2v-2026-06-12', 'wan2.7-i2v-2026-04-25'
+  )),
+  resolution text not null check (resolution in ('720P','1080P')),
+  seconds integer not null check (seconds between 2 and 15),
+  -- Based on vendor Singapore list price, updated by reviewed migration only.
+  reserved_usd numeric(12,4) not null default 0,
+  idempotency_key text not null check (idempotency_key ~ '^[a-f0-9]{64}$'),
+  status text not null default 'QUEUED'
+    check (status in ('QUEUED','SUBMITTING','PENDING','RUNNING',
+                     'IMPORTING','SUCCEEDED','FAILED','CANCELED','UNKNOWN')),
+  provider_task_id text,
+  output_asset_id uuid references public.media_assets(id),
+  error_code text,
+  attempt_token uuid,
+  lease_until timestamptz,
+  created_at timestamptz not null default now(),
+  updated_at timestamptz not null default now(),
+  constraint premium_video_image_input check (
+    (mode='image' and input_asset_id is not null
+      and model_id='wan2.7-i2v-2026-04-25')
+    or (mode='text' and input_asset_id is null
+      and model_id='wan2.7-t2v-2026-06-12')
+  ),
+  constraint premium_video_shop_idempotency unique (shop_id,idempotency_key)
+);
+create index premium_video_jobs_shop_created on public.premium_video_jobs
+  (shop_id,created_at desc);
+create index premium_video_jobs_due on public.premium_video_jobs
+  (status,lease_until) where status in ('QUEUED','PENDING','RUNNING','UNKNOWN');
+
+alter table public.premium_video_jobs enable row level security;
+revoke all on public.premium_video_jobs from public,anon,authenticated;
+grant select on public.premium_video_jobs to authenticated;
+grant all on public.premium_video_jobs to service_role;
+create policy premium_video_job_tenant_read on public.premium_video_jobs
+  for select to authenticated
+  using (retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
+
+-- Atomic premium reservation, same row lock and existing ledger as Part 1.
+-- Worker inserts ONLY after verified user JWT, tenant rights and asset provenance.
+-- Enforced again here; no TRIAL or other existing shop can use the paid provider.
+create function retail_private.reserve_premium_video()
+returns trigger language plpgsql security definer set search_path=''
+as $$
+declare
+  sub public.shop_subscriptions%rowtype;
+  used_seconds bigint;
+  used_usd numeric(12,4);
+  amount numeric(12,4);
+begin
+  if (select auth.role()) is distinct from 'service_role' then
+    raise exception 'Backend-only premium reservation' using errcode='42501';
+  end if;
+  if new.status <> 'QUEUED' or new.provider_task_id is not null
+    or new.output_asset_id is not null or new.attempt_token is not null then
+    raise exception 'Invalid initial premium job' using errcode='42501';
+  end if;
+  if not exists (
+    select 1 from public.shop_memberships m
+    where m.shop_id=new.shop_id and m.user_id=new.requested_by
+      and m.active and m.role in ('OWNER','EDITOR')
+  ) then
+    raise exception 'Active tenant write role required' using errcode='42501';
+  end if;
+  if not exists (
+    select 1 from public.campaign_days d
+      join public.campaigns c on c.id=d.campaign_id
+    where d.id=new.day_id and d.campaign_id=new.campaign_id
+      and d.shop_id=new.shop_id and c.shop_id=new.shop_id
+      and c.status='DRAFT' and d.review_status = 'APPROVED'
+  ) then
+    raise exception 'Invalid reviewed campaign day' using errcode='42501';
+  end if;
+  if new.mode='image' and not exists (
+    select 1 from public.media_assets a
+    where a.id=new.input_asset_id and a.shop_id=new.shop_id
+      and a.mime_type in ('image/png','image/jpeg','image/webp')
+  ) then
+    raise exception 'Invalid tenant image' using errcode='42501';
+  end if;
+  select * into sub from public.shop_subscriptions s
+    where s.shop_id=new.shop_id for update;
+  if not found or sub.status<>'ACTIVE' or sub.plan_code='TRIAL'
+     or now() < sub.valid_from or now() >= sub.valid_until
+     or now() < sub.period_start or now() >= sub.period_end
+     or sub.premium_video_seconds=0 or sub.premium_video_budget_usd=0 then
+    raise exception 'SUBSCRIPTION_REQUIRED' using errcode='RG001';
+  end if;
+  if exists (
+    select 1 from public.premium_video_jobs j
+    where j.shop_id=new.shop_id and j.idempotency_key=new.idempotency_key
+  ) then
+    raise exception 'Already reserved premium request' using errcode='23505';
+  end if;
+  amount := (new.seconds * (case when new.resolution='720P'
+                                  then 0.1000 else 0.1500 end));
+  select coalesce(sum(u.units),0) into used_seconds
+    from public.shop_usage_reservations u
+    where u.shop_id=new.shop_id and u.period_start=sub.period_start
+      and u.operation='premium_video';
+  select coalesce(sum(j.reserved_usd),0) into used_usd
+    from public.premium_video_jobs j
+    join public.shop_usage_reservations u on u.shop_id=j.shop_id
+      and u.job_id=j.id and u.operation='premium_video'
+      and u.period_start=sub.period_start
+    where j.shop_id=new.shop_id;
+  if used_seconds + new.seconds > sub.premium_video_seconds
+     or used_usd + amount > sub.premium_video_budget_usd then
+    raise exception 'QUOTA_EXCEEDED' using errcode='RG002';
+  end if;
+  new.reserved_usd:=amount;
+  insert into public.shop_usage_reservations
+    (shop_id,operation,job_id,period_start,units)
+  values (new.shop_id,'premium_video',new.id,sub.period_start,new.seconds);
+  return new;
+end
+$$;
+revoke all on function retail_private.reserve_premium_video()
+  from public,anon,authenticated;
+create trigger premium_job_reserve before insert on public.premium_video_jobs
+  for each row execute function retail_private.reserve_premium_video();
+
+-- A user (including a shop OWNER) can inspect their own job but cannot
+-- edit allowance, forge reservations, change providers, or inject task URLs.
+-- Existing premium ledger is still OWNER-only, unchanged by this migration.
+commit;
~~~~

### azure-functions/campaign-api/premium_cancel.py
~~~~diff
@@ -0,0 +1,71 @@
+"""Part 3: source-only, fail-closed cancellation of *unsubmitted* premium jobs.
+
+No HTTP route, migration or worker is activated by importing this module.
+Only a future reviewed service-role DB transaction may actually cancel a job.
+"""
+from __future__ import annotations
+
+from tenant_store import canonical_uuid, StorageUnavailable
+
+
+class PremiumCancelBoundary:
+    """JWT-scoped request guard before ONE authoritative DB cancellation RPC.
+
+    Required store.cancel_unsubmitted_atomic(job_id, shop_id, user_id):
+      - A SINGLE database transaction serializes against QUEUED -> SUBMITTING.
+      - Rechecks active OWNER/EDITOR membership, exact shop and job, and a
+        reservation in the EXISTING shop_usage_reservations ledger.
+      - Requires status QUEUED, provider_task_id NULL, attempt_token NULL.
+      - Sets CANCELED, releases the premium reservation and records a durable
+        audit/credit release receipt atomically.
+      - Returns an exact receipt, or None if any precondition has changed.
+      - NEVER touches SUBMITTING/PENDING/RUNNING/UNKNOWN/IMPORTING jobs.
+    Until that RPC and its concurrency tests exist this boundary must remain OFF.
+    """
+
+    def __init__(self, users, store, *, enabled=False):
+        self.users, self.store, self.enabled = users, store, enabled
+
+    def cancel(self, token, user_id, job_id):
+        if not self.enabled:
+            return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
+        try:
+            uid, jid = canonical_uuid(user_id), canonical_uuid(job_id)
+        except (TypeError, ValueError):
+            return 400, {"error": "INVALID_REQUEST"}
+        try:
+            job = self.store.get_authenticated(token, jid)
+            if not isinstance(job, dict) or job.get("id") != jid:
+                return 404, {"error": "NOT_FOUND"}
+            sid = canonical_uuid(job["shop_id"])
+            if not self.users.member(token, uid, sid, write=True):
+                return 404, {"error": "NOT_FOUND"}
+            if job.get("status") == "CANCELED":
+                # Require persisted proof; CANCELED alone is not proof of a
+                # provider-free cancellation or refundable credit release.
+                if (job.get("credit_released") is True and
+                    job.get("provider_submission_not_started") is True and
+                    job.get("provider_task_id") is None):
+                    return 200, {"job_id": jid, "status": "CANCELED"}
+                return 409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"}
+            if (job.get("status") != "QUEUED" or
+                job.get("provider_task_id") is not None or
+                job.get("attempt_token") is not None):
+                return 409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"}
+
+            receipt = self.store.cancel_unsubmitted_atomic(jid, sid, uid)
+            if receipt is None:
+                # Race with another worker: no refund or state assertion.
+                return 409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"}
+            if (not isinstance(receipt, dict) or
+                receipt.get("id") != jid or
+                receipt.get("shop_id") != sid or
+                receipt.get("status") != "CANCELED" or
+                receipt.get("credit_released") is not True or
+                receipt.get("provider_submission_not_started") is not True or
+                receipt.get("provider_task_id") is not None):
+                # Fail closed if DB RPC cannot prove a transactional refund.
+                return 503, {"error": "CANCELLATION_RECEIPT_UNVERIFIED"}
+            return 200, {"job_id": jid, "status": "CANCELED"}
+        except (StorageUnavailable, ValueError, TypeError, KeyError):
+            return 503, {"error": "SERVICE_UNAVAILABLE"}
~~~~

### azure-functions/campaign-api/premium_http.py
~~~~diff
@@ -0,0 +1,97 @@
+"""Fail-closed, standalone Part 3 premium HTTP adapter (NOT registered in Azure).
+
+Reusable source contract for additive authenticated premium create/status/download
+routes. Does not enable billing, create cloud queues, apply migrations or call Wan.
+The production API may mount this ONLY after vetted SQL/worker/entitlement gates.
+"""
+from __future__ import annotations
+
+import re
+
+from security import AuthenticationError
+from tenant_store import (
+    StorageUnavailable, SubscriptionDenied, canonical_uuid,
+)
+
+CAMPAIGN_CREATE = re.compile(r"^/campaigns/([^/]+)/premium-videos$")
+PREMIUM_JOB = re.compile(r"^/premium-video-jobs/([^/]+)(/download)?$")
+PRIVATE_FILE = re.compile(
+    r"^([0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\.mp4$"
+)
+
+
+class PremiumHTTPBoundary:
+    """Dedicated private controller; no change to Part1 HTTPAPI public v1 API."""
+
+    def __init__(self, verify_token, users, premium_store, coordinator,
+                 *, enabled=False):
+        self.verify_token = verify_token
+        self.users = users
+        self.store = premium_store
+        self.coordinator = coordinator
+        self.enabled = enabled
+
+    def handle(self, method, path, authorization, body=None):
+        try:
+            if (not isinstance(authorization, str) or
+                not authorization.startswith("Bearer ") or
+                not authorization[7:].strip()):
+                raise AuthenticationError("Bearer token required")
+            token = authorization[7:].strip()
+            user_id = canonical_uuid(self.verify_token(token))
+            if not self.enabled or not self.coordinator:
+                return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
+            if not isinstance(path, str):
+                return 404, {"error": "NOT_FOUND"}
+
+            match = CAMPAIGN_CREATE.fullmatch(path)
+            if match is not None and method == "POST":
+                campaign_id = canonical_uuid(match.group(1))
+                return self.coordinator.create(token, user_id, campaign_id, body)
+
+            match = PREMIUM_JOB.fullmatch(path)
+            if match is not None:
+                jid = canonical_uuid(match.group(1))
+                if match.group(2) is None and method == "GET":
+                    return self.coordinator.status(token, user_id, jid)
+                if match.group(2) == "/download" and method == "GET":
+                    return self._download(token, user_id, jid)
+            return 404, {"error": "NOT_FOUND"}
+        except AuthenticationError:
+            return 401, {"error": "UNAUTHORIZED"}
+        except SubscriptionDenied as exc:
+            if exc.code == "RG002":
+                return 429, {"error": "QUOTA_EXCEEDED"}
+            return 402, {"error": "SUBSCRIPTION_REQUIRED"}
+        except (ValueError, TypeError, AttributeError):
+            return 400, {"error": "INVALID_REQUEST"}
+        except (StorageUnavailable, KeyError):
+            return 503, {"error": "SERVICE_UNAVAILABLE"}
+
+    def _download(self, token, user_id, job_id):
+        """Download is authorized from current DB and user JWT, never a URL input."""
+        job = self.store.get_authenticated(token, job_id)
+        if not isinstance(job, dict) or job.get("id") != job_id:
+            return 404, {"error": "NOT_FOUND"}
+        sid = canonical_uuid(job["shop_id"])
+        if not self.users.member(token, user_id, sid):
+            # 404 avoids disclosing tenant/job existence.
+            return 404, {"error": "NOT_FOUND"}
+        if job.get("status") != "SUCCEEDED" or not job.get("output_asset_id"):
+            return 409, {"error": "OUTPUT_NOT_READY"}
+        aid = canonical_uuid(job["output_asset_id"])
+        asset = self.users.asset(token, sid, aid)
+        if (not isinstance(asset, dict) or asset.get("id") != aid or
+            asset.get("shop_id") != sid or
+            asset.get("storage_bucket") != "retailgrowth-media" or
+            asset.get("mime_type") != "video/mp4"):
+            return 404, {"error": "OUTPUT_NOT_FOUND"}
+
+        path = asset.get("object_path")
+        prefix = f"{sid}/renders/{job_id}/"
+        if not isinstance(path, str) or not path.startswith(prefix):
+            return 404, {"error": "OUTPUT_NOT_FOUND"}
+        if PRIVATE_FILE.fullmatch(path[len(prefix):]) is None:
+            # Only the immutable lease-token path emitted by private importer.
+            return 404, {"error": "OUTPUT_NOT_FOUND"}
+        return 200, {"url": self.users.sign_download(token, sid, path)}
~~~~

### azure-functions/campaign-api/premium_outbox.py
~~~~diff
@@ -0,0 +1,78 @@
+"""Source-only premium outbox/poison/recovery boundary, disabled by default.
+
+Requires unimplemented, audited service-role Postgres RPCs. No real timer,
+queue trigger, cloud account or premium paid API is created here.
+
+An at-least-once queue ACK can be ambiguous; underlying SQL job claim/lease
+must fence *all* worker actions so replays NEVER duplicate provider POSTs.
+"""
+from __future__ import annotations
+
+import hashlib
+from tenant_store import StorageUnavailable, canonical_uuid
+
+
+class PremiumRuntimeDisabled(RuntimeError):
+    pass
+
+
+def dispatch_premium_outbox(store, queue, *, enabled=False, limit=20):
+    if not enabled:
+        raise PremiumRuntimeDisabled("Premium publishing is disabled")
+    if type(limit) is not int or not 1 <= limit <= 50:
+        raise ValueError("Invalid premium outbox batch limit")
+    events = store.claim_outbox(limit)
+    if not isinstance(events, list):
+        raise StorageUnavailable("Invalid premium outbox claim")
+    count = 0
+    for event in events:
+        if not isinstance(event, dict) or event.get("kind") != "premium_video":
+            raise StorageUnavailable("Invalid premium outbox type")
+        try:
+            event_id = canonical_uuid(event["id"])
+            lease = canonical_uuid(event["lease_token"])
+            jid = canonical_uuid(event["job_id"])
+        except (ValueError, KeyError, TypeError) as exc:
+            raise StorageUnavailable("Invalid premium outbox receipt") from None
+
+        try:
+            queue.enqueue(jid)
+        except Exception:
+            # A failed send does not prove the queue rejected the message.
+            # SQL retains the event for CAS-fenced replay; do not claim
+            # success or create any provider job here.
+            store.confirm_outbox(event_id, lease, False)
+        else:
+            store.confirm_outbox(event_id, lease, True)
+            count += 1
+    return count
+
+
+def record_premium_poison(store, raw_body, *, enabled=False):
+    if not enabled:
+        raise PremiumRuntimeDisabled("Premium poison recovery is disabled")
+    if not isinstance(raw_body, bytes) or len(raw_body) > 65536:
+        raise ValueError("Invalid premium poison body")
+    fingerprint = hashlib.sha256(raw_body).hexdigest()
+    try:
+        candidate = raw_body.decode("ascii") if len(raw_body) == 36 else ""
+        jid = canonical_uuid(candidate) if candidate else None
+    except (UnicodeError, ValueError):
+        jid = None
+    # NEVER let a poison message directly set any customer/job status.
+    # Durable receipt, then operator/reconciler reviews cost and provider.
+    if store.record_poison("premium_video", fingerprint, jid) is not True:
+        raise StorageUnavailable("Premium poison receipt was not durable")
+    return jid
+
+
+def reconcile_premium_and_dispatch(store, queue, *, enabled=False):
+    if not enabled:
+        raise PremiumRuntimeDisabled("Premium recovery is disabled")
+    result = store.reconcile()
+    if not isinstance(result, dict):
+        raise StorageUnavailable("Invalid premium reconciliation receipt")
+    # Implementing SQL must NEVER turn UNKNOWN/SUBMITTING into QUEUED:
+    # an uncertain provider POST may have been charged.
+    count = dispatch_premium_outbox(store, queue, enabled=True)
+    return {"reconciliation": result, "dispatched": count}
~~~~

### azure-functions/campaign-api/premium_poll_completion.py
~~~~diff
@@ -0,0 +1,98 @@
+"""Source-only, fail-closed Wan poll -> verified private clip completion.
+
+No Azure trigger is registered here. A future protected service-role store must
+claim IMPORTING jobs atomically and issue a fenced lease. Never send provider
+URLs into HTTP responses, job queues, customer-visible DB rows or logs.
+"""
+from __future__ import annotations
+
+import re
+
+from premium_private_import import (
+    PremiumImportError, import_to_private_storage, validate_vendor_video_url,
+)
+from tenant_store import canonical_uuid
+
+TASK_ID = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
+
+
+class PremiumCompletionError(RuntimeError):
+    """Safe error with no provider URL, token, tenant prompt or raw payload."""
+
+
+class PremiumPollCompletion:
+    """Only the already-reserved, claim-fenced IMPORTING job can import video.
+
+    store.claim_import(job_id) MUST be an atomic service-role DB RPC that
+    returns id, shop_id, attempt_token, provider_task_id, status, seconds,
+    reservation_confirmed and holds the active lease. The returned claim
+    must come exclusively from the database, not from an HTTP/queue payload.
+    store.finalize(job, shop, lease, private_path) MUST atomically verify this
+    same active lease, tenant membership, and existing reservation.
+    """
+
+    def __init__(self, store, provider, media, *, enabled=False, opener=None,
+                 probe=None):
+        self.store, self.provider, self.media = store, provider, media
+        self.enabled, self.opener, self.probe = enabled, opener, probe
+
+    def run_once(self, job_id):
+        jid = canonical_uuid(job_id)
+        if not self.enabled:
+            raise PremiumCompletionError("Premium private completion is disabled")
+
+        claim = self.store.claim_import(jid)
+        if claim is None:
+            return {"job_id": jid, "status": "NOT_CLAIMED"}
+        try:
+            sid = canonical_uuid(claim["shop_id"])
+            token = canonical_uuid(claim["attempt_token"])
+            seconds = claim["seconds"]
+            task_id = claim["provider_task_id"]
+            if (canonical_uuid(claim["id"]) != jid or
+                claim["status"] != "IMPORTING" or
+                claim["reservation_confirmed"] is not True or
+                type(seconds) is not int or not 2 <= seconds <= 15 or
+                not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id)):
+                raise ValueError("Untrusted premium import claim")
+        except (AttributeError, KeyError, TypeError, ValueError):
+            raise PremiumCompletionError("Premium import claim is invalid") from None
+
+        # One task GET, not another billable create POST. Provider itself
+        # requires its independent owner-approved enabled/key/cost gates.
+        try:
+            result = self.provider.poll_private(task_id)
+            if not isinstance(result, dict) or result.get("task_id") != task_id:
+                raise PremiumCompletionError("Provider task identity mismatch")
+            status = result.get("status")
+            if status in ("PENDING", "RUNNING"):
+                return {"job_id": jid, "status": "AWAITING_PROVIDER"}
+            if status in ("FAILED", "CANCELED", "UNKNOWN"):
+                # UNKNOWN can be expiry; neither refund nor paid retry is safe.
+                # Operator must reconcile provider billing and state.
+                return {"job_id": jid, "status": "RECONCILE"}
+            if status != "SUCCEEDED":
+                raise PremiumCompletionError("Unsupported provider task state")
+            url = result.get("video_url")
+            validate_vendor_video_url(url)
+            params = {
+                "provider_url": url,
+                "shop_id": sid,
+                "job_id": jid,
+                "lease_token": token,
+                "expected_seconds": seconds,
+                "media": self.media,
+                "store": self.store,
+                "opener": self.opener,
+            }
+            if self.probe is not None:
+                params["probe"] = self.probe
+            complete = import_to_private_storage(**params)
+            return {"job_id": jid, "status": "SUCCEEDED",
+                    "output_asset_id": canonical_uuid(complete["output_asset_id"])}
+        except (PremiumImportError, PremiumCompletionError):
+            raise PremiumCompletionError("Premium import needs safe reconciliation") from None
+        except Exception:
+            # Unexpected provider/store errors also must not leak signed URLs.
+            # No silent retry, credit refund, duplicate POST or success flag.
+            raise PremiumCompletionError("Premium private completion unavailable") from None
~~~~

### azure-functions/campaign-api/premium_private_import.py
~~~~diff
@@ -0,0 +1,165 @@
+"""Fail-closed worker-only Wan output importer, OFF in production.
+
+Provider URL never goes to a customer. Follow NO redirects. Validate media
+before uploading to existing private RetailGrowthAI tenant storage. The
+caller must already hold a DB-fenced valid premium task and cost reservation.
+"""
+from __future__ import annotations
+
+import json
+import re
+import subprocess
+import tempfile
+from time import time
+from pathlib import Path
+from urllib.error import HTTPError, URLError
+from urllib.parse import urlparse, parse_qs
+from urllib.request import Request, build_opener, HTTPRedirectHandler
+
+from tenant_store import canonical_uuid, StorageUnavailable
+
+MAX_BYTES = 80 * 1024 * 1024
+# Reviewed examples in Alibaba Model Studio Wan API docs (Singapore/Beijing).
+HOST_PATTERN = re.compile(
+    r"^dashscope-(?:result-)?[a-z0-9-]{1,30}\.oss-(?:accelerate|[a-z0-9-]{2,35})\.aliyuncs\.com$"
+)
+
+
+class PremiumImportError(RuntimeError):
+    """Sanitized; never logs third-party signed URLs or tenant prompt data."""
+
+
+def _valid_signed_expiry(query):
+    """Reject expired, malformed or ambiguous OSS signature expiry values."""
+    try:
+        values = parse_qs(query, keep_blank_values=True)
+        candidates = values.get("Expires", []) + values.get("expires", [])
+        return (len(candidates) == 1 and
+                candidates[0].isdigit() and
+                int(candidates[0]) > int(time()) + 30)
+    except (TypeError, ValueError, OverflowError):
+        return False
+
+
+def validate_vendor_video_url(url):
+    if not isinstance(url, str) or len(url) > 2048:
+        raise PremiumImportError("Invalid private provider media reference")
+    try:
+        parsed = urlparse(url)
+        valid = (parsed.scheme == "https" and bool(parsed.hostname) and
+                 HOST_PATTERN.fullmatch(parsed.hostname) is not None and
+                 parsed.port in (None, 443) and
+                 not parsed.username and not parsed.password and
+                 not parsed.fragment and parsed.path.lower().endswith(".mp4") and
+                 len(parsed.path) <= 500 and
+                 not any(x in parsed.path.lower() for x in ("%2f", "%5c", "..")) and
+                 _valid_signed_expiry(parsed.query))
+    except ValueError:
+        valid = False
+    if not valid:
+        raise PremiumImportError("Untrusted provider media origin")
+    return url
+
+
+class NoRedirect(HTTPRedirectHandler):
+    def redirect_request(self, req, fp, code, msg, headers, newurl):
+        # Never follow a signed URL to a private IP, local metadata server or
+        # unreviewed secondary host, even if Alibaba changes its CDN.
+        return None
+
+
+def fetch_signed_video(url, output, *, opener=None):
+    validate_vendor_video_url(url)
+    opener = opener or build_opener(NoRedirect())
+    req = Request(url, headers={"Accept": "video/mp4,application/octet-stream"},
+                  method="GET")
+    try:
+        with opener.open(req, timeout=60) as response:
+            if response.status != 200:
+                raise PremiumImportError("Provider download unavailable")
+            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
+            if content_type not in ("video/mp4", "application/octet-stream", ""):
+                raise PremiumImportError("Unexpected provider content type")
+            length = response.headers.get("Content-Length")
+            if length is not None and (not length.isdigit() or int(length) > MAX_BYTES):
+                raise PremiumImportError("Provider video exceeds media limit")
+            total = 0
+            with open(output, "wb") as file:
+                while True:
+                    chunk = response.read(1024 * 1024)
+                    if not chunk:
+                        break
+                    total += len(chunk)
+                    if total > MAX_BYTES:
+                        raise PremiumImportError("Provider video exceeds media limit")
+                    file.write(chunk)
+    except (HTTPError, URLError, OSError) as exc:
+        raise PremiumImportError("Provider download failed") from exc
+    if total < 1024:
+        raise PremiumImportError("Provider video is empty")
+    with open(output, "rb") as file:
+        if file.read(12)[4:8] != b"ftyp":
+            raise PremiumImportError("Provider output is not MP4")
+    return total
+
+
+def probe_mp4(path):
+    try:
+        proc = subprocess.run(
+            ["ffprobe", "-v", "error", "-protocol_whitelist", "file",
+             "-show_format", "-show_streams", "-of", "json", str(path)],
+            capture_output=True, text=True,
+            timeout=30, check=True
+        )
+        return json.loads(proc.stdout)
+    except (OSError, ValueError, subprocess.CalledProcessError,
+            subprocess.TimeoutExpired) as exc:
+        raise PremiumImportError("Provider output could not be verified") from exc
+
+
+def verify_video(metadata, *, expected_seconds):
+    try:
+        seconds = float(metadata["format"]["duration"])
+        streams = metadata["streams"]
+        video = [s for s in streams if s.get("codec_type") == "video"]
+        if len(video) != 1 or video[0]["codec_name"] != "h264":
+            raise ValueError("invalid video codec")
+        width, height = int(video[0]["width"]), int(video[0]["height"])
+        if not (240 <= width <= 1920 and 240 <= height <= 1920 and
+                width % 2 == 0 and height % 2 == 0):
+            raise ValueError("invalid video dimensions")
+        if not (2 <= expected_seconds <= 15 and
+                expected_seconds - 1.5 <= seconds <= expected_seconds + 1.5):
+            raise ValueError("duration mismatch")
+    except (KeyError, TypeError, ValueError, IndexError) as exc:
+        raise PremiumImportError("Provider media failed codec/duration validation") from exc
+
+
+def import_to_private_storage(*, provider_url, shop_id, job_id, lease_token,
+                              expected_seconds, media, store, opener=None,
+                              probe=probe_mp4):
+    """Import under existing private bucket; finalize only via DB-fenced CAS.
+
+    The caller never supplies browser input here. A DB worker must map the
+    claim's shop_id/job_id/lease_token to this invocation, and store.finalize
+    must atomically check the current lease and persist output media metadata.
+    """
+    sid, jid, token = (canonical_uuid(x) for x in
+                       (shop_id, job_id, lease_token))
+    validate_vendor_video_url(provider_url)
+    with tempfile.TemporaryDirectory(prefix="rgai-premium-") as directory:
+        target = Path(directory) / "provider-clip.mp4"
+        fetch_signed_video(provider_url, target, opener=opener)
+        verify_video(probe(target), expected_seconds=expected_seconds)
+        # PrivateMedia.upload disables overwriting old output and strictly
+        # scopes to sid/renders/jid/token.mp4 in retailgrowth-media bucket.
+        private_path = media.upload(sid, jid, target, lease_token=token)
+        expected_path = sid + "/renders/" + jid + "/" + token + ".mp4"
+        if private_path != expected_path:
+            raise PremiumImportError("Private media receipt mismatch")
+        result = store.finalize(jid, sid, token, private_path)
+        if not isinstance(result, dict) or result.get("status") != "SUCCEEDED":
+            raise PremiumImportError("Lease-fenced private completion failed")
+        output_id = canonical_uuid(result.get("output_asset_id"))
+        return {"job_id": jid, "status": "SUCCEEDED",
+                "output_asset_id": output_id}
~~~~

### azure-functions/campaign-api/premium_queue.py
~~~~diff
@@ -0,0 +1,26 @@
+"""Dedicated premium Azure Storage Queue sender, NEVER provisioning cloud resources.
+
+One UUID per message, same pattern as existing free planning/render queues.
+The premium queue is absent from DEV until a separately approved deployment.
+"""
+from __future__ import annotations
+
+from tenant_store import canonical_uuid
+
+PREMIUM_QUEUE_NAME = "retail-premium-video"
+
+
+class AzurePremiumQueue:
+    def __init__(self, connection_string=None, *, client=None):
+        if client is None:
+            if not connection_string:
+                raise ValueError("Premium Storage connection required")
+            from azure.storage.queue import QueueClient
+            client = QueueClient.from_connection_string(
+                connection_string, queue_name=PREMIUM_QUEUE_NAME)
+        self.client = client
+
+    def enqueue(self, job_id):
+        jid = canonical_uuid(job_id)
+        # NO prompt, tenant, token, storage path, vendor URL or price may appear.
+        self.client.send_message(jid)
~~~~

### azure-functions/campaign-api/premium_video_jobs.py
~~~~diff
@@ -0,0 +1,185 @@
+"""Part 3 premium-video orchestration boundary (not wired to live Functions).
+
+Create/status is JWT/RLS scoped through injected existing RetailGrowthAI stores.
+Only a dedicated service-only database INSERT with a BEFORE INSERT quota trigger
+may reserve premium seconds. Workers only pass UUIDs in Azure Queue messages.
+Provider activation remains disabled by default; no paid request happens here.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+from uuid import uuid4
+
+from ai_agents.premium_video import (
+    WanRequest, AlibabaWanProvider, PremiumVideoDisabled, campaign_video_prompt
+)
+from tenant_store import canonical_uuid, StorageUnavailable
+
+AVAILABLE_MODES = ("text", "image")
+AVAILABLE_RESOLUTIONS = ("720P", "1080P")
+AVAILABLE_DURATIONS = range(2, 16)
+
+
+class PremiumVideoCoordinator:
+    def __init__(self, user_store, premium_store, rights_store,
+                 *, enabled=False):
+        self.user_store = user_store
+        self.premium_store = premium_store
+        self.rights_store = rights_store
+        self.enabled = enabled
+
+    def create(self, token, user_id, campaign_id, payload):
+        # Preserve the free FFmpeg path even if premium has no entitlement.
+        if not self.enabled:
+            return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
+        if not isinstance(payload, dict) or set(payload) != {
+            "day_id", "mode", "resolution", "duration_seconds", "input_asset_id"
+        }:
+            return 400, {"error": "INVALID_REQUEST"}
+        try:
+            cid = canonical_uuid(campaign_id)
+            did = canonical_uuid(payload["day_id"])
+            uid = canonical_uuid(user_id)
+            mode, resolution = payload["mode"], payload["resolution"]
+            duration = payload["duration_seconds"]
+            if (mode not in AVAILABLE_MODES or resolution not in AVAILABLE_RESOLUTIONS
+                or type(duration) is not int or duration not in AVAILABLE_DURATIONS):
+                return 400, {"error": "INVALID_REQUEST"}
+            asset = payload["input_asset_id"]
+            if mode == "image":
+                asset = canonical_uuid(asset)
+            elif asset is not None:
+                return 400, {"error": "INVALID_REQUEST"}
+            campaign = self.user_store.campaign(token, uid, cid)
+            if campaign is None:
+                return 404, {"error": "NOT_FOUND"}
+            sid = canonical_uuid(campaign["shop_id"])
+            if campaign["status"] != "DRAFT":
+                return 409, {"error": "CAMPAIGN_NOT_DRAFT"}
+            if not self.user_store.member(token, uid, sid, write=True):
+                return 403, {"error": "FORBIDDEN"}
+            days = [d for d in campaign["days"]
+                    if d.get("id") == did and d.get("shop_id") == sid]
+            if len(days) != 1 or days[0].get("review_status") != "APPROVED":
+                return 409, {"error": "DAY_NOT_APPROVED"}
+            if mode == "image":
+                # Existing user-JWT RLS asset check + service-only rights check.
+                owned = self.user_store.asset(token, sid, asset)
+                if owned is None or owned.get("mime_type") not in (
+                        "image/png", "image/jpeg", "image/webp"):
+                    return 403, {"error": "IMAGE_NOT_AUTHORIZED"}
+                if not self.rights_store.valid_media(sid, [asset]):
+                    return 403, {"error": "ASSET_RIGHTS_UNVERIFIED"}
+            # Only approved (already reviewed) day content enters the provider.
+            prompt = campaign_video_prompt(days[0])
+            canonical = [uid, sid, cid, did, mode, resolution, duration,
+                         asset, prompt]
+            digest = hashlib.sha256(json.dumps(canonical, sort_keys=True,
+                separators=(",", ":")).encode("utf-8")).hexdigest()
+            previous = self.premium_store.find_authenticated(token, sid, digest)
+            if previous is not None:
+                return 200, self._public(previous)
+            row = {
+                "id": str(uuid4()), "shop_id": sid, "campaign_id": cid,
+                "day_id": did, "requested_by": uid, "mode": mode,
+                "model_id": ("wan2.7-t2v-2026-06-12" if mode == "text"
+                             else "wan2.7-i2v-2026-04-25"),
+                "resolution": resolution, "seconds": duration,
+                "input_asset_id": asset, "idempotency_key": digest,
+                "status": "QUEUED"
+            }
+            # insert_reserved is a *single* DB write, protected by the new
+            # subscription row-lock + shared usage ledger trigger. A second
+            # distinct client POST cannot create spend outside that trigger.
+            try:
+                created = self.premium_store.insert_reserved(row)
+            except StorageUnavailable:
+                existing = self.premium_store.find_authenticated(token, sid, digest)
+                if existing is not None:
+                    return 200, self._public(existing)
+                raise
+            if not isinstance(created, dict) or created.get("id") != row["id"]:
+                raise StorageUnavailable("premium insert verification failed")
+            # Queue publication is NOT performed here: a durable outbox trigger
+            # and idempotent service worker are required before this API may
+            # be routed in production.
+            return 202, self._public(created)
+        except (TypeError, ValueError, AttributeError, KeyError):
+            return 400, {"error": "INVALID_REQUEST"}
+
+    def status(self, token, user_id, job_id):
+        if not self.enabled:
+            return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
+        jid = canonical_uuid(job_id)
+        job = self.premium_store.get_authenticated(token, jid)
+        if job is None or not self.user_store.member(token, user_id, job["shop_id"]):
+            return 404, {"error": "NOT_FOUND"}
+        return 200, self._public(job)
+
+    @staticmethod
+    def _public(job):
+        # Never include cost controls, backend provider task IDs, signed URLs,
+        # API credentials or storage object paths in JSON returned to users.
+        return {k: job.get(v) for k,v in {
+            "job_id": "id", "status": "status", "output_asset_id": "output_asset_id",
+            "error_code": "error_code"
+        }.items()}
+
+
+class PremiumSubmissionWorker:
+    """Lease-fenced source-only worker bridge for durable Azure UUID triggers.
+
+    If an async task submission response is uncertain, mark UNKNOWN; NEVER
+    issue another provider POST automatically because that might double charge.
+    """
+    def __init__(self, store, provider: AlibabaWanProvider):
+        self.store, self.provider = store, provider
+
+    def submit_once(self, job_id):
+        jid = canonical_uuid(job_id)
+        claim = self.store.claim(jid)
+        if claim is None:
+            return "NOT_CLAIMED"
+        if claim.get("status") != "SUBMITTING" or not claim.get("attempt_token"):
+            raise StorageUnavailable("invalid premium lease")
+        try:
+            request = WanRequest(
+                mode=claim["mode"], prompt=claim["prompt"],
+                duration_seconds=claim["seconds"],
+                resolution=claim["resolution"],
+                signed_first_frame=claim.get("signed_first_frame"),
+                shop_id=claim["shop_id"]
+            )
+            result = self.provider.submit(request)
+        except PremiumVideoDisabled:
+            self.store.finish_attempt(jid, claim["attempt_token"],
+                                      "FAILED", error_code="PROVIDER_NOT_APPROVED")
+            return "FAILED"
+        except Exception:
+            # Even if a request might have reached the provider, it is never
+            # safe to auto-post again. Human reconciliation must inspect it.
+            self.store.finish_attempt(jid, claim["attempt_token"],
+                                      "UNKNOWN", error_code="PROVIDER_RESULT_UNKNOWN")
+            return "UNKNOWN"
+        self.store.record_task(jid, claim["attempt_token"], result["task_id"])
+        return "PENDING"
+
+    def poll_once(self, job_id):
+        jid = canonical_uuid(job_id)
+        claim = self.store.claim_poll(jid)
+        if claim is None:
+            return "NOT_CLAIMED"
+        task_id, lease = claim["provider_task_id"], claim["attempt_token"]
+        result = self.provider.poll(task_id)
+        if result["status"] in ("PENDING", "RUNNING"):
+            self.store.record_poll(jid, lease, result["status"])
+        elif result["status"] == "SUCCEEDED":
+            # MUST NOT mark SUCCEEDED until provider bytes have been safely
+            # imported, ffprobed, uploaded to PRIVATE shop storage and a signed
+            # RetailGrowthAI link is provisioned. Keep pending importer state.
+            self.store.record_poll(jid, lease, "IMPORTING")
+        else:
+            self.store.record_poll(jid, lease, "FAILED")
+        return result["status"]
~~~~

### azure-functions/campaign-api/premium_worker.py
~~~~diff
@@ -0,0 +1,121 @@
+"""Premium job lifecycle; code only, no registered Azure trigger or paid API calls.
+
+Production store MUST be the service-role DB adapter with atomic, lease-token-
+fenced claim/state RPCs and an idempotent, transactional outbox. The caller must
+supply the already-reviewed, tenant-authorized request; no user-supplied URLs.
+"""
+from __future__ import annotations
+import re
+from dataclasses import dataclass
+from typing import Protocol
+from uuid import UUID
+
+_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
+
+
+class PremiumLifecycleError(RuntimeError):
+    """Sanitized lifecycle error; never includes prompts, keys or media URLs."""
+
+
+def normalized_id(value):
+    if not isinstance(value, str) or not _UUID.fullmatch(value):
+        raise ValueError("Invalid premium job identifier")
+    if str(UUID(value)) != value:
+        raise ValueError("Noncanonical premium job identifier")
+    return value
+
+
+@dataclass(frozen=True)
+class Claim:
+    id: str
+    shop_id: str
+    attempt_token: str
+    mode: str
+    prompt: str
+    duration_seconds: int
+    resolution: str
+    expected_usd: float
+    asset_id: str | None = None
+
+    def __post_init__(self):
+        normalized_id(self.id)
+        normalized_id(self.shop_id)
+        normalized_id(self.attempt_token)
+        if self.mode not in ("text", "image"):
+            raise ValueError("Invalid premium task mode")
+        if type(self.duration_seconds) is not int or not 2 <= self.duration_seconds <= 15:
+            raise ValueError("Invalid reserved premium duration")
+        if self.resolution not in ("720P", "1080P"):
+            raise ValueError("Invalid reserved resolution")
+        if type(self.expected_usd) not in (float, int) or self.expected_usd <= 0:
+            raise ValueError("Missing server-reserved cost")
+        if not isinstance(self.prompt, str) or not self.prompt.strip():
+            raise ValueError("Missing reviewed prompt")
+        if (self.mode == "image") != (self.asset_id is not None):
+            raise ValueError("Invalid image attachment mode")
+        if self.asset_id is not None:
+            normalized_id(self.asset_id)
+
+
+class PremiumStore(Protocol):
+    def claim_queued(self, job_id: str) -> Claim | None: ...
+    def mark_submitting(self, job_id: str, attempt_token: str) -> bool: ...
+    def mark_pending(self, job_id: str, attempt_token: str,
+                     provider_task_id: str) -> bool: ...
+    def mark_unknown(self, job_id: str, attempt_token: str) -> bool: ...
+
+
+class PremiumJobWorker:
+    """At most one provider POST per persistent QUEUED -> SUBMITTING transition.
+
+    If the HTTP response is lost, job remains UNKNOWN and NEVER re-submits on
+    ordinary replay. Operator/provider reconciliation is a separate approved
+    action. Reject stale attempts rather than duplicate user/provider cost.
+    """
+    def __init__(self, store: PremiumStore, provider, *,
+                 resolve_signed_frame=None, enabled=False):
+        self.store, self.provider = store, provider
+        self.resolve_signed_frame = resolve_signed_frame
+        self.enabled = enabled
+
+    def submit_queued(self, job_id: str):
+        from ai_agents.premium_video import WanRequest
+        jid = normalized_id(job_id)
+        if not self.enabled:
+            raise PremiumLifecycleError("Premium generation is disabled")
+        claim = self.store.claim_queued(jid)
+        if claim is None:
+            return {"status": "ALREADY_CLAIMED", "job_id": jid}
+        if claim.id != jid:
+            raise PremiumLifecycleError("Claim identity mismatch")
+        if not self.store.mark_submitting(jid, claim.attempt_token):
+            return {"status": "ALREADY_CLAIMED", "job_id": jid}
+
+        # A successful transition to SUBMITTING is the durable boundary.
+        # A later error must never cause a second provider POST by retry.
+        try:
+            frame = None
+            if claim.mode == "image":
+                if self.resolve_signed_frame is None:
+                    raise PremiumLifecycleError("Secure media resolver unavailable")
+                frame = self.resolve_signed_frame(claim.shop_id, claim.asset_id)
+            spec = WanRequest(claim.mode, claim.prompt, claim.duration_seconds,
+                              claim.resolution, signed_first_frame=frame,
+                              shop_id=claim.shop_id if claim.mode == "image" else None)
+            if self.provider.estimated_usd(spec) > claim.expected_usd + 1e-7:
+                raise PremiumLifecycleError("Provider cost exceeds DB reservation")
+            result = self.provider.submit(spec)
+        except Exception:
+            # May have been accepted remotely despite a transport failure.
+            # This is NOT proof of zero charge; never silently refund or retry.
+            if not self.store.mark_unknown(jid, claim.attempt_token):
+                raise PremiumLifecycleError("Cannot persist uncertain premium status")
+            return {"status": "UNKNOWN", "job_id": jid}
+        if result.get("status") != "PENDING" or not isinstance(result.get("task_id"), str):
+            if not self.store.mark_unknown(jid, claim.attempt_token):
+                raise PremiumLifecycleError("Cannot persist uncertain premium status")
+            return {"status": "UNKNOWN", "job_id": jid}
+        if not self.store.mark_pending(jid, claim.attempt_token, result["task_id"]):
+            # A provider task may already be charging; never retry on CAS failure.
+            raise PremiumLifecycleError("Provider accepted but DB acknowledgment failed")
+        return {"status": "PENDING", "job_id": jid}
~~~~

### docs/DECISIONS.md
~~~~diff
@@ -253,3 +253,29 @@
 ## 2026-10-23 — Live quota-enabled Part 1 acceptance
 - Declare hosted DEV content plus trial-quota acceptance only after a single genuine end-to-end pass with all steps and cleanup. [#39958569041 attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39958569041) meets this: real Foundry, JWT/RLS tenant isolation, shop auto-trial, exactly one campaign and render reservation, safe draft edit, H264 30-second signed private MP4 and teardown. No paid checkout or self-upgrade exists.
 - Intermittent Azure gateway 503 is tracked separately as availability tuning; use guarded reads/CAS/idempotent render retries, not weaker authorization. Read-only audit found all 11 Functions and zero queue backlog.
+
+## 2026-10-23 — Part 3 independent integration decisions (source-only)
+- Preserve working Part 1 FFmpeg render as default; premium WAN is a disabled opt-in provider alternative (no production branch switch). No customer-paid checkout, automatic activation, external Wan API calls or unrelated resource reuse without approved region/rights/budget.
+- Independent Part 3 integration and internal PRs may self-merge into `feat/part3-integration`, **never** direct to main; final Coordinator reviews shared CI/UI/schema compatibility against a later concurrently updated main.
+- Extend existing `shop_subscriptions`/`shop_usage_reservations` quota architecture for premium seconds/USD rather than a parallel billing system; staged SQL defaults to ZERO. Canonical Supabase migration files and hosted DEV DB history are protected; promotion only after a NEW reviewed migration and isolated security tests.
+- Use approved Alibaba Wan 2.7 async T2V/I2V with server-only keys, tenant/private image rights and dollar cap; on uncertain paid POST response mark UNKNOWN, never blindly duplicate. Store provider output only in tenant private storage after signed-origin verification and ffprobe, return no vendor URLs or sensitive status fields to frontend.
+- The dedicated premium worker and SQL are intentionally incomplete/not wired to live Function triggers, so activation must remain false; provider substitution, cancellation/reconciliation, real price quote and media retention require separate design/test approval.
+
+## 2026-10-24 — Part 3 internal output/FFmpeg boundary (source only)
+- Never use a vendor-signed Wan task output URL as a browser-download link, API response, durable queue payload or stored customer metadata. `poll()` exposes only safe status; `poll_private()` is an internal provider adapter and only a database-lease-fenced importer consumes its link. Reject expired/ambiguous signed URL before any network fetch, and complete by tenant-private media + CAS only.
+- Keep the existing Part1 standard FFmpeg render and quotas unchanged and default. The new `video-engine/premium_compose.py` is an optional separate 30-second assembly requiring prior private clip imports, tenant ownership, current commercial rights, validated codec/size/duration, optional independently licensed music and exact 30-second timeline. Do not silently send another paid provider POST, charge double or claim fallback refunds. No cloud or customer activation from this source.
+- Owner commercial provider/workspace, media consent, per-shop cost allocation and one bounded paid smoke remain separate release gates; reviewed schema and worker integration still pending. Coordinator merges final PR #125 only after compatibility.
+
+## 2026-10-24 — Additional Part 3 safety decisions #193–#196
+- An actual 30-second local FFmpeg **synthetic** video/audio smoke is the minimum offline composition evidence. It is NOT evidence of Alibaba Wan paid output or commercial media licensing. Preserve default cost-free FFmpeg and original public API.
+- New premium user API uses separate JWT-verified, tenant-RLS-enabled adapter for job create/status/download; only exact existing private-media signed URL path can be returned. The adapter remains disabled until DB/credit/worker security gates are complete; never expose provider task/media URL.
+- Human approval is REQUIRED before external paid Wan processing. The selected `campaign_days.review_status` must equal `APPROVED`; `DRAFT`, `REJECTED` and missing status are denied in Python and staged SQL. Actual safe status transition and revision revocation remain a separate authenticated contract gate.
+- Premium delivery requires its **own** `retail-premium-video` UUID-only Azure Queue and service-owned transactional outbox. Do NOT use Part1 existing render queues or automatically retry provider submissions after ambiguous vendor acceptance. Poison receipts record digest, not body or credentials. No queue cloud provisioning/paid services/hosted schema migration authorized by source.
+
+## 2026-10-24 — Part 3 strict media receipt and offline-only probe
+- An imported premium media asset may be finalized ONLY when the actual returned storage path equals `{shop_uuid}/renders/{job_uuid}/{lease_uuid}.mp4`; a shared prefix alone is inadequate. Never report success for a forged object path, even if the media transport upload returned success.
+- Always set the `file`-only FFprobe protocol whitelist when inspecting externally generated MP4; provider output is untrusted data. All premium media remains privately stored, with short-lived, authenticated RetailGrowthAI download links and no direct vendor URL to browsers.
+
+## 2026-10-24 — Premium cancellation is provable only before provider submission
+- Cancellation can automatically release a **premium reservation**, not customer money, only through one database transaction that wins the race against the job's durable `QUEUED → SUBMITTING` CAS, rechecks active tenant write membership, and proves provider submission never started. The receipt must prove exact job/shop, `CANCELED`, no provider task, and ledger credit release. A lost race or partial receipt is a 409/503, never an asserted refund.
+- Once SUBMITTING, PENDING, RUNNING, IMPORTING, UNKNOWN, FAILED or SUCCEEDED, cancellation and any credit reconciliation require reviewed provider usage evidence; never blind POST retry or refund. Source-only boundary remains disabled until a tested service-role SQL RPC is wired. FFmpeg and the existing subscriptions ledger remain authoritative.
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -291,3 +291,41 @@ Baseline: `main` `84c9b87`, [latest completed 4/4 main CI #39805920327](https://
 - DONE: [Live run #39958569041 attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39958569041) SUCCESS: authenticated two-tenant trial, single campaign and render reservations, real Foundry seven-day plan, saved draft, 30-second signed private H264 MP4 and complete cleanup. 0 residual test users/shops/usage in Supabase. No extra resources or migration replay needed.
 - Next Part 1 improvement: investigate intermittent Azure gateway 503/cold-start performance (safe bounded retry already works); [runtime audit #39950554363 attempt 3](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39950554363) healthy, all queues empty.
 - Paid plans still require separately approved pricing, billing provider and server-side renewal flow; STARTER/GROWTH/BUSINESS are candidate identifiers, not purchasable. Keep Parts 2/3 and other projects out of scope.
+
+## 2026-10-23 — Part 3 own integration follow-ons (not Part 1 deployment tasks)
+- [x] Wan 2.7 official provider/version/region/cost research; no paid API call.
+- [x] Isolated and merged reviewed internal PRs #109 provider, #113 premium jobs/staged SQL, #115 optional UI, #122 provider-private media import. All existing CI checks verified on their PR heads.
+- [ ] Before any premium enablement: Coordinator to rebase against *latest main*, review shared UI/CI and candidate v2 contracts (preserve immutable Part1 v1 APIs), review migration manifest and promote **staged** `azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql` into a newly approved canonical timestamp. Do NOT apply hosted schema yet.
+- [ ] Complete service-only DB RPCs/atomic outbox, premium queue/poison/cancellation and fenced lease, sanitized GET/POST REST endpoints, safe provider output origin validation and actual private importer lifecycle. Finish concurrency/negative SQL, idempotent unknown-provider accounting and 30-second FFmpeg composition/fallback.
+- [ ] Final owner approvals for Alibaba paid workspace, commercial license, consent and reviewed maximum spend; only then one bounded, explicitly approved LIVE provider E2E. Default `RETAIL_PREMIUM_VIDEO_ENABLED=false`; premium seconds and USD budget 0; no customer charge or paid provider requests.
+- [ ] Final Part 3 Coordinator-only PR from integration → main must stay unmerged until security, compatibility and live cost gates are cleared. No direct main changes, Part2 publishing effects, WineShopPOS or GenAI Galaxy modifications.
+
+## 2026-10-24 — Part 3 remaining after source milestones #188/#189
+- [x] Internal workstream #188: implement offline safe Wan SUCCESS result retrieval -> claim/tenant-reservation-fenced private import bridge; signed OSS URL expiry/SSRF checks. [2/2 Part3 and 4/4 existing CI](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/188); merged into Part3 only, **not** registered in Azure.
+- [x] Internal workstream #189: implement source-only licensed 2-8 clip Wan-to-30s FFmpeg assembler with test-only command simulation/invalid-MP4 real preflight, keeping Part1 renderer free/default. [2/2 Part3 and 4/4 existing CI](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/189). Does **not** prove a real 30-second provider composition or a deployed user flow.
+- [ ] Priority 1: review and migrate proposed P3 SQL and implement actual DB tenant/lease/credit/worker RPCs with disposable tenant-negative and concurrency tests; hosted schema application separately owner-approved.
+- [ ] Priority 2: authenticated premium API and independent transactional outbox, timer+UUID queue, worker/poison/cancellation/poll/import pipeline, client entitlement/selection and signed download; flag remains off.
+- [ ] Priority 3: actual FFmpeg multi-clip media smoke using synthetic licensed fixtures, quality/CTA/music/crossfade review, hybrid free stock fallback and real provider substitution only after independent prices/terms approval.
+- [ ] Priority 4: final cost/rights/provider grants and paid DEV smoke require explicit owner approval; never enable billable requests without it.
+- [ ] Final Coordinator review/rebase and DRAFT PR #125 to main, no direct Part 3 merge to main.
+
+## 2026-10-24 — Part 3 follow-up after independent PRs #193–#196
+- [x] Confirm actual synthetic 30-second H264/AAC composite and decoded clip order; #193 passed standard 4/4 + Part3 2/2, NO provider call.
+- [x] Implement disabled and unaffiliated premium HTTP create/status/private download source adapter with scoped JWT/asset ownership; #194 verified, **not mounted to Function App**.
+- [x] Prevent paid processing of generated unapproved DRAFT day in coordinator + review-only SQL; #195 verified. An authorized human `APPROVED` workflow is STILL missing in Part1 public APIs.
+- [x] Isolate disabled UUID-only premium queue, CAS outbox, poison and recovery source protocol; #196 verified. No actual premium queue or hosted RPC registration.
+- [ ] Finish/independently review atomic billing/idempotency/approval/outbox SQL, implement service-role CAS/claim and lease/finalization with cross-tenant/concurrency/rollback negative tests, then seek separate owner approval before applying any hosted SQL.
+- [ ] Wire disabled-by-default protected premium Function HTTP routes and isolated Azure timers/queue/worker/poller/recovery with verified keys and spending limits ONLY after schema/cloud approvals; source-only modules do not satisfy this.
+- [ ] Implement version-fenced content approval, cancellation/UNKNOWN vendor reconciliation, provider credit quote/real spent cost and safe session concurrency; source Wan2.7 2–15s clips and FFmpeg concat do not constitute live video generation.
+- [ ] Brand overlays/CTA, source image/music rights and signed download end-to-end; optional Wan provider substitution must be separately priced/licensed.
+- [ ] Obtain commercial paid provider workspace/region/legal spend approval for one strictly capped DEV Wan real-world test; do not start paid requests without it.
+- [ ] Final Coordinator PR #125 remains DRAFT, not merged; coordinator reconciles newest Part1/Part2 `main`.
+
+## 2026-10-24 — Part 3 media hardening completion
+- [x] PR #198 private import security: exact immutable tenant/job/lease .mp4 receipt required before DB finalization, `ffprobe` local-only protocol whitelist and forged-path tests; merged to `feat/part3-integration` after all six CI successes.
+- [ ] Existing P3 blockers unchanged: approved premium SQL + atomic credit/lease/outbox RPCs and negative concurrent DB tests; actual disabled Azure HTTP and premium queue/timer/poison wiring; approval/consent versioning; billing and UNKNOWN/cancellation reconciliation; branded mixed AI+stock composition and real Wan E2E; owner approval for paid provider/workspace/spending, then final Coordinator reconciliation/merge.
+
+## 2026-10-24 — Part 3 next after queued-cancel contract (#226)
+- [x] Source-only cancellation authorization / no-double-refund contract and mock race tests merged into `feat/part3-integration`: six GitHub CI jobs passed for PR #226.
+- [ ] **Blocking:** implement and REVIEW a single serializable/row-locked server-only `cancel_unsubmitted_atomic` RPC against the existing premium reservation ledger, with simultaneous QUEUED→SUBMITTING CAS race tests. Do not return success/credit on uncertain provider submission. Do not apply staged premium migration to DEV before approval.
+- [ ] Activate additive premium JWT HTTP, Azure premium job queues, outbox/poison/poll service-role persistence only after approved schema/security/cost/rights gates. All premium flags and allowances remain ZERO/OFF; live paid provider test requires specific approval. Coordinator alone merges final DRAFT PR #125 to main when qualified.
~~~~

### docs/PART3_IMPLEMENTATION.md
~~~~diff
@@ -0,0 +1,51 @@
+# Part 3 — implementation map and integration gates
+
+**Integration:** `feat/part3-integration` → final single coordinator-reviewed PR to `main`.
+**Current status:** source under active implementation, not enabled/deployed, no billable test run.
+
+## Branch/workstream ownership
+
+| Workstream | Branch | Scope | Completion boundary |
+| --- | --- | --- | --- |
+| P3-A: provider + t2v/i2v + prompt | `feat/p3-wan-provider` (#109) | `ai-agents/src/ai_agents/premium_video.py`, provider tests, provider handoff | Async Wan2.7 adapter and mock gates only; actual Wan3.0 upgrade/approval separate |
+| P3-B: entitlement, ledger, state, retries | `feat/p3-premium-jobs` (#113) | additive `supabase/migrations/20261023180000_p3_premium_video_reservations.sql`, independent service modules, Python tests | zero-allowance server-owned atomic reservations and UNKNOWN-safe prototype; no applied SQL or worker |
+| P3-C: frontend selection | `feat/p3-premium-ui` (#115) | `frontend/src/features/premium-video/**`, isolated JS tests | FFmpeg default, premium disabled; not mounted in shared CampaignDashboard |
+| P3-D: durable dispatch and Azure worker | **Not yet branched** | proposed new `azure-functions/campaign-api/premium_dispatch/**`, tests | exact queued UUID, transactional outbox, durable DB claim, timer/poll/poison, no existing queue trigger collision |
+| P3-E: private ingestion + substitution | **Not yet branched** | proposed `azure-functions/campaign-api/premium_media/**`, media tests | validate provider destination/CDN/size/codec, private per-shop object+output media registration, existing private signed URL; explicit free FFmpeg fallback |
+| P3-F: cancellation/refunds/security/performance | **Not yet branched** | independent security negative tests, performance and reconciliation runbook | no double charge, safe cancel before request, uncertain provider charges marked UNKNOWN, admin reconciliation, concurrency and load guardrails |
+
+Do not claim a branch or PR exists unless verified. Independent branches must be based on the current Part 3 integration tip when actually started, with disjoint path ownership.
+
+## Integration API proposal — stage, do not change shared v1 silently
+
+- Future authenticated `POST /api/campaigns/{campaign_id}/premium-videos` accepts `{day_id, mode, resolution, duration_seconds, input_asset_id}`, no arbitrary path/URL/model ID; server derives selected provider, reviewed prompt, consent and price. Return `202 {job_id,status}` only if quota AND durable enqueue/outbox exist.
+- Future authenticated `GET /api/premium-video-jobs/{job_id}` returns sanitized `{job_id,status,output_asset_id,error_code}`, tenant-filtered. Download should use the existing short-lived signed private mechanism, not provider CDN links.
+- Existing `POST /api/campaigns/{id}/renders` and `GET /api/render-jobs/{id}` retain exactly their Part 1 meanings. Keep FFmpeg default; no implicit premium provider billable fallback.
+- Route/contract additions and CampaignDashboard placement are staged for joint review with Part 2 coordinator; never edit overlapping Part 2 shared paths independently.
+
+## Security and spending invariants
+
+1. Existing RLS membership/asset provenance must be checked on request and again before provider transfer. Cloud service role cannot rely on only shop ID from the browser.
+2. Existing subscription ledger `shop_usage_reservations` is the only quota source. Each premium job must have one idempotent atomic reservation of seconds and maximum USD (rounded up at vendor price); zero allowances by default. No self-service upgrades, card charges, Razorpay, or second billing system.
+3. DB transaction writes a durable outbox event alongside accepting a job. Azure queued messages contain UUID only. Token-fenced job claims and owner-only or service-only status mutation prevent cross-tenant state writes.
+4. Set SUBMITTING durably before contacting a paid provider. Network uncertainty is UNKNOWN: never automatically repeat POST or refund as though no provider charge occurred. Poll existing task IDs; time-limited URLs must be privately imported before expiry.
+5. Cancel QUEUED locally only after atomic cancellation and release proof. Once SUBMITTING/PENDING or uncertain, cancellation/credit refund requires verified provider cancellation/billing semantics.
+6. No uncontrolled SSRF or arbitrary HTTPS import; allowlist provider-origin download host, limit bytes/video streams/frame dimension, validate output via ffprobe, store in existing `retailgrowth-media` bucket.
+7. No tokens, commercial inputs, signed URLs, model prompt with PII, or credentials in CI logs. Explicit image transfer/commercial license/AI disclosure consent before use.
+8. Strict global/preset/user cost ceiling, alerts and approval flag; no provider key in `VITE_*`.
+
+## Pre-merge verification
+
+- Verify all existing **four** standard CI jobs on each PR and after integration. Dedicated P3 Python/security unit and mocked video tests must run and be inspectable, not inferred from source presence.
+- Apply and negative-test the *new migration only* in disposable Postgres. Hosted DEV migration prohibited until explicit reviewed scope/approval. No Part 1 migration replay.
+- Exercise mock provider creation and polling, timeouts/duplicates, failed storage upload, tenant denial, cancellation boundary, FFmpeg free fallback, UI disabled state and no double reservation.
+- Run any truly billable and externally transferring smoke only after the separate owner/provider/license/region/cost consent gates. All existing Part 1 production and other repositories remain unchanged.
+
+## Snapshot and blockers
+
+Verified internal PRs: #109 / #113 / #115, each targeting `feat/part3-integration`. Their source currently includes offline tests, but this document **does not assert the CI runs completed**. The Phase 3 integration is **not complete**: outbox/RPCs, provider output ingestion, Wan3.0 adapter, compiled frontend placement, actual deployment, billing approval, hosted negative tests and live generation remain open. Do not merge any PR or the final branch solely on this documentation.
+
+## LATEST source checkpoint — 2026-10-23 (supersedes earlier pre-merge snapshot)
+- The previous snapshot was a preliminary design. Internal PRs #109, #113, #115, #122 each passed *four existing* and *two additional Part 3* CI checks and were actually merged into **feat/part3-integration** only. A private output importer is now source-implemented, but no live importer worker, provider account or paid calls exist.
+- The premium React panel was mounted **disabled by default** after the existing FFmpeg controls on the Part 3 integration branch; it has no premium POST handler in production. FFmpeg remains the active default.
+- Proposed quota SQL was intentionally MOVED OUT of supabase/migrations to azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql after the strict Part 1 migration whitelist test rejected automatic schema drift. No hosted migration applied. Live queue/outbox/API routes/credit concurrency tests and approved Wan generation remain outstanding. The final Coordinator draft PR #125 → main is NOT ready for merge until these dependencies are reviewed.
~~~~

### docs/PART3_PROVIDER_RESEARCH.md
~~~~diff
@@ -0,0 +1,64 @@
+# RetailGrowthAI — Part 3 Provider and Cost Evaluation (2026-10-23)
+
+**State: research and disabled source prototypes only. No approved account, paid video call, hosted migration, cloud worker or customer charge.** Preserve Part 1 FFmpeg as the default for all shops.
+
+## Current official Alibaba provider matrix
+
+Official sources:
+- Wan 3.0 standard: https://www.alibabacloud.com/help/en/model-studio/wan3-0-video
+- Wan 3.0 Prime: https://www.alibabacloud.com/help/en/model-studio/wan3-0-video-prime
+- Wan 3.0 API/guide: https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-guide
+- Wan 2.7 text API: https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
+- Wan 2.7 image API: https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference
+- Price table: https://www.alibabacloud.com/help/en/model-studio/model-pricing
+
+| Model ID | Text/Image | Duration | Resolution | Singapore nominal price / output second |
+| --- | --- | --- | --- | --- |
+| wan3.0-video | both, plus other references | 2–30s | 480P/720P/1080P | $0.05 / $0.10 / $0.20 |
+| wan3.0-video-prime | both, speed-oriented | 2–30s | 480P/720P/1080P | $0.068 / $0.14 / $0.28 |
+| wan2.7-t2v-2026-06-12 | text | 2–15s | 720P/1080P | $0.10 / $0.15 |
+| wan2.7-i2v-2026-04-25 | image-first-frame | 2–15s | 720P/1080P | $0.10 / $0.15 |
+
+Prices above are Alibaba's published original list prices, **not a negotiated commitment**. The Wan 3.0 site advertises a dated discount ending 2026-09-24; do NOT use that expired promotion in pricing policy. Other deployment regions have different prices and must be verified independently with matched model, API key, workspace and endpoint. Availability must be checked in the actual target workspace before activation. WAN 3.0 now supports a single full 30-second output and is a candidate for the production adapter; narrow Wan 2.7 source implementation remains sandboxed for now.
+
+### Illustrative clip cost excluding tax, FX fees and storage
+
+Using October 23 USD/INR reference **~₹94.9 per USD** (https://wise.com/us/currency-converter/usd-to-inr-rate/history/23-10-2026):
+
+| Output | Alibaba list cost | Indicative INR |
+| --- | ---: | ---: |
+| Wan3.0 standard 30s 720p | $3.00 | ~₹285 |
+| Wan3.0 standard 30s 1080p | $6.00 | ~₹569 |
+| Wan3.0 Prime 30s 720p | $4.20 | ~₹399 |
+| Wan3.0 Prime 30s 1080p | $8.40 | ~₹797 |
+| Wan2.7 15s 720p | $1.50 | ~₹142 |
+| Wan2.7 15s 1080p | $2.25 | ~₹214 |
+
+**Free promotional quota is never assumed**; its eligibility, region, model and expiry may change. Output billing and real invoicing should be reconciled via provider usage, not UI estimates. Reserve the worst-case cost before any request, retain reservations for UNKNOWN attempts, enforce daily/provider and per-shop ceilings, and reconcile actual usage after success/failure before credit release. Trial and existing plan premium allowance remains zero.
+
+## Async tasks, safety and rights
+
+- The official APIs require async submission and task-ID polling; output URLs and task IDs are time-limited (documented ~24h). Never repeat a provider POST after uncertain acceptance. Persist SUBMITTING before send; after response loss, UNKNOWN pending reconciliation rather than another paid POST.
+- Video is generated outside the RetailGrowthAI Supabase/Azure storage boundary. Require explicit product/data-region review and commercial-rights and user-media consent before transferring customer images. Only server-issued short-lived tenant-private storage links may be inputs; do not accept arbitrary HTTP URLs. Verify file size/MIME/license/provenance and reject unsupported/regulated claims.
+- Model Studio product terms: https://www.alibabacloud.com/help/en/legal/latest/alibaba-cloud-international-website-product-terms-of-service-v-3-8-0 — provider says it does not claim ownership of Output IPR, but customers remain responsible for input/output lawful use, data protection and necessary consents. This is **not** blanket copyright clearance or a guarantee of exclusivity. Review current agreement, relevant jurisdiction and commercial use before launch.
+- Provider result URLs must not be shown to end users. Import bytes via a verified allowlisted origin, bound and validate content/FFprobe, register media_assets with tenant rights in existing private bucket, and expose only existing short-lived signed private download.
+- FFmpeg still handles the baseline free/included path, sound/overlays and any approved fallback. **Never silently switch from failed Wan to another paid model** or automatically charge again; any provider substitution needs a new price/consent check.
+- Alibaba Model Studio is official primary. Third-party API resellers (e.g. Runway, https://dev.runwayml.com/learn/wan-3-0-api) claim hosted Wan 3.0 access; independent account pricing, rights, data location, contractual status, and API compatibility are NOT verified and are not approved.
+
+## Approval gates for future live use
+
+1. Formal provider/model/version/region and commercial terms review; ensure purchased plan permits customer commercial outputs and external user media, including consent and data residency.
+2. Verified server-only credentials stored in RetailGrowthAI-specific secret store, immutable per-model pricing/FX snapshots, nonzero owner-approved budget ceiling and alerts.
+3. Reviewed additive Supabase migration + RLS/tenant denial/atomic reservation+refund tests; idempotent status transitions, safe cancel semantics and reconcilable UNKNOWN states.
+4. Configured and approved *existing* Azure worker/queue/outbox or separately approved queue provisioning, bounded retries and concurrency, safe importer and private downloads.
+5. 4/4 existing CI + additional P3 tests, security review, and a **separately owner-approved** single controlled paid DEV test; no automatic customer charges.
+6. Part 3 final PR reviewed by Coordinator only; do not merge Part 3 directly to main.
+
+## Implementation handoff snapshot
+
+Integration branch: `feat/part3-integration`, internal #109 gated Wan2.7 adapter, #113 zero-default quota/job schema + worker scaffolding, #115 free-first standalone UI. These feature PRs target the integration branch. The current frontend chooser is deliberately **not mounted** in the shared Part 1 dashboard. Premium HTTP routes, queue/outbox wiring, DB RPCs, secure provider-output importer, hosted SQL application, cancellation and live video tests are **unfinished**. Source code is not proof of live Wan generation.
+
+## LATEST Part 3 progress addendum — 2026-10-23
+- The prior handoff snapshot is historical. Dedicated branches for provider (#109), zero-default job/credit scaffolding (#113), disabled chooser (#115), and private output importer (#122) all merged into **feat/part3-integration** after verified six-job mock CI. Importer is code only: no registered live queue worker. The chooser is now mounted disabled, with FFmpeg still default.
+- The original proposed premium SQL was moved outside runnable migration history, pending Coordinator-approved new migration/ledger/security tests. Default quota remains zero. Vendor output CDN hostname compatibility requires checking the official `dashscope-a717.oss-accelerate.aliyuncs.com` example; follow-up PR #126 is under CI/review and should not be claimed merged until confirmed.
+- No paid Wan API request, external media transfer, plan payment or production activation took place.
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -368,3 +368,25 @@ See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by
 ## 2026-10-23 — Quota-enabled hosted E2E fully green
 - [Run #39958569041, attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39958569041) SUCCESS: two disposable Auth users and shops got auto-created seven-day trials; one campaign and one render quota unit were reserved. Real Foundry seven-day DRAFT, cross-tenant denial, persisted reviewed PATCH, successful FFmpeg H264 30-second 1080x1920 MP4, private signed download and fixture cleanup all PASSED in one run. Read-only DB afterward: zero temporary users, shops or reservations.
 - [Read-only queue audit #39950554363, attempt 3](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39950554363) SUCCESS: 11 Functions indexed, planning/render/recovery enabled, HTTP401 protected API and all four queue depths zero. Part 1 content + DEV trial/quota path fully verified; paid checkout/pricing/renewals NOT implemented.
+
+## 2026-10-23 — Part 3 independent development checkpoint (integration branch ONLY)
+- Part 3 dedicated `feat/part3-integration` branched from verified main `1ef7271004666c13a13cf627ed47460397799edc`; subsequent Part 1 main changes continue independently and must be rebased/reviewed by final coordinator.
+- Internally reviewed and merged **provider PR #109**, **premium UI PR #115**, **premium job scaffolding PR #113**, and **secure private importer PR #122** into Part 3 integration (none into main); each passed separate two-job Part 3 mock CI and existing four-job Part 1 CI at its exact tested PR head.
+- Provider code implements opt-in/gated Wan 2.7 async text/image-to-video requests, cost ceiling, private tenant image URL checks and safe polling; source-only premium SQL is **staged under azure-functions/campaign-api/part3_sql**, not applied to existing 11 hosted migrations. It extends the existing quota ledger and defaults to ZERO premium allocation, not a second billing system.
+- Premium UI is mounted on the Part 3 integration branch beneath the existing FFmpeg render controls with activation flags omitted/false; Part 1 FFmpeg remains the usable default. Importer has strict CDN allowlist, no redirects, bounded MP4 bytes/codec checking, existing private storage and lease-fenced completion interface.
+- **NOT live/complete:** no approved provider account/key/paid call, no actual premium clip, no final premium HTTP routes, transactional outbox/Azure queue registration, worker/poller/inbound provider byte import wired into production, or hosted premium migration. Real credit concurrency negative DB tests and usage reconciliation, cancellation/provider substitution, customer terms and billing approval remain. Keep premium DISABLED, no new cloud resources; no WineShopPOS/GenAI Galaxy or Part 2 changes.
+- Official docs, cost/rights and approval gates: `docs/part3/PROVIDERS_AND_COSTS.md`, `docs/part3/IMPLEMENTATION_AND_GATES.md`. Existing Part1 genuine hosted E2E and quotas are unaffected by source-only work.
+
+## 2026-10-24 — Part 3 Lead source milestones #188 and #189 (NOT hosted)
+- Two new Part3-only internal PRs passed exact 2/2 dedicated and 4/4 existing GitHub CI and were independently merged into `feat/part3-integration`: [#188](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/188) `7f31f0ba` (trusted private provider poll/OSS link expiry and lease-fenced mock output importer) and [#189](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/189) `0680b887` (separately licensed 30s FFmpeg concatenation of imported Wan clips, no change to default free rendering). CI: #188 [P3 40027754515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40027754515), [existing 40027754811](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40027754811); #189 [P3 40028636020](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40028636020), [existing 40028635956](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40028635956).
+- Source only: no Azure premium trigger, hosted P3 DB migration/claim RPC, provider account/API task, premium video MP4, new bill, licensed music purchase or real composition E2E. Full delivery remains blocked by credit/schema reconciliation, durable queues/HTTP API, signed private delivery, actual vendor/region rights/pricing and approved spend/test. The final Coordinator PR [#125](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/125) remains DRAFT. Details: `docs/part3/QUALIFICATION.md`, `docs/part3/POLL_COMPLETION_HANDOFF.md`, `docs/part3/FFMPEG_ASSEMBLY_HANDOFF.md`.
+
+## 2026-10-24 — Part 3 Chat 2 source continuation #193–#196 (INTEGRATION BRANCH ONLY)
+- Part3 lead independently reviewed and merged [#193](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/193) `e0bda65` (real **synthetic** offline 30s 720p H264/AAC FFmpeg composition with two distinct clip frames and self-generated audio), [#194](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/194) `4e8a830` (disabled authenticated premium HTTP create/status/sign-download boundary), [#195](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/195) `18b5794` (strict **APPROVED** campaign-day paid-job gate in Python + unapplied SQL), and [#196](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/196) `62fb30b` (disabled distinct UUID-only premium Azure queue + CAS outbox/poison/recovery protocol). Each PR passed exact dedicated Part3 2/2 and existing 4/4 CI before internal merge. Full run refs in `docs/part3/QUALIFICATION.md`.
+- No actual Wan MP4, paid provider request, cloud provisioning, hosted premium migration, registered premium Azure Function, retailer credit allocation or customer bill. The new HTTP/queue source is NOT wired to existing deployed Function App; all premium flags remain OFF, standard FFmpeg render remains primary. Owner must approve eventual hosted schema, service wiring, commercial workspace and bounded live smoke separately. Final Coordinator PR [#125](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/125) stays DRAFT; Part 1 and Part 2 unaffected.
+
+## 2026-10-24 — Part 3 security PR #198
+- Part3 Lead self-merged [#198](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/198) at `62100f0` after its dedicated [#40031597546](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597546) 2/2 and standard [#40031597516](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597516) 4/4 success. It enforces exact tenant-job-lease MP4 output receipts and local-only ffprobe for imported Wan media. No cloud/provider/SQL migration activation or Part1/Part2 changes. Prior combined integration HEAD `f88138fe` passed 6/6 after standard CI run #40030842790 attempt 2 (initial disposable Postgres port conflict). Final Coordinator PR #125 remains DRAFT.
+
+## 2026-10-24 — Part 3 queued-only cancellation guard merged (not activated)
+- [Internal PR #226](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/226) merged **only** into `feat/part3-integration` as `bccd6e0` after [Part 3 CI #40076805919](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805919) **2/2** and [standard CI #40076805911](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805911) **4/4**. Backend source-only `PremiumCancelBoundary` checks active JWT shop write membership, exact job identity, QUEUED and absence of provider submission/lease before asking a still-unimplemented atomic cancel/refund DB RPC. It refuses UNKNOWN/SUBMITTING and incomplete proof. No Azure registration, premium migration, hosted test, Wan call or customer charge. FFmpeg default unchanged; final PR #125 remains DRAFT.
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -149,3 +149,18 @@ Use scripts/checkpoint.sh after completing a task.
 - 2026-10-23: Continued #102 atomic subscriptions from prior interrupted CI. Fixed local negative test fixture to distinguish authenticated JWT from service DB setup instead of suppressing failing security tests; confirmed CI 4/4 and merged. Added disposable SQL negative tests: automatic 7-day trial, browser cannot self-upgrade or forge ledger, foreign tenant cannot read entitlement/meter, third campaign and render denied by SQLSTATE RG002 without spending an extra unit, expired plan SQLSTATE RG001, wrong actor denied. Supabase `apply_migration` SUCCESS to dedicated `jeearzffnjbvghwjjjrf` (only new 11th migration version 20261023134701, original 10 untouched; no existing shop/auth rows). Read-only RLS audit found OWNER-only SELECT and 3 triggers. #103 aligned exact history version and added protected one-shot Azure backend release, CI 4/4 merged; [#39965140549](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39965140549) SUCCESS same existing app 11 indexed / API 401, no provisioning. #104 Account read-only owner plan + friendly API 402/429, offline security/client + Playwright mock fixture regression fixed, PR 4/4 and merged; SWA #39965683074 SUCCESS at https://purple-dune-06b5da200.2.azurestaticapps.net, routes /, /campaigns and /account HTTPS checks PASSED. Independently verified hosted DB ephemeral SQL tests left no quota fixtures. No paid plan charging, Parts 2/3, WineShopPOS or GenAI Galaxy changes.
 
 - 2026-10-23 14:16 UTC: Resumed interrupted post-subscription hosted E2E [#39958569041 attempt 2](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39958569041); GitHub job SUCCESS. Logs: campaign accepted, foreign tenant denied, real seven-day DRAFT, draft PATCH saved, render created and SUCCEEDED, signed 30-second 1080x1920 H264 ffprobe passed, fixture cleanup PASS, overall PASSED. Supabase read-only checked auto-trial on two temporary shops and exactly one campaign/render reservation; post-run zero synthetic Auth users, shops and reservations. Read-only Azure audit [#39950554363 attempt 3](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/39950554363) SUCCESS: all 11 indexed, protected API 401, 4 queues empty. Main CI #39966947050 4/4. No resources added, prior migrations reapplied, Part 2/3 or other projects touched. Remaining availability 503 tuning and separately approved billing.
+
+- 2026-10-23 Part 3 Lead: Connected repo, read AGENTS/canonical docs and verified live Part1 Foundry/FFmpeg/private media and trial quota architecture. Created dedicated `feat/part3-integration` from verified main 1ef72710 and independent p3 feature branches. Reviewed and squash-merged #109 (Wan 2.7 async T2V/I2V prompt provider) and #115 (disabled, free-first premium selection), #113 (tenant-authenticated premium jobs and zero-default SQL proposal staged outside immutable Supabase migration history), #122 (signed provider output private importer + no-redirect/MP4 validation). Each exact PR head passed separate two-job Part3 and existing four-job Part1 GitHub CI; no checks bypassed. During #113 tests, corrected missing isolated dependency stub and unreviewed migration whitelist issue without weakening security.
+- 2026-10-23 Part 3 Lead: Added separate offline-only Part 3 CI and configured full existing PR checks for Part 3 integration target, plus `docs/part3` vendor/rights/cost and activation gate notes. Mounted premium UI on Part 3 branch with all activation flags absent/false; standard FFmpeg path unchanged. No cloud resource/migration deployment, billable generation, subscription charge, real premium private media or main integration. Remaining premium outbox/real worker/DB RPCs, endpoint, approved paid provider, complete provider substitution, cancellation and live tests are explicitly incomplete; final Coordinator owns main.
+
+- 2026-10-24 Part 3 Lead: Resumed from exact `feat/part3-integration`; reviewed latest main/canonical docs, Part1 FFmpeg/API, offline Wan provider/importer, actual Alibaba async result schema. Built `feat/p3-private-poll-completion` and reviewed/merged [PR #188](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/188) as `7f31f0ba` after dedicated Actions #40027754515 2/2 and existing #40027754811 4/4. Added private-only provider poll, DB-claim-gated import bridge, expiry/SSRF/tenancy/status mocks, docs/part3/POLL_COMPLETION_HANDOFF.md. No provider calls, hosted DB or Azure execution.
+- 2026-10-24 Part 3 Lead: Built independent `feat/p3-ffmpeg-ai-assembly`; fixed a real failing FFmpeg test-harness assertion from Actions #40028201422, hardened source probe and audio preflight, then reviewed/merged [PR #189](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/189) as `0680b887`. Exact final CI #40028636020 dedicated 2/2 and #40028635956 existing 4/4 PASS. Pure optional assembly still requires real 30s composition test, provider clip, worker and billing. All premium flags OFF. No main merge, WineShopPOS, GenAI Galaxy or Part 2 mutations.
+
+- 2026-10-24 Part 3 Lead: Resumed interrupted integration; verified previous exact branch HEAD #188/#189 6/6 and main divergence; created/QA-reviewed/merged [PR #193](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/193) `e0bda65` after P3 CI #40029556625 2/2, standard #40029556607 4/4: real FFmpeg generated 15s red+15s blue + self-owned WAV tone, ffprobe 30s H264/AAC, frame order verified, all temp synthetic media deleted. No Wan/vendor/cost.
+- 2026-10-24 Part 3 Lead: Merged [#194](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/194) `4e8a830` after P3 #40029862503 2/2 + standard #40029862536 4/4: disabled JWT premium create/status/download module, RLS membership and immutable private output path security, no Azure route registered. Added tests and `docs/part3/PREMIUM_HTTP_HANDOFF.md`.
+- 2026-10-24 Part 3 Lead: Merged [#195](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/195) `18b5794` after P3 #40030136015 2/2 + standard #40030136005 4/4: fixed source-only premium gate wrongly accepting non-rejected DRAFT; Python and staged not-applied SQL now require exact `APPROVED`, negative tests and approval-workflow limitation noted.
+- 2026-10-24 Part 3 Lead: Merged [#196](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/196) `62fb30b` after P3 #40030452145 2/2 + standard #40030452191 4/4: additive default-disabled distinct premium Azure UUID queue, mock CAS outbox/poison/recovery client source and fail-closed tests; no queues, live RPC, triggers or providers activated. Updated canonical docs, retained DRAFT Coordinator PR #125 and no Part1/Part2/WineShopPOS/GenAI-Galaxy mutation.
+
+- 2026-10-24 Part 3 Lead: Verified combined head `f88138fe` full Part3 2/2 and base 4/4 CI after rerunning transient runner port-54322 Supabase failure (run #40030842790 attempt 2). Scoped extra private-import audit found lax `startswith` storage receipt matching and missing ffprobe local-only protocol. Opened, tested, reviewed and self-merged [#198](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/198) `62100f0` following [P3 40031597546](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597546) 2/2 plus [standard 40031597516](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597516) 4/4. Added six exact-receipt denial cases and ffprobe protocol-whitelist assertion. No Wan task, hosted cloud/schema, customer charge, direct main merge or WineShopPOS/GenAI-Galaxy mutation.
+
+- 2026-10-24: Verified newer concurrent Part 3 internal work already merged PR #109 and many subsequent workstreams; closed accidental duplicate #222 without merging to protect established provider implementation. Added `premium_cancel.py`, mocked tenant/QUEUED/CAS/UNKNOWN/no-refund tests and a scoped handoff in dedicated `feat/p3-safe-cancel-contract`, PR [#226](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/226). Actual dedicated [#40076805919](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805919) 2/2 PASS and [#40076805911](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805911) 4/4 PASS; squash-merged to `feat/part3-integration` at `bccd6e0`. This is fail-closed source-only code, **not** a live DB cancel/refund RPC, HTTP endpoint, provider charge or deployment. No main, Part 1/2, WineShopPOS or GenAI Galaxy changes.
~~~~

### docs/part3/APPROVED_CONTENT_GATE.md
~~~~diff
@@ -0,0 +1,9 @@
+# Part 3: explicit human approval gate for paid provider calls
+
+A campaign created by Part1 Foundry is `status=DRAFT` and its generated `campaign_days.review_status` is initially `DRAFT`. Previously the source-only Part3 coordinator and prospective SQL reservation denied only `REJECTED`, which could permit a DRAFT day to be submitted to an external paid provider if premium were activated.
+
+**Security fix**: the Part3 coordinator now requires `review_status == 'APPROVED'` for the selected day, and the review-only, NOT APPLIED Part3 SQL reservation trigger uses the exact same predicate. Neither `DRAFT`, `REJECTED` nor missing status can reserve a provider job or transfer business content. The request still requires authenticated OWNER/EDITOR and documented commercial rights.
+
+The current Part1 API may not yet provide an explicit authorized `DRAFT -> APPROVED` campaign-day transition. Do not weaken this gate to force testing. Owner/coordinator must define an authenticated, tenant-scoped, version-pinned human approval workflow and its edit-revocation semantics before premium activation. This source change does not promote the pending SQL migration, and no paid API, cloud, live DB, shared Part1 code or Part2 code was touched.
+
+Regression tests in `tests/api/test_premium_video_jobs.py` exercise all negative review states and verify the check runs before any media/credit reserve. Run existing 4/4 plus Part3 dedicated 2/2 CI before Part3 internal merge.
~~~~

### docs/part3/DURABLE_QUEUE_HANDOFF.md
~~~~diff
@@ -0,0 +1,20 @@
+# Part 3 durable premium outbox / Azure UUID queue scaffold (OFF)
+
+Branch `feat/p3-durable-queue-scaffold` targets `feat/part3-integration`, NOT main.
+
+## Additive source implementation
+
+- `premium_queue.AzurePremiumQueue` mirrors the existing Part1 Azure Storage Queue client but targets a **distinct proposed** `retail-premium-video` queue. It emits only canonical 36-character job UUIDs; no prompt, token, tenant data, signed URL, media or cost. It does NOT call `create_queue`, provision the queue or use a paid API.
+- `premium_outbox.dispatch_premium_outbox` expects an **atomic, database-claimed** premium outbox event with `id, lease_token, kind='premium_video', job_id`, sends only the UUID and confirms with CAS. On ambiguous Queue send, it marks the claimed event as unconfirmed; an eventual resend is safe ONLY if the yet-to-be-implemented DB claim worker enforces at-most-one billable provider POST even on replay.
+- `record_premium_poison` records an SHA-256 fingerprint + optional canonical job UUID, never arbitrary message contents or job status. It requires durable DB receipt before queue ACK.
+- `reconcile_premium_and_dispatch` invokes the future SQL reconciler first. **Never** reset UNKNOWN/SUBMITTING to QUEUED or send a second paid provider request without a verified provider reconciliation.
+- Every dispatcher and poison action is `enabled=False` by default and raises before touching external dependencies.
+
+## Essential missing integration before deployment
+
+1. A separately owner-approved new Supabase migration must provide atomic `claim_premium_outbox`, `confirm_premium_outbox`, `record_premium_poison` and `reconcile_premium` service-role RPCs (names are contracts/proposals only), database-backed idempotency, rights/credit evidence, TTL leases and bounded retries, plus correct RLS and negative concurrency tests.
+2. Azure infrastructure must be explicitly approved to create the distinct premium queue + poison queue, and the owner must authorize deployment of the new **DISABLED** premium timer/queue/poison triggers.
+3. The consuming premium worker must claim the actual SQL job/attempt before calling provider. All replays, poison and ambiguous vendor POSTs must be fenced and stop at UNKNOWN rather than creating another charged task.
+4. No live queue, timer, Python Function registration, database changes, WAN request, hosted E2E or premium credits are made by this workstream.
+
+CI: `tests/reliability/test_premium_outbox.py` tests UUID-only payload, malformed claims, disabled default, CAS confirmation, ambiguous queue ACK, durable poison receipts and reconciliation sequencing. Require 4/4 existing CI plus 2/2 Part3 dedicated CI before merging internally.
~~~~

### docs/part3/FFMPEG_ASSEMBLY_HANDOFF.md
~~~~diff
@@ -0,0 +1,23 @@
+# Part 3: Optional AI clip -> 30-second FFmpeg assembly (source only)
+
+Branch `feat/p3-ffmpeg-ai-assembly`, targeting `feat/part3-integration`.
+
+## Delivered source boundary
+- `video-engine/premium_compose.py` is an **additive** 30-second MP4 assembler; existing default `video-engine/render.py` and Part 1 free FFmpeg rendering remain unchanged. `select_render_mode` defaults to `ffmpeg` unless a separate authorized + enabled + all-clips-ready premium decision is explicitly provided.
+- Accepts **only tenant-scoped private and independently reviewed provider output receipts**, not browser URLs or user input paths; 2–8 clips, each 2–15 seconds, exact total 30 seconds.
+- Requires recorded commercial-use evidence and server-managed paths; re-probes imported MP4 H.264 codec, duration, portrait dimensions and bounded bytes before encoding. Audio sources require separately licensed rights evidence. Uses silent AAC if no music, never bundles unlicensed stock audio.
+- Uses the existing FFmpeg/ffprobe toolchain and `verify_reel` contract. One H.264 yuv420p video + AAC audio output at 30 seconds. Uses a no-shell bounded FFmpeg process with safe error text and a temporary output before success atomic move.
+- Supports only clip stitching/hard cuts (no branded overlay or dissolve yet); premium 30-second user workflow is **not live**. This source is not called by any registered Azure API/worker and cannot charge a provider. Paid Wan API remains OFF.
+
+## Preconditions before activating
+- All `clip receipts` must be fetched from the existing service-role/tenant-scoped authorized store by job ID; never trust a client-provided manifest.
+- Provider result URLs must first be imported through `premium_private_import`, and clip provenance/billing/tenant/rights must be verified server-side.
+- Reserve a strict total premium spend budget and concurrency before any paid provider task. A 30-second composition may require multiple billable 15s clips; do not bill the customer twice for fallback or duplicate renders.
+- A failed/absent premium clip must not silently incur another paid provider POST. UI should explicitly offer the already-working standard FFmpeg renderer as the default fallback. Do not automatically refund a task that may have been charged.
+- Branded overlays, CTA, text claim approval, optional fade transitions and mixed stock/AI timelines need review before launch; the minimal pure AI assembly does not implement those capabilities.
+- Production output still requires authenticated private upload, DB CAS finalization, signed tenant-only download, exact per-shop usage and hosted FFmpeg benchmark.
+
+## Mocked/offline testing
+`tests/media/test_premium_clip_compose.py` checks FFmpeg command generation with mocks, free-first selection, cross-tenant/rights/path/duration/codec denial, safe default silence and licensed audio. Real full-resolution output/video quality and hosted tests are **not claimed**. Existing Part 1 FFmpeg CI remains the original quality gate.
+
+No WAN API calls, paid clouds, schema changes, releases, Part 2 or unrelated repositories affected.
~~~~

### docs/part3/IMPLEMENTATION_AND_GATES.md
~~~~diff
@@ -0,0 +1,46 @@
+# Part 3 — Internal development and activation gates (2026-10-23)
+
+## Branch ownership and internal PRs
+- Independent integration: `feat/part3-integration` → **final coordinator PR to main only after tests**.
+- Provider / T2V / I2V / prompt: `feat/p3-wan-provider`, PR #109, owns `ai-agents/src/ai_agents/premium_video.py` and provider tests.
+- Durable jobs + credit ledger: `feat/p3-premium-jobs`, PR #113, owns `azure-functions/campaign-api/premium_video_jobs.py`, STAGED un-applied SQL proposal at azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql and tests.
+- Premium UI: `feat/p3-premium-ui`, PR #115, owns new `frontend/src/features/premium-video/**` and mocked Node tests.
+- Two-job isolated PR workflow and existing four-job repository CI must pass all internal PRs; do not merge failing code. Final integration adds files without touching Part 2 OAuth or Part 1 production deployment.
+
+## Current implemented / staged boundaries
+- **Default free FFmpeg**: existing `instagram_reel_30s` API and worker remain unchanged.
+- Alibaba WAN 2.7 opt-in Python adapter: async submit/poll and bounded prompt, strict workspace endpoint and signed tenant-private source URL format, per-job maximum USD budget, default off. It does NOT send any vendor calls without explicit on/off flag, valid API key, workspace and nonzero cap.
+- Source-only premium table includes job identity, tenant, provider task ID, safe statuses, encrypted/private separation and idempotency key; source migration extends **existing** `shop_subscriptions` and `shop_usage_reservations` by operation/premium seconds. Premium allowance defaults 0, so no trial/customer receives premium access. Row lock + shared ledger prevents concurrent over-reservation. These are not additional card/billing services.
+- Authenticated job controller scaffold requires reviewed DRAFT and OWNER/EDITOR role, user JWT/RLS asset check + service-side media rights, deterministic request idempotency and safe job response. Mock worker records UNKNOWN on uncertain submission, never sends an unbounded duplicate POST.
+- Frontend component defaults to FFmpeg; selectable Wan state requires all THREE server entitlement, enabled feature, and ready authenticated endpoint. Component currently intentionally not mounted in shared CampaignDashboard to preserve Part 1 behavior.
+
+## Incomplete before provider activation
+1. Review source schema, reconcile the older locked migration manifest, promote the proposal to a NEW timestamped migration, and **authorize/apply it separately** to DEV (never replay Part 1's 11 versions); require disposable negative SQL and real concurrency/tenant tests.
+2. Wire a new **transactional premium outbox** and queue trigger into existing Azure Functions/Storage config; use UUID-only messages, CAS leases and poison/recovery behavior. Do not overload Part 1's free render queue.
+3. Ensure credentials, workspace region, cost limits, customer consent and provider terms reviewed and approved; add a per-tenant monthly spend ceiling and provider call concurrency limit. Do not enable the feature just by deploying source.
+4. Implement server-side encrypted provider task persistence/lease token fencing, bounded poller, cancel semantics (local cancellation does not imply refunded provider usage) and billing reconciliation on UNKNOWN.
+5. Implement safe provider output importer with allowlisted redirect destinations, time/byte limits and MP4 ffprobe; upload to existing `retailgrowth-media` bucket under validated tenant-scoped private path with signed RetailGrowthAI-only download URL. Current poller intentionally **does not** pass through vendor result URL or mark completion until import.
+6. Wire explicit authenticated premium API routes/status, user-reviewed brand claims and frontend selection; submit API must reject missing approved credit quote, expired JWT, foreign/VIEWER, unsupported images, unreviewed claims, expired subscription.
+7. Run full offline pytest/Node/SQL/FFmpeg + hosted DEV canary with approved isolated test identity/provider spending; measure real $/clip and retry/failed spend; then decide production activation. **No billable tests without specific owner approval.**
+8. No social publishing side effects (Part 2 owns OAuth/schedulers), no changes to WineShopPOS or GenAI Galaxy, no duplicate payment system.
+
+## Current operational default
+`RETAIL_PREMIUM_VIDEO_ENABLED=false`; `RETAIL_WAN_APPROVED_PER_JOB_USD=0`; no model key, paid-provider request, SaaS bill or new resource. Do not deploy the unreviewed Part 3 migration or mount and expose an enabled premium control.
+
+## Integration record (2026-10-23)
+- Provider PR #109 merged into feat/part3-integration after 2/2 Part 3 and 4/4 existing CI jobs passed.
+- Free-first premium UI PR #115 merged after 2/2 Part 3 and 4/4 existing CI jobs passed.
+- Atomic premium job scaffold PR #113 merged after 2/2 Part 3 and 4/4 existing CI jobs passed. Initial CI failures from cross-branch provider test import and canonical migration whitelist were fixed without weakening either security test: provider contract mock is isolated, SQL proposal is OUTSIDE automatically applied supabase/migrations. No hosted migration executed.
+- Private importer PR #122 **merged** into feat/part3-integration after 2/2 dedicated Part 3 and 4/4 existing Part 1 CI checks passed. No Azure premium trigger registered; premium remains disabled.
+
+## Final Coordinator interface-review boundary
+- The additive premium React panel was mounted on `feat/part3-integration` after the standard FFmpeg RenderStatus. All entitlement/endpoint/enablement props default to false; this is a **disabled informational option**, never a paid request. Final Coordinator must approve shared `CampaignDashboard.jsx` placement and `.github/workflows/frontend-bootstrap.yml` branch target change before main integration.
+- Current work has **no registered premium job REST or Azure queue route**. Staged SQL is **not** in `supabase/migrations` and therefore is not an executable/migrated feature. Do not interpret green mock CI as production or hosted premium video.
+- Main advanced independently during Part 3 work. Final Coordinator must rebase carefully and rerun all existing CI after resolving any merge conflict, retaining later Part 1 subscription/navigation updates and all Part 2 files.
+
+## 2026-10-24 — Latest additive internal milestones (supersedes older pending notes)
+- [#193](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/193): real local synthetic 30s FFmpeg/H264/AAC smoke; not vendor output.
+- [#194](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/194): source-only disabled JWT HTTP premium create/status/private download; not an Azure route.
+- [#195](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/195): exact APPROVED review gate prevents paid transfer of Part1 default DRAFT campaign days; staged SQL not applied, safe approval endpoint pending.
+- [#196](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/196): isolated, source-only premium Azure queue + CAS outbox/poison design, not provisioned nor active.
+- All four internal PRs passed dedicated P3 2/2 and standard 4/4 CI before merge, see `docs/part3/QUALIFICATION.md`. The real data-plane/service-role claims, migrations, worker/HTTP registration and cloud/paid hosted E2E still have NOT happened; premium costs remain ZERO unless the owner explicitly authorizes future activation.
~~~~

### docs/part3/MEDIA_FENCE_HARDENING.md
~~~~diff
@@ -0,0 +1,12 @@
+# Part 3 private output and probe hardening (source only)
+
+Internal branch: `feat/p3-media-fence-hardening` -> `feat/part3-integration`.
+
+The existing premium output importer already restricts Alibaba signed video origins, disables HTTP redirects, bounds download size, validates MP4 bytes and applies lease-fenced DB completion. This change strengthens two additional checks:
+
+1. **Exact lease-scoped storage receipt**: after calling the existing `PrivateMedia.upload`, importer now requires the returned object path to equal `{shop_uuid}/renders/{job_uuid}/{lease_uuid}.mp4` precisely. A malicious or faulty storage adapter cannot substitute the same prefix with a suffix, additional path segment, different job or an altered extension and then mark the job complete.
+2. **Local-only media probe**: `probe_mp4` invokes ffprobe with `-protocol_whitelist file` to prevent crafted provider MP4 references from causing network fetches via unexpected protocols. Media input still comes only from the bounded verified local download.
+
+Regression coverage in `tests/reliability/test_premium_private_import.py` denies six receipt-faking variants before the database completion callback and asserts the local-only ffprobe invocation.
+
+These are backend source/offline test changes only. No approved or paid Wan workspace, Azure deployment, Supabase hosted migration, queue provisioning or customer charge. Actual premium service integration remains disabled until formal DB/worker/security/rights/cost approvals.
~~~~

### docs/part3/POLL_COMPLETION_HANDOFF.md
~~~~diff
@@ -0,0 +1,28 @@
+# Part 3: Internal Wan poll -> private clip completion (source only)
+
+Implementation workstream: `feat/p3-private-poll-completion`, targeting `feat/part3-integration`.
+
+## Scope and external evidence
+- Alibaba Model Studio WAN 2.7 official async task query: GET workspace `/api/v1/tasks/{task_id}`, task statuses PENDING/RUNNING/SUCCEEDED/FAILED/CANCELED/UNKNOWN, `output.video_url` on success, 24-hour task/media expiry.
+- Official vendor guides: https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference and https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference.
+- The existing public `AlibabaWanProvider.poll()` **still returns only safe status**. The new `poll_private()` is strictly server/internal and includes the expiring URL ONLY on SUCCEEDED.
+- `PremiumPollCompletion.run_once(job_id)` accepts only a canonical UUID, checks a backend-claimed IMPORTING lease, verified premium reservation and tenant identity, reads the vendor output once, validates signed OSS hostname/expiry, downloads without redirects, validates MP4/H.264/duration, uploads privately and calls fenced store finalization.
+- Any ambiguous provider task (UNKNOWN/CANCELED/FAILED) is **RECONCILE**, not an automatic refund or another billable POST. Expired URLs, forged tenant leases and missing reservation cannot import. Nothing returns signed vendor URLs in the public result.
+- `premium_private_import.validate_vendor_video_url` now requires exactly one future `Expires` epoch with >=30 seconds remaining, rejecting expired or duplicate values before network access.
+- The backend and provider both remain **disabled by default**. This module has no registered Azure Function, deployed code path, Supabase migration, actual provider task or media.
+
+## Required runtime/service-role contracts BEFORE wiring
+- `store.claim_import(job_id)`: one atomic privileged DB claim for this canonical job UUID; return `None` for unclaimed/foreign/expired job; otherwise DB-authored `{id, shop_id, attempt_token, provider_task_id, status: IMPORTING, reservation_confirmed: true, seconds}`. Verify the premium reservation in the existing Part 1 usage ledger, a current lease and original tenant. Never let HTTP or Azure Queue payload supply these fields.
+- `store.finalize(job_id, shop_id, attempt_token, private_path)`: CAS checks the **same** live claim and tenant, creates/links one tenant-private `media_assets` record in existing `retailgrowth-media`, records billing outcome from actual vendor usage and marks SUCCEEDED atomically. The fake test implementation only proves the expected interface.
+- `media.upload`: must implement tenant-scoped existing private bucket storage, no overwrite, bounded file, and a well-defined stale-lease/orphan cleanup strategy. Post-upload DB failure may leave an object: reconcile rather than blindly repeat.
+- Add a durable Azure poll timer/UUID queue, enforced per-shop spend and provider concurrency, poison and failure reconciliation, secure signed RetailGrowthAI downloads, and operator audit. Do not put provider URL, prompt, token or key into queue, logs or frontend.
+- For a real provider task `poll_private` performs one outbound **nonbillable** status GET, but it is nevertheless gated by an owner-approved API key and enabled flag. Do not activate or run billable tasks without explicit approval.
+
+## Offline tests
+- `ai-agents/tests/test_premium_video.py`: worker-private vs safe public response and disabled gate.
+- `tests/reliability/test_premium_poll_completion.py`: safe import, lease/tenant/usage denials, provider status reconciliation, expired/forged/duplicate signed URL denials, failed DB CAS, no secret leakage.
+- `tests/reliability/test_premium_private_import.py`: bounded download, codec/bytes validation and private finalization.
+- Both existing four-job CI and dedicated Part 3 CI are required for a merge. Green mock tests do not authorize a live release.
+
+## Follow-up/ownership
+The still-unfinished Part 3 work is schema/RPC review, durable outbox, registered Azure polling/import worker, live API/frontend authentication/credit UI, premium multi-clip 30-second FFmpeg composition, cost/rights review and separately approved hosted DEV smoke. Coordinator only reviews/merges the final `feat/part3-integration` -> `main` PR.
~~~~

### docs/part3/PREMIUM_HTTP_HANDOFF.md
~~~~diff
@@ -0,0 +1,24 @@
+# Part 3: Additive, disabled premium HTTP boundary (source only)
+
+Branch: `feat/p3-premium-http-gate` targeting `feat/part3-integration` (self-merged by Part3 Lead after all tests).
+
+## New source contract
+`azure-functions/campaign-api/premium_http.py` provides `PremiumHTTPBoundary` with a verified user JWT at every request:
+- `POST /campaigns/{campaign_id}/premium-videos`: forwards a strictly canonical campaign ID and payload to the existing premium coordinator; does **not** publish any Azure queue payload or charge a provider.
+- `GET /premium-video-jobs/{job_id}`: returns only coordinator-safe status without provider task IDs or signed output URLs.
+- `GET /premium-video-jobs/{job_id}/download`: only after RLS-scoped job fetch, CURRENT shop membership, SUCCEEDED status, exact output asset ID/shop/bucket/MIME, immutable `{shop_id}/renders/{job_id}/{lease_uuid}.mp4` receipt and the existing user-JWT `TenantStore.sign_download` 60-second private Storage signer.
+
+The entire boundary has `enabled=False` by default; even a verified user cannot access it without the separately approved backend gate. Requests are never enabled from request parameters or browser flags. Unauthorized/foreign/expired/stale/wrong-status requests return restricted error codes, with no raw provider/storage errors.
+
+## Explicit limitations
+This is NOT mounted into the live `function_app.py` or `HTTPAPI`; no Azure API route exists until Coordinator-approved additive wiring. `PremiumVideoCoordinator` currently depends on unimplemented real P3 database reservation/claim RPCs, and staged SQL has NOT been applied to DEV. Neither the existing Part1 HTTP contract nor the standard FFmpeg render/upload/download flow changes.
+
+Before integration in Azure:
+- Finish exact new premium SQL schema, existing-ledger credits, atomic idempotency and tenant denial SQL tests; apply hosted migration ONLY after explicit approval.
+- Implement backend-only real premium repository and HTTP dependencies with bounded response/timeouts and RLS JWT validation.
+- Register new Azure Function routes only under locked premium backend activation; wire UUID-only transactional outbox + premium queue/recovery/poller/import and signed private output.
+- Verify real user auth, foreign tenant denial, positive owner entitlement and output delivery in DEV. Approve vendor spend separately.
+
+Tests: `tests/api/test_premium_http.py` validates disabled-by-default auth, create/status routing, read-only private tenant access, signed download shape, wrong status, forged object path and foreign/mismatched media denials. Existing four GitHub CI jobs cover this source-only test; 2/2 dedicated Part3 tests also required.
+
+No paid API calls, cloud deployment, schema modification, charges or cross-project files.
~~~~

### docs/part3/PROVIDERS_AND_COSTS.md
~~~~diff
@@ -0,0 +1,42 @@
+# Part 3 — Wan vendor research and cost baseline (2026-10-23)
+
+Verified with official Alibaba Cloud documentation. This is **research**, not approval to consume any paid provider API. Vendor plans/prices may change, including promotional prices and taxes.
+
+## Available official Alibaba Model Studio models
+- `wan2.7-t2v-2026-06-12`: text-to-video, 720P/1080P, 2–15 seconds, 30 fps MP4 (International/Singapore).
+- `wan2.7-i2v-2026-04-25`: first-frame / first-and-last-frame / video continuation, 720P/1080P, 2–15 seconds, 30 fps MP4. Source media must be licensed; for first-frame video its aspect ratio follows the source image, not a `ratio` parameter.
+- `wan3.0-video-prime`: newer 480P/720P/1080P multi-modal video up to 30 seconds. Pricing is higher; not implemented by the initial narrow 2.7 adapter.
+- `wan2.6-t2v`, `wan2.6-i2v`: legacy separately versioned endpoints; do not send new 2.7 payload to legacy format.
+
+## Official reference prices (Singapore, USD)
+| Model | 720P / second | 1080P / second | Notes |
+|---|---:|---:|---|
+| Alibaba Wan 2.7 T2V | $0.10 | $0.15 | 2–15s |
+| Alibaba Wan 2.7 I2V | $0.10 | $0.15 | 2–15s |
+| Alibaba Wan 3.0 Video Prime | $0.14 | $0.28 | up to 30s |
+| fal.ai Wan 2.6 I2V (third-party) | $0.10 | $0.15 | 5/10/15s; alternative provider only |
+
+At an *indicative* **₹94.94/USD** on 2026-10-23, Wan 2.7 for 5s 720P ≈ **₹47.47**, 10s 720P ≈ **₹94.94**, 15s 1080P ≈ **₹213.62**. A 30s campaign Reel requires composition of clips, e.g. two 15s 720P Wan 2.7 clips = $3.00 ≈ **₹284.82**, while two 15s at 1080P = $4.50 ≈ **₹427.23**. These exclude GST, foreign exchange spread, failed/retried tasks, premium FFmpeg assembly, hosting/storage/network and platform margin. Do not present them as a customer price or quote without real-time approved provider cost.
+
+## API and region
+- Use *workspace-specific Singapore* HTTPS `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com` with same-region API key. Region/model/key must match.
+- Call `POST /api/v1/services/aigc/video-generation/video-synthesis` with `X-DashScope-Async: enable`; poll `GET /api/v1/tasks/{task_id}` at bounded intervals (vendor suggests ~15 seconds).
+- Model creation usually takes 1–5 minutes. Task IDs and result video URLs are valid for **24 hours**, not a permanent customer media link. Never return provider URL directly to the browser; backend must privately import, verify codecs/bytes and save in existing private media storage.
+- WAN 2.7 T2V has explicit `ratio`; I2V uses first-frame aspect ratio. Watermark choice and AI disclosure must comply with platform/local policy.
+
+## Rights and provider approval
+- Alibaba Cloud paid Model Studio product terms say the provider does **not** claim IP ownership in output, but customer input/output use is subject to rules/laws, rights of third parties and output may lack exclusivity.
+- **Model Studio console *trial interactions* are explicitly restricted to evaluation and not commercial publication.** Never treat free console trial renders as licensed marketing assets.
+- Verify paid workspace entitlement, commercial terms and permitted data regions. Customer must own/authorize input photo, likeness/logo/music and consent to cross-provider transfer. Moderation can reject copyrighted/unsafe content. No automatic posting: human review.
+- Alternative fal.ai API has separate terms, media handling, pricing, model versions and credentials; provider substitution requires independent review and cannot silently inherit Alibaba approval.
+
+Sources:
+- https://www.alibabacloud.com/help/en/model-studio/video-generate-edit-model
+- https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
+- https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference
+- https://www.alibabacloud.com/help/en/model-studio/model-pricing
+- https://www.alibabacloud.com/help/en/model-studio/wan3-0-video-prime
+- https://www.alibabacloud.com/help/en/legal/latest/alibaba-cloud-international-website-product-terms-of-service-v-3-8-0
+- https://help.aliyun.com/en/model-studio/bailian-service-notes
+- https://fal.ai/models/wan/v2.6/image-to-video/api
+- https://indiagraphs.com/data/usd-inr-exchange-rate/average-usd-inr-rate-per-usd
~~~~

### docs/part3/QUALIFICATION.md
~~~~diff
@@ -0,0 +1,68 @@
+# Part 3 full integration source-qualification record — 2026-10-23
+
+**Branch:** `feat/part3-integration`; **final draft PR:** #125 into main — Coordinator only. This qualification file is a source-only integration CI trigger and records exact PR evidence. No hosted deployment.
+
+## Reviewed internal merges and CI evidence
+
+| Internal PR | Scope | Exact check runs | Result |
+|---|---|---|---|
+| #109 | WAN 2.7 provider, async T2V/I2V, prompt/limits | Dedicated #39975248007 2/2; existing #39975248169 4/4 | PASS, merged to Part3 |
+| #115 | FFmpeg-default premium chooser, no billing | Dedicated #39975257823 2/2; existing #39975257898 4/4 | PASS, merged to Part3 |
+| #113 | premium job scaffold, zero-default shared-ledger SQL proposal | Dedicated #39975690745 2/2; existing #39975690715 4/4 | PASS after fixing isolated provider mock and unreviewed-migration conflict, merged to Part3 |
+| #122 | no-redirect, bounded, verified private Wan MP4 output importer | Dedicated #39976479632 2/2; existing #39976479459 4/4 | PASS, merged to Part3 |
+| #126 | vendor official output OSS hostname compatibility fix/regression | Dedicated #39977762809 2/2; existing #39977763357 4/4 | PASS, merged to Part3 |
+| [#188](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/188) | worker-only Wan success URL, lease-fenced private completion + expiry guards | Dedicated [#40027754515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40027754515) 2/2; Part 1 [#40027754811](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40027754811) 4/4 | PASS, merged to Part3 as 7f31f0ba |
+| [#189](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/189) | offline optional 30-second licensed Wan clip FFmpeg composition, default-free fallback | Dedicated [#40028636020](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40028636020) 2/2; Part 1 [#40028635956](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40028635956) 4/4 | PASS, merged to Part3 as 0680b887 |
+| [#193](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/193) | REAL offline FFmpeg 30s synthetic composite: two independently encoded clips, licensed fixture audio, pixel verification | Dedicated [#40029556625](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029556625) 2/2; Part 1 [#40029556607](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029556607) 4/4 | PASS, merged as e0bda65 |
+| [#194](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/194) | disabled JWT premium create/status/private download HTTP adapter | Dedicated [#40029862503](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029862503) 2/2; Part 1 [#40029862536](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40029862536) 4/4 | PASS, merged as 4e8a830 |
+| [#195](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/195) | explicitly APPROVED day mandatory before premium credit reservation, Python + staged SQL | Dedicated [#40030136015](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030136015) 2/2; Part 1 [#40030136005](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030136005) 4/4 | PASS, merged as 18b5794 |
+| [#196](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/196) | disabled isolated premium UUID-only Azure queue, CAS outbox and poison source scaffold | Dedicated [#40030452145](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030452145) 2/2; Part 1 [#40030452191](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030452191) 4/4 | PASS, merged as 62fb30b |
+| [#198](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/198) | exact lease-private output receipt + ffprobe local-only protocol guard | Dedicated [#40031597546](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597546) 2/2; Part 1 [#40031597516](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40031597516) 4/4 | PASS, merged as 62100f0 |
+
+The twelve internal feature PRs merge only into `feat/part3-integration`; the final PR #125 is open as **DRAFT**, not merged into `main`.
+
+## Default-safe integrated behavior
+
+- Current Part 1 `RenderStatus` and FFmpeg 30s Reel remain unchanged. The new PremiumVideoPanel is mounted AFTER standard render and its activation props default to **false**, so the premium mode is visible as an unavailable alternative but cannot launch paid requests.
+- Wan 2.7 T2V/I2V adapter is gated by disabled-by-default server flag, trusted Singapore Alibaba Workspace origin, valid server key, and nonzero explicit per-job USD ceiling. Provider submit is async and only returns safe task ID/status.
+- Source-only server premium coordinator checks tenant JWT/RLS campaign/day membership, image rights, disallowed inputs, and idempotency; worker marks uncertain task creation UNKNOWN instead of blindly re-posting a billable request.
+- The source-only proposed SQL in `azure-functions/campaign-api/part3_sql/` extends the EXISTING `shop_subscriptions`/`shop_usage_reservations` rather than adding a second billing system. Premium allocation defaults to 0. The proposal is **not** in executable `supabase/migrations/` and has **NOT** been applied to hosted DEV.
+- Provider output private importer allows documented `dashscope-a717.oss-accelerate.aliyuncs.com` URLs and reviewed matching host shapes, but rejects arbitrary URL/redirects/local IP and invalid MP4 bytes/codecs/duration. Uploads use existing tenant-private storage and require a lease-token-checked completion callback. No external provider URL is returned to browser.
+
+## Incomplete / release-blocking tasks
+
+1. Coordinator rebase/merge review against newer Part1 main commits, especially shared React campaign UI, workflows and canonical docs. No Part2-owned files touched.
+2. **Promote/add new DB migration only under explicit approval:** review staged SQL, authoritative migration history, negative foreign tenant and race/rollback/credit test evidence, stable dollar exchange/cost pricing; no hosted schema changes today.
+3. Wire private premium create/status/download HTTP API, transactional premium outbox/queue trigger/poison/recovery, service-role CAS claim/lease/finalization RPCs and registered worker, so tasks progress end-to-end using UUID-only messages. None are live yet.
+4. Implement safe full provider result retrieval and pass **only** valid signed provider data from the internal poller into importer. Confirm expiry handling and no duplicate provider charge on UNKNOWN. Add cancellation/cost reconciliation and restricted production error codes.
+5. Compose multiple provider clips into 30-second campaign using current FFmpeg with explicit free fallback, optional provider substitution only after fresh price/rights approval, and independently licensed music.
+6. Owner to approve paid commercial API workspace, data-region/rights and image consent, per-tenant monetary ceilings and one strictly bounded paid DEV smoke before enabling customer premium.
+7. Real browser Auth with cross-tenant denials, provider clip MP4/ffprobe and signed download under approved fresh test identities. No live Wan invoice/task/media exists, no paid subscription or checkout activation.
+
+**DO NOT** mistake mocked CI or draft final PR for feature launch. Retain `RETAIL_PREMIUM_VIDEO_ENABLED=false` and no positive premium allowance until the tasks and separate approvals are complete. No WineShopPOS or GenAI Galaxy mutation.
+
+## 2026-10-24 continuation — new source-only milestones
+
+- #188 implements `AlibabaWanProvider.poll_private` returning signed output only to the privileged importer and `PremiumPollCompletion` with an existing database lease/tenant/reservation *contract*, not a hosted implementation. It rejects expired/duplicate Alibaba `Expires`, wrong claim/task, unsafe URL, invalid MP4 and stale finalization. No provider URL enters a customer response.
+- #189 adds `video-engine/premium_compose.py`, a no-shell FFmpeg/H.264/AAC 30-second join for 2-8 **already imported** licensed/rights-verified private Wan clips. It does not modify the existing standard image renderer; `select_render_mode` is strictly free-first. Music must pass existing local audio rights/codec validation; no royalty-free material is bundled.
+- Tests on the exact PR heads are green as recorded above. Private-completion test uses mocked provider/storage DB; new compositor FFmpeg command is unit-tested with fake clip commands, with real rejection of spoofed invalid MP4; **no live provider video or actual 30-second Wan composite E2E was run**. This is not user-ready.
+- Remaining **release blockers**: reviewed/applicable Supabase schema + atomic service-role RPCs, durable Azure premium queues/worker/poison/recovery, JWT-authenticated premium API/download, approved provider/region/rights/credit/rate policy, real signed frame/image consent, actual FFmpeg mixed stock + AI overlays/CTA, cancellation/provider reconciliation, real rendered composition/hosted E2E, final Coordinator merge. Keep all premium flags and allowances OFF. No external social publishing work or WineShopPOS changes.
+
+## 2026-10-24 further source-only continuation (PRs #193–#196)
+
+- #193 runs an actual **local/CI** FFmpeg composite from two independently generated 15-second synthetic 720p H264 clips and a locally generated test tone. Independent ffprobe confirms 30s H264/AAC; decoded red at 5s and blue at 25s proves correct order. It is NOT paid Wan output or production licensed soundtrack.
+- #194 creates `premium_http.PremiumHTTPBoundary` for JWT-scoped create/status and lease-name-checked private signed download. Not registered in live Azure Functions. Existing Part1 v1 routes unchanged.
+- #195 fixes a human approval vulnerability: Part1 day generated with `review_status='DRAFT'` can no longer reserve paid Wan credits. Source controller and un-applied proposed SQL require exactly `APPROVED`; actual Part1 authorized DRAFT->APPROVED workflow remains to be developed/reviewed.
+- #196 source-only `retail-premium-video` queue adapter, CAS outbox dispatcher, poison fingerprinting and reconcile sequence; all disabled by default, **no Azure queue provisioned**. Real service-role SQL RPCs and registered queue/timer triggers still unimplemented.
+- Final integrated verification after documentation commits must be checked separately, rather than assuming prior PR CI proves exact updated integration HEAD.
+- Blocking end-to-end work: atomic reviewed/approved new migration, actual service-role repository/RPCs for claims/outbox/lease/finalize/credits, Azure premium function registration/queue/poison and safe UNKNOWN reconciliation; branding/CTA mixed-media timeline; real JWT/tenant hosted E2E, licensed provider output and protected secrets, owner vendor spend/legal/data-region approval and one bounded paid DEV test. Keep Part3 OFF and PR #125 DRAFT; never merge to main from Part3 Lead.
+
+## 2026-10-24 latest verification and security fix
+
+- Immediately preceding #198, the exact integrated branch head `f88138fe678973240bf99207ec5277140485f4c7` completed dedicated P3 CI [#40030842866](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030842866) **2/2** and standard CI [#40030842790](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40030842790) **4/4**, **attempt 2**. The initial security job failed before SQL tests because GitHub runner port `54322` was occupied; a rerun passed with all Supabase SQL negative tests intact. Do not cite attempt 1 as a clean pass.
+- [#198](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/198) adds a strict equality check for `{shop}/renders/{job}/{lease}.mp4` provider upload receipts (prevent same-prefix substitutions) and `ffprobe -protocol_whitelist file` for imported files. Regressions proved unsafe paths cannot reach database finalization, and file-only probing prevents remote protocol use. All 6 exact PR-head checks passed before self-merge.
+- The merged branch head will change as this documentation lands; verify new exact HEAD CI separately. The live provider/DB/Azure/rights/cost release gates remain **UNMET** and premium flags remain off.
+
+## 2026-10-24 — Cancellation workstream and exact PR evidence
+- [#226](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/226) added a disabled-by-default source-only `PremiumCancelBoundary`, with independent offline Python tests ensuring only user-authorized QUEUED/pre-submit jobs can request an atomic release of the existing reservation. Revoked/foreign users, SUBMITTING/PENDING/UNKNOWN, forged receipts and lost cancel-vs-submit CAS races never receive cancellation success or assumed credits. Internally merged `bccd6e0` after [dedicated Part 3 #40076805919](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805919) **2/2** and [full standard #40076805911](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40076805911) **4/4**.
+- This is **not** executable cancellation: no service-role transactional `cancel_unsubmitted_atomic` SQL RPC, HTTP route, hosted negative test or live credits were changed. See `azure-functions/campaign-api/PART3_CANCELLATION_HANDOFF.md`. Formal vendor/data/rights/pricing/DEV spend approvals, migration, queued worker, real end-to-end testing and Coordinator-only main integration remain outstanding. Provider flag OFF; PR #125 stays DRAFT.
~~~~

### docs/part3/REAL_COMPOSITION_SMOKE.md
~~~~diff
@@ -0,0 +1,11 @@
+# Real offline Part 3 synthetic 30-second media smoke
+
+This milestone is **not a paid Wan run**, customer-ready media or hosted deployment.
+
+`tests/media/test_premium_compose_real.py` invokes the actual system FFmpeg binary to encode two distinct **synthetic** 15-second 720x1280 H.264 MP4 clips (red/blue) and generates a self-owned 440Hz PCM WAV test tone. It passes these as already-verified importer-style receipts into the Part 3-only `video-engine/premium_compose.py` function and independently invokes ffprobe on the assembled output to require exactly 30 seconds, H.264 video and AAC audio. It decodes frame pixels at 5s and 25s to prove both source clips were included in the correct order.
+
+All inputs are created in temporary storage and automatically deleted; the test never contacts Alibaba or other services, never activates paid video, and cannot reuse any production/customer assets. The fixture calls itself “synthetic” and MUST NOT be represented as a legitimate vendor-generated Wan video or production-licensed marketing soundtrack.
+
+This is invoked by existing `video-engine/ci.sh` via its standard `python3 -m unittest discover -s tests/media -p 'test_*.py' -v` command, within the existing FFmpeg CI gate. Ensure both the dedicated Part 3 CI 2/2 and repository CI 4/4 succeed before merging.
+
+The user-ready premium feature still requires: approved vendor, actual paid provider smoke (separate owner approval), durable backend/outbox/worker/lease/credit migration, authenticated API and signed downloads, media licensing/customer consent, mixed stock+AI branding/CTA, failure/UNKNOWN reconciliation and safe app activation.
~~~~

### frontend/src/features/campaigns/CampaignDashboard.jsx
~~~~diff
@@ -6,6 +6,7 @@ import {
   buildCampaignRequest, cloneCampaign, formatDayDate, linkedInText,
   serializeDraftDay, timelineErrors, updateCampaignDay, updateScene, withAuthorizedMedia,
 } from './campaign-model.mjs'
+import PremiumVideoPanel from '../premium-video/PremiumVideoPanel.jsx'
 import './CampaignDashboard.css'
 
 const INITIAL_BRIEF = 'Create seven days of helpful style inspiration for my clothing boutique, with LinkedIn posts and Instagram Reel concepts.'
@@ -676,6 +677,7 @@ export default function CampaignDashboard() {
             </div>}
         <RenderStatus day={day} valid={storyErrors.length === 0} live={loaded} dirty={changed || savingDay}
           job={renderJob} onRender={startRender} onDownload={downloadRender} />
+        <PremiumVideoPanel dayId={day.id} authorizedImageIds={assetIds} />
       </section>
       {notice && <p className="rg-session-notice" role="status">{notice}</p>}
       <p className="rg-footnote">{loaded
~~~~

### frontend/src/features/premium-video/PART3_UI_HANDOFF.md
~~~~diff
@@ -0,0 +1,5 @@
+# Part 3 UI handoff
+
+This isolated frontend component is intentionally not mounted in Part 1 CampaignDashboard until final integration. FFmpeg remains the default. Wan can only appear active when server entitlement, backend support and reviewed feature flag are all true. There is no customer checkout, automatic payment, provider key or provider URL in the frontend. The final coordinator must review shared campaign UI placement and the authenticated premium API contract before mounting it.
+
+Full existing 4-job Part 1 CI and dedicated 2-job Part 3 CI must pass on this PR before integration merge.
~~~~

### frontend/src/features/premium-video/PremiumVideoPanel.jsx
~~~~diff
@@ -0,0 +1,97 @@
+import { useState } from 'react'
+import { DEFAULT_VIDEO_ENGINE, premiumVideoChoices, PREMIUM_VIDEO_STATUS,
+         validatePremiumRequest } from './premium-video-model.mjs'
+
+/**
+ * Part 3 additive UI. Never posts to a provider or to a billing API.
+ * In Part 1 this panel is intentionally not mounted. When Part 3 reaches the
+ * final coordinator, mount beside the FFmpeg button and pass server-verified
+ * entitlement AND backend capability as separate values.
+ */
+export default function PremiumVideoPanel({
+  dayId, authorizedImageIds = [], entitlement = false,
+  endpointReady = false, featureEnabled = false, onCreate,
+}) {
+  const [engine, setEngine] = useState(DEFAULT_VIDEO_ENGINE)
+  const [mode, setMode] = useState('text')
+  const [duration, setDuration] = useState(5)
+  const [resolution, setResolution] = useState('720P')
+  const [assetId, setAssetId] = useState('')
+  const [status, setStatus] = useState('')
+  const [pending, setPending] = useState(false)
+  const options = premiumVideoChoices({ entitlement, endpointReady, featureEnabled })
+  const canUsePremium = options[1].available && typeof onCreate === 'function'
+
+  async function requestPremium() {
+    if (!canUsePremium || pending) return
+    setPending(true)
+    setStatus('')
+    try {
+      const body = validatePremiumRequest({
+        day_id: dayId, mode, resolution, duration_seconds: duration,
+        input_asset_id: mode === 'image' ? assetId : null,
+      }, { entitlement, endpointReady, featureEnabled })
+      const job = await onCreate(body)
+      if (!job || typeof job.job_id !== 'string' || job.status !== 'QUEUED') {
+        throw new Error('Premium video was not confirmed by the backend')
+      }
+      setStatus('Premium job queued. Credits are reserved by the server, not the browser.')
+    } catch (err) {
+      setStatus(err?.message || 'Premium request could not be accepted')
+    } finally {
+      setPending(false)
+    }
+  }
+
+  return (
+    <section aria-label="Video generator selection" className="rg-panel" data-premium-status={PREMIUM_VIDEO_STATUS}>
+      <h3>Choose your video generator</h3>
+      <p>Standard FFmpeg rendering remains the default and uses your existing render quota.</p>
+      <fieldset>
+        <legend>Video engine</legend>
+        {options.map(item => (
+          <label key={item.id} style={{ display: 'block', marginBottom: '.6rem' }}>
+            <input type="radio" name="rg-video-engine" value={item.id}
+              checked={engine === item.id} disabled={!item.available || (item.id === 'wan' && !canUsePremium)}
+              onChange={() => setEngine(item.id)} />
+            <strong> {item.label}</strong>
+            <small style={{ display: 'block' }}>{item.cost}</small>
+          </label>
+        ))}
+      </fieldset>
+      {!canUsePremium && (
+        <p role="status">Premium Wan videos are not active. Provider approval, private media import, and server-controlled credits are required. You can still generate standard FFmpeg Reels above.</p>
+      )}
+      {engine === 'wan' && canUsePremium && <>
+        <label>Generation source
+          <select value={mode} onChange={event => setMode(event.target.value)}>
+            <option value="text">Text-to-video</option>
+            <option value="image">Animate an approved business image</option>
+          </select>
+        </label>
+        {mode === 'image' && <label>Approved source image
+          <select value={assetId} onChange={event => setAssetId(event.target.value)}>
+            <option value="">Choose an authorized image</option>
+            {authorizedImageIds.map(id => <option key={id} value={id}>{id.slice(0, 8)}…</option>)}
+          </select>
+        </label>}
+        <label>Duration
+          <select value={duration} onChange={event => setDuration(Number(event.target.value))}>
+            {[5,10,15].map(seconds => <option key={seconds} value={seconds}>{seconds} seconds</option>)}
+          </select>
+        </label>
+        <label>Resolution
+          <select value={resolution} onChange={event => setResolution(event.target.value)}>
+            <option value="720P">720p</option>
+            <option value="1080P">1080p</option>
+          </select>
+        </label>
+        <p>Final premium credit estimate and permission must be confirmed by the server before submitting. Content may be transferred to an approved external provider.</p>
+        <button type="button" disabled={pending} onClick={requestPremium}>
+          {pending ? 'Submitting…' : 'Request premium AI video'}
+        </button>
+      </>}
+      {status && <p role="status">{status}</p>}
+    </section>
+  )
+}
~~~~

### frontend/src/features/premium-video/premium-video-model.mjs
~~~~diff
@@ -0,0 +1,33 @@
+// Part 3 additive UI model: FFmpeg stays the default, premium unavailable.
+// Frontend capability toggles NEVER grant entitlement or allow a paid API call.
+// A server-owned permission and dedicated authenticated endpoint are also needed.
+const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
+export const DEFAULT_VIDEO_ENGINE = 'ffmpeg'
+export const PREMIUM_VIDEO_STATUS = 'AWAITING_PROVIDER_AND_CREDIT_APPROVAL'
+
+export function premiumVideoChoices({ entitlement = false, endpointReady = false,
+                                     featureEnabled = false } = {}) {
+  const premiumAvailable = entitlement === true && endpointReady === true && featureEnabled === true
+  return [
+    { id: 'ffmpeg', label: 'Standard FFmpeg Reel', available: true, cost: 'Included in existing render quota' },
+    { id: 'wan', label: 'Premium Wan AI video', available: premiumAvailable,
+      cost: 'Premium credits · requires a confirmed server quote' },
+  ]
+}
+
+export function validatePremiumRequest(input, { entitlement = false,
+                                        endpointReady = false, featureEnabled = false } = {}) {
+  if (!input || typeof input !== 'object' ||
+      !premiumVideoChoices({ entitlement, endpointReady, featureEnabled })[1].available) {
+    throw new Error('Premium video is not activated for this business')
+  }
+  const { day_id, mode, resolution, duration_seconds, input_asset_id } = input
+  if (!UUID.test(day_id || '') || !['text','image'].includes(mode) ||
+      !['720P','1080P'].includes(resolution) ||
+      !Number.isInteger(duration_seconds) || duration_seconds < 2 || duration_seconds > 15 ||
+      (mode === 'image' && !UUID.test(input_asset_id || '')) ||
+      (mode === 'text' && input_asset_id !== null)) {
+    throw new Error('Invalid premium video options')
+  }
+  return { day_id, mode, resolution, duration_seconds, input_asset_id }
+}
~~~~

### tests/ai/test_premium_wan_provider.py
~~~~diff
@@ -0,0 +1,122 @@
+"""Offline/no-network Part 3 provider safety and Wan protocol tests."""
+import pytest
+
+from ai_agents.premium_video import (
+    AlibabaWanProvider, WanRequest, PremiumVideoDisabled,
+    PremiumVideoProviderError, campaign_video_prompt, validate_private_frame,
+)
+
+SHOP = "16b9017c-8f02-4a80-b312-5c924213d15a"
+SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"
+URL = (SUPABASE + "/storage/v1/object/sign/retailgrowth-media/" +
+       SHOP + "/uploads/asset.png?token=server-only")
+
+
+def provider(**kwargs):
+    defaults = dict(
+        enabled=True, workspace_origin="https://work123.ap-southeast-1.maas.aliyuncs.com",
+        api_key="not-a-real-api-key-1234", approved_max_usd=5,
+        supabase_origin=SUPABASE,
+    )
+    defaults.update(kwargs)
+    return AlibabaWanProvider(**defaults)
+
+
+def test_fail_closed_default_and_missing_pricing_gate():
+    safe = WanRequest("text", "A video", 5)
+    with pytest.raises(PremiumVideoDisabled):
+        AlibabaWanProvider().submit(safe)
+    with pytest.raises(PremiumVideoDisabled):
+        provider(approved_max_usd=0).submit(safe)
+
+
+def test_rejects_endpoint_ssrf_even_with_key_and_gate():
+    for origin in ("http://work123.ap-southeast-1.maas.aliyuncs.com",
+                   "https://work123.ap-southeast-1.maas.aliyuncs.com.evil.com",
+                   "https://127.0.0.1", "https://work123.ap-southeast-1.maas.aliyuncs.com/path"):
+        with pytest.raises(PremiumVideoDisabled):
+            provider(workspace_origin=origin).submit(WanRequest("text", "Sample"))
+
+
+def test_request_types_and_cost_bounds():
+    for options in (dict(mode="text", prompt="x", duration_seconds=30),
+                    dict(mode="text", prompt="x", duration_seconds=True),
+                    dict(mode="text", prompt="x", resolution="4K"),
+                    dict(mode="text", prompt="x", ratio="90:10"),
+                    dict(mode="image", prompt="x", signed_first_frame=URL)):
+        with pytest.raises(ValueError):
+            WanRequest(**options)
+    with pytest.raises(PremiumVideoDisabled):
+        provider(approved_max_usd=.40).submit(WanRequest("text", "Hello", 5))
+    assert provider().estimated_usd(WanRequest("text", "Hello", 5)) == .5
+    assert provider().estimated_usd(WanRequest("text", "Hello", 10, "1080P")) == 1.5
+
+
+def test_wan_text_submit_is_async_and_no_unapproved_request():
+    calls = []
+    def transport(method, url, headers, payload):
+        calls.append((method, url, headers, payload))
+        return {"output": {"task_id": "task00000042", "task_status": "PENDING"}}
+
+    p = provider(transport=transport)
+    task = p.submit(WanRequest("text", "Boutique launch", duration_seconds=5))
+    assert task == {"provider": "alibaba-wan", "model": "wan2.7-t2v-2026-06-12",
+                    "task_id": "task00000042", "status": "PENDING"}
+    method, endpoint, headers, payload = calls[0]
+    assert method == "POST" and endpoint.endswith("/video-synthesis")
+    assert headers["X-DashScope-Async"] == "enable"
+    assert payload["parameters"]["ratio"] == "9:16"
+    assert payload["parameters"]["watermark"] is True
+    assert payload["input"] == {"prompt": "Boutique launch"}
+
+
+def test_wan_image_uses_signed_owned_private_frame_only():
+    calls = []
+    def transport(method, url, headers, payload):
+        calls.append(payload)
+        return {"output": {"task_id": "task00000123"}}
+    spec = WanRequest("image", "Motion", shop_id=SHOP, signed_first_frame=URL)
+    assert provider(transport=transport).submit(spec)["model"] == "wan2.7-i2v-2026-04-25"
+    assert calls[0]["input"]["media"] == [{"type": "first_frame", "url": URL}]
+    assert "ratio" not in calls[0]["parameters"]
+
+    for bad in (
+        "https://evil.com/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a?token=x",
+        SUPABASE + "/storage/v1/object/public/retailgrowth-media/" + SHOP + "/a",
+        SUPABASE + "/storage/v1/object/sign/retailgrowth-media/other/a?token=x",
+        SUPABASE + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/a",
+        SUPABASE + "/storage/v1/object/sign/retailgrowth-media/" + SHOP + "/../a?token=x",
+    ):
+        with pytest.raises(ValueError):
+            validate_private_frame(bad, shop_id=SHOP, supabase_origin=SUPABASE)
+
+
+def test_poll_returns_no_externally_signed_video_download_url():
+    def transport(method, url, headers, payload):
+        assert method == "GET" and url.endswith("/api/v1/tasks/task00000042")
+        return {"output": {"task_id": "task00000042",
+                            "task_status": "SUCCEEDED",
+                            "video_url": "https://untrusted.test/download.mp4?secret=abc"}}
+    status = provider(transport=transport).poll("task00000042")
+    assert status == {"task_id": "task00000042", "status": "SUCCEEDED"}
+    assert "video_url" not in status
+
+
+def test_invalid_task_ids_and_provider_responses_are_denied():
+    with pytest.raises(ValueError):
+        provider(transport=lambda *args: {}).poll("../private")
+    with pytest.raises(PremiumVideoProviderError):
+        provider(transport=lambda *args: {"output": {"task_status": "PENDING"}}).submit(
+            WanRequest("text", "Sample"))
+    with pytest.raises(PremiumVideoProviderError):
+        provider(transport=lambda *args: {"output": {"task_id": "task00000042",
+                                                      "task_status": "UNKNOWN_BAD"}}).poll(
+            "task00000042")
+
+
+def test_prompt_uses_reviewed_claims_only():
+    day = {"topic": "Day 1 - fresh arrivals", "instagram": {"reel": {"cta": "Visit us"}}}
+    result = campaign_video_prompt(day)
+    assert "fresh arrivals" in result and "Visit us" in result
+    assert "20% off" not in result
+    assert "20% off" in campaign_video_prompt(day, approved_offer="20% off")
~~~~

### tests/api/test_premium_cancel.py
~~~~diff
@@ -0,0 +1,123 @@
+"""Offline Part 3 cancellation security/race tests. Zero cloud/provider calls."""
+from pathlib import Path
+import sys
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
+
+import pytest
+from premium_cancel import PremiumCancelBoundary
+
+UID = "123e4567-e89b-42d3-a456-426614174001"
+OTHER = "123e4567-e89b-42d3-a456-426614174002"
+SID = "123e4567-e89b-42d3-a456-426614174003"
+JID = "123e4567-e89b-42d3-a456-426614174004"
+
+
+class Users:
+    def __init__(self, allow=True):
+        self.allow = allow
+    def member(self, token, user, shop, write=False):
+        assert write is True and token == "mock-jwt" and shop == SID
+        return self.allow and user == UID
+
+
+class Store:
+    def __init__(self, **overrides):
+        self.job = dict(id=JID, shop_id=SID, status="QUEUED",
+                        provider_task_id=None, attempt_token=None)
+        self.job.update(overrides)
+        self.calls = []
+        self.receipt = dict(id=JID, shop_id=SID, status="CANCELED",
+                            credit_released=True, provider_submission_not_started=True,
+                            provider_task_id=None)
+    def get_authenticated(self, token, job_id):
+        assert token == "mock-jwt"
+        return self.job
+    def cancel_unsubmitted_atomic(self, job_id, shop_id, user_id):
+        self.calls.append((job_id, shop_id, user_id))
+        return self.receipt
+
+
+def test_disabled_by_default_does_not_even_read_storage():
+    store = Store()
+    assert PremiumCancelBoundary(Users(), store).cancel("mock-jwt", UID, JID) == (
+        503, {"error": "PREMIUM_VIDEO_DISABLED"})
+    assert not store.calls
+
+
+def test_only_owned_queued_job_with_transaction_receipt_can_cancel():
+    store = Store()
+    api = PremiumCancelBoundary(Users(), store, enabled=True)
+    assert api.cancel("mock-jwt", UID, JID) == (
+        200, {"job_id": JID, "status": "CANCELED"})
+    assert store.calls == [(JID, SID, UID)]
+
+
+def test_foreign_and_inactive_member_cannot_cancel_or_refund():
+    for allow, who in ((False, UID), (True, OTHER)):
+        store = Store()
+        assert PremiumCancelBoundary(Users(allow), store, enabled=True).cancel(
+            "mock-jwt", who, JID)[0] == 404
+        assert store.calls == []
+
+
+@pytest.mark.parametrize("status", ["SUBMITTING", "PENDING", "RUNNING",
+                                      "IMPORTING", "SUCCEEDED", "FAILED",
+                                      "UNKNOWN"])
+def test_no_refund_after_provider_attempt_or_uncertain_status(status):
+    store = Store(status=status)
+    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
+        "mock-jwt", UID, JID)[0] == 409
+    assert store.calls == []
+
+
+@pytest.mark.parametrize("field,value", [
+    ("attempt_token", "123e4567-e89b-42d3-a456-426614174005"),
+    ("provider_task_id", "provider-task-id")
+])
+def test_even_queued_row_with_submit_evidence_cannot_cancel(field, value):
+    store = Store(**{field: value})
+    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
+        "mock-jwt", UID, JID)[0] == 409
+    assert not store.calls
+
+
+def test_canceled_job_needs_proof_of_released_ledger_and_no_submit():
+    store = Store(status="CANCELED")
+    api = PremiumCancelBoundary(Users(), store, enabled=True)
+    assert api.cancel("mock-jwt", UID, JID)[0] == 409
+    store.job.update(credit_released=True, provider_submission_not_started=True)
+    assert api.cancel("mock-jwt", UID, JID) == (
+        200, {"job_id": JID, "status": "CANCELED"})
+    assert not store.calls
+
+
+@pytest.mark.parametrize("overrides", [
+    {"status": "QUEUED"}, {"id": OTHER},
+    {"shop_id": OTHER}, {"credit_released": False},
+    {"provider_submission_not_started": False},
+    {"provider_task_id": "provider-task-id"}
+])
+def test_bad_or_partial_atomic_receipt_fails_closed(overrides):
+    store = Store()
+    store.receipt.update(overrides)
+    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
+        "mock-jwt", UID, JID)[0] == 503
+    assert len(store.calls) == 1
+
+
+def test_lost_race_refunds_nothing():
+    store = Store()
+    store.receipt = None
+    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
+        "mock-jwt", UID, JID) == (
+        409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"})
+
+
+def test_bad_ids_and_foreign_job_identity_fail_safely():
+    store = Store()
+    api = PremiumCancelBoundary(Users(), store, enabled=True)
+    assert api.cancel("mock-jwt", UID, "../../bad")[0] == 400
+    store.job["id"] = OTHER
+    assert api.cancel("mock-jwt", UID, JID)[0] == 404
+    assert not store.calls
~~~~

### tests/api/test_premium_http.py
~~~~diff
@@ -0,0 +1,184 @@
+"""Offline Part 3 premium HTTP boundary tests: no live Azure, DB or Wan calls."""
+import sys
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
+                       "azure-functions" / "campaign-api"))
+
+from premium_http import PremiumHTTPBoundary
+from security import AuthenticationError
+from tenant_store import StorageUnavailable
+
+UID = "123e4567-e89b-42d3-a456-426614174001"
+SID = "123e4567-e89b-42d3-a456-426614174002"
+CID = "123e4567-e89b-42d3-a456-426614174003"
+JID = "123e4567-e89b-42d3-a456-426614174004"
+ASSET = "123e4567-e89b-42d3-a456-426614174005"
+LEASE = "123e4567-e89b-42d3-a456-426614174006"
+OUTPUT = f"{SID}/renders/{JID}/{LEASE}.mp4"
+
+
+class Coordinator:
+    def __init__(self):
+        self.calls = []
+
+    def create(self, token, user, campaign, body):
+        self.calls.append(("create", token, user, campaign, body))
+        return 202, {"job_id": JID, "status": "QUEUED"}
+
+    def status(self, token, user, job_id):
+        self.calls.append(("status", token, user, job_id))
+        return 200, {"job_id": JID, "status": "PENDING"}
+
+
+class Store:
+    def __init__(self):
+        self.rows = {JID: {"id": JID, "shop_id": SID,
+                           "status": "SUCCEEDED", "output_asset_id": ASSET}}
+        self.calls = []
+
+    def get_authenticated(self, token, job_id):
+        self.calls.append(("job", token, job_id))
+        return self.rows.get(job_id)
+
+
+class Users:
+    def __init__(self):
+        self.can_read = True
+        self.allowed_asset = True
+        self.asset_overrides = {}
+        self.signs = []
+
+    def member(self, token, user, shop):
+        return self.can_read and token == "valid-user-jwt" and user == UID and shop == SID
+
+    def asset(self, token, sid, asset):
+        assert token == "valid-user-jwt"
+        if not self.allowed_asset:
+            return None
+        return dict({"id": ASSET, "shop_id": SID,
+                     "storage_bucket": "retailgrowth-media",
+                     "object_path": OUTPUT, "mime_type": "video/mp4"},
+                    **self.asset_overrides)
+
+    def sign_download(self, token, shop_id, object_path):
+        self.signs.append((token, shop_id, object_path))
+        return "https://signed.test.invalid/storage/v1/object/sign/" + object_path + "?token=mock"
+
+
+def auth(token):
+    if token == "valid-user-jwt":
+        return UID
+    raise AuthenticationError("Untrusted test bearer")
+
+
+def fixture(enabled=True):
+    users, store, controller = Users(), Store(), Coordinator()
+    api = PremiumHTTPBoundary(auth, users, store, controller, enabled=enabled)
+    return api, users, store, controller
+
+
+def test_default_disabled_and_missing_bearer_fail_before_any_job_or_download():
+    api, users, store, controller = fixture(enabled=False)
+    endpoint = f"/premium-video-jobs/{JID}/download"
+    assert api.handle("GET", endpoint, "Bearer valid-user-jwt") == (
+        503, {"error": "PREMIUM_VIDEO_DISABLED"})
+    for bad in ("", "invalid", "Bearer ", "Bearer forged"):
+        assert api.handle("GET", endpoint, bad)[0] == 401
+    assert not users.signs and not store.calls and not controller.calls
+
+
+def test_valid_authenticated_creation_and_status_does_not_leak_task_id():
+    api, users, store, controller = fixture()
+    body = {"mode": "text", "day_id": CID, "resolution": "720P",
+            "duration_seconds": 5, "input_asset_id": None}
+    assert api.handle("POST", f"/campaigns/{CID}/premium-videos",
+                      "Bearer valid-user-jwt", body) == (
+        202, {"job_id": JID, "status": "QUEUED"})
+    assert controller.calls[-1] == ("create", "valid-user-jwt", UID, CID, body)
+    assert api.handle("GET", f"/premium-video-jobs/{JID}",
+                      "Bearer valid-user-jwt") == (
+        200, {"job_id": JID, "status": "PENDING"})
+    assert not users.signs
+
+
+def test_private_download_issues_only_rls_scoped_signed_retailgrowth_link():
+    api, users, store, controller = fixture()
+    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
+                      "Bearer valid-user-jwt") == (
+        200, {"url": "https://signed.test.invalid/storage/v1/object/sign/" +
+              OUTPUT + "?token=mock"})
+    assert users.signs == [("valid-user-jwt", SID, OUTPUT)]
+    assert controller.calls == []
+
+
+def test_foreign_job_or_revoked_shop_role_is_404_and_never_signs():
+    api, users, store, controller = fixture()
+    users.can_read = False
+    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
+                      "Bearer valid-user-jwt") == (404, {"error": "NOT_FOUND"})
+    assert not users.signs
+    users.can_read = True
+    store.rows[JID] = {"id": JID, "shop_id": SID, "status": "SUCCEEDED",
+                       "output_asset_id": None}
+    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
+                      "Bearer valid-user-jwt")[0] == 409
+    assert not users.signs
+
+
+def test_pending_task_cannot_be_downloaded():
+    api, users, store, controller = fixture()
+    store.rows[JID]["status"] = "IMPORTING"
+    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
+                      "Bearer valid-user-jwt") == (
+        409, {"error": "OUTPUT_NOT_READY"})
+    assert users.signs == []
+
+
+def test_foreign_or_malformed_asset_receipt_never_signs():
+    changes = [
+        {"object_path": SID + "/renders/other-job/" + LEASE + ".mp4"},
+        {"object_path": SID + "/renders/" + JID + "/../../other.mp4"},
+        {"object_path": OUTPUT + "?evil=true"},
+        {"object_path": OUTPUT.replace(".mp4", ".MP4")},
+        {"object_path": SID + "/renders/" + JID + "/not-a-uuid.mp4"},
+        {"mime_type": "image/png"},
+        {"storage_bucket": "public-media"},
+        {"shop_id": "123e4567-e89b-42d3-a456-426614174007"},
+        {"id": "123e4567-e89b-42d3-a456-426614174007"},
+    ]
+    for override in changes:
+        api, users, store, controller = fixture()
+        users.asset_overrides = override
+        code, response = api.handle(
+            "GET", f"/premium-video-jobs/{JID}/download", "Bearer valid-user-jwt")
+        assert code == 404, (override, response)
+        assert users.signs == []
+
+
+def test_no_untrusted_query_or_http_method_can_trigger_creation_or_download():
+    api, users, store, controller = fixture()
+    for method, path in [
+        ("POST", f"/premium-video-jobs/{JID}/download"),
+        ("GET", f"/premium-video-jobs/{JID}/download?token=stolen"),
+        ("GET", f"/campaigns/{CID}/premium-videos"),
+        ("POST", f"/campaigns/{CID}/premium-videos?paid=true"),
+        ("GET", f"/premium-video-jobs/{JID}/unknown"),
+    ]:
+        assert api.handle(method, path, "Bearer valid-user-jwt")[0] == 404
+    assert controller.calls == [] and users.signs == []
+
+
+def test_malformed_identifiers_and_signed_media_store_failure_are_sanitized():
+    api, users, store, controller = fixture()
+    assert api.handle("GET", "/premium-video-jobs/../../secrets",
+                      "Bearer valid-user-jwt")[0] == 404
+    assert api.handle("GET", "/premium-video-jobs/not-a-uuid",
+                      "Bearer valid-user-jwt")[0] == 400
+
+    def unavailable(*args):
+        raise StorageUnavailable("private provider URL and secret")
+    users.sign_download = unavailable
+    code, payload = api.handle("GET", f"/premium-video-jobs/{JID}/download",
+                               "Bearer valid-user-jwt")
+    assert code == 503 and payload == {"error": "SERVICE_UNAVAILABLE"}
~~~~

### tests/api/test_premium_video_jobs.py
~~~~diff
@@ -0,0 +1,210 @@
+"""Mocked Part 3 orchestration: no hosted DB, WAN, Azure or paid APIs."""
+import sys
+from pathlib import Path
+import pytest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
+                       "azure-functions" / "campaign-api"))
+# This independently-owned workstream targets the provider interface without
+# copying its implementation. CI on the isolated jobs branch stubs it; once
+# provider PR is merged first, pytest imports the real module automatically.
+import importlib.util
+if importlib.util.find_spec("ai_agents.premium_video") is None:
+    import types
+    module = types.ModuleType("ai_agents.premium_video")
+    class FakeWanRequest:
+        def __init__(self, mode, prompt, duration_seconds=5, resolution="720P",
+                     signed_first_frame=None, shop_id=None):
+            self.mode, self.prompt = mode, prompt
+            self.duration_seconds, self.resolution = duration_seconds, resolution
+            self.signed_first_frame, self.shop_id = signed_first_frame, shop_id
+    class FakePremiumVideoDisabled(RuntimeError):
+        pass
+    module.WanRequest = FakeWanRequest
+    module.AlibabaWanProvider = object
+    module.PremiumVideoDisabled = FakePremiumVideoDisabled
+    module.campaign_video_prompt = lambda day: "Marketing: " + day["topic"]
+    sys.modules["ai_agents.premium_video"] = module
+
+from premium_video_jobs import PremiumVideoCoordinator, PremiumSubmissionWorker
+
+UID = "123e4567-e89b-42d3-a456-426614174001"
+SID = "123e4567-e89b-42d3-a456-426614174002"
+CID = "123e4567-e89b-42d3-a456-426614174003"
+DID = "123e4567-e89b-42d3-a456-426614174004"
+AID = "123e4567-e89b-42d3-a456-426614174005"
+JID = "123e4567-e89b-42d3-a456-426614174006"
+LEASE = "123e4567-e89b-42d3-a456-426614174007"
+
+class Users:
+    def __init__(self, *, allow=True, asset_allowed=True):
+        self.allow, self.asset_allowed = allow, asset_allowed
+    def campaign(self, token, user, cid):
+        assert token == "signed-test-jwt" and user == UID
+        return {"id": cid, "shop_id": SID, "status": "DRAFT",
+                "days": [{"id": DID, "shop_id": SID, "topic": "Autumn coats",
+                          "instagram": {"reel": {"cta": "Visit us"}},
+                          "review_status": "APPROVED"}]}
+    def member(self, token, user, shop, write=False):
+        return self.allow and shop == SID and user == UID
+    def asset(self, token, sid, asset):
+        return ({"id": asset, "mime_type": "image/jpeg"} if self.asset_allowed else None)
+
+class Rights:
+    def __init__(self, allowed=True): self.allowed = allowed
+    def valid_media(self, sid, ids): return self.allowed
+
+class Store:
+    def __init__(self):
+        self.inserted = []
+        self.found = None
+    def find_authenticated(self, token, shop, digest): return self.found
+    def insert_reserved(self, row):
+        self.inserted.append(row)
+        return row
+    def get_authenticated(self, token, job_id):
+        return self.found
+
+def payload(mode="text", aid=None):
+    return {"day_id": DID, "mode": mode, "resolution": "720P",
+            "duration_seconds": 5, "input_asset_id": aid}
+
+def test_fails_closed_without_approval_or_creating_job():
+    store = Store()
+    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=False)
+    assert api.create("signed-test-jwt", UID, CID, payload()) == (
+        503, {"error": "PREMIUM_VIDEO_DISABLED"})
+    assert not store.inserted
+
+def test_authenticated_tenant_and_reviewed_campaign_required():
+    store = Store()
+    api = PremiumVideoCoordinator(Users(allow=False), store, Rights(), enabled=True)
+    assert api.create("signed-test-jwt", UID, CID, payload())[0] == 403
+    assert not store.inserted
+
+def test_source_only_insert_is_canonical_and_idempotent():
+    store = Store()
+    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
+    code, res = api.create("signed-test-jwt", UID, CID, payload())
+    assert code == 202 and res["status"] == "QUEUED" and res["job_id"]
+    assert "provider_task_id" not in res and "idempotency_key" not in res
+    record = store.inserted[0]
+    assert record["shop_id"] == SID and record["requested_by"] == UID
+    assert record["model_id"] == "wan2.7-t2v-2026-06-12"
+    assert len(record["idempotency_key"]) == 64
+    store.found = record
+    assert api.create("signed-test-jwt", UID, CID, payload())[0] == 200
+    assert len(store.inserted) == 1
+
+def test_image_mode_checks_current_asset_membership_and_commercial_rights():
+    for allow_asset, allow_rights in [(False, True), (True, False)]:
+        store = Store()
+        api = PremiumVideoCoordinator(Users(asset_allowed=allow_asset), store,
+                                      Rights(allow_rights), enabled=True)
+        assert api.create("signed-test-jwt", UID, CID, payload("image", AID))[0] == 403
+        assert store.inserted == []
+    store = Store()
+    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
+    assert api.create("signed-test-jwt", UID, CID, payload("image", AID))[0] == 202
+    assert store.inserted[0]["input_asset_id"] == AID
+    assert store.inserted[0]["model_id"] == "wan2.7-i2v-2026-04-25"
+
+@pytest.mark.parametrize("body", [
+    {"mode": "text"}, payload("invalid"), payload("text", AID),
+    payload("image", None), {**payload(), "duration_seconds": 16},
+    {**payload(), "duration_seconds": True}, {**payload(), "resolution": "4K"}
+])
+def test_rejects_invalid_paid_video_requests(body):
+    store = Store()
+    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
+    assert api.create("signed-test-jwt", UID, CID, body)[0] == 400
+    assert store.inserted == []
+
+def test_status_never_exposes_provider_id_or_foreign_job():
+    store = Store()
+    store.found = {"id": JID, "shop_id": SID, "status": "RUNNING",
+                   "provider_task_id": "secret-provider-task", "reserved_usd": 1.5}
+    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
+    code, result = api.status("signed-test-jwt", UID, JID)
+    assert code == 200 and result["job_id"] == JID
+    assert "provider_task_id" not in result and "reserved_usd" not in result
+    api = PremiumVideoCoordinator(Users(allow=False), store, Rights(), enabled=True)
+    assert api.status("signed-test-jwt", UID, JID)[0] == 404
+
+class WorkerStore:
+    def __init__(self):
+        self.claimed = {"id": JID, "shop_id": SID, "status": "SUBMITTING",
+                        "attempt_token": LEASE, "mode": "text",
+                        "prompt": "Approved reviewed creative", "seconds": 5,
+                        "resolution": "720P"}
+        self.calls = []
+    def claim(self, job_id): return self.claimed
+    def finish_attempt(self, *args, **kwargs): self.calls.append(("finish", args, kwargs))
+    def record_task(self, *args): self.calls.append(("task", args))
+    def claim_poll(self, jid):
+        return {"provider_task_id": "job-12345678", "attempt_token": LEASE}
+    def record_poll(self, *args): self.calls.append(("poll", args))
+
+class Provider:
+    def __init__(self, error=None): self.error, self.count = error, 0
+    def submit(self, spec):
+        self.count += 1
+        if self.error: raise self.error
+        return {"task_id": "job-12345678"}
+    def poll(self, task_id):
+        return {"task_id": task_id, "status": "SUCCEEDED"}
+
+def test_worker_submits_once_without_calling_paid_provider_twice():
+    store, provider = WorkerStore(), Provider()
+    worker = PremiumSubmissionWorker(store, provider)
+    assert worker.submit_once(JID) == "PENDING"
+    assert provider.count == 1
+    assert store.calls == [("task", (JID, LEASE, "job-12345678"))]
+
+def test_unknown_provider_response_never_retries_or_double_charges():
+    store, provider = WorkerStore(), Provider(RuntimeError("network response lost"))
+    worker = PremiumSubmissionWorker(store, provider)
+    assert worker.submit_once(JID) == "UNKNOWN"
+    assert provider.count == 1
+    assert store.calls[0][0] == "finish"
+    assert store.calls[0][2]["error_code"] == "PROVIDER_RESULT_UNKNOWN"
+
+def test_provider_success_not_mistaken_for_private_media_download():
+    store, provider = WorkerStore(), Provider()
+    assert PremiumSubmissionWorker(store, provider).poll_once(JID) == "SUCCEEDED"
+    assert store.calls == [("poll", (JID, LEASE, "IMPORTING"))]
+
+
+@pytest.mark.parametrize("review_status", ["DRAFT", "REJECTED", None, ""])
+def test_paid_provider_cannot_reserve_unapproved_campaign_day(review_status):
+    """A generated DRAFT is not approval to consume money or transmit content."""
+    class NotApprovedUsers(Users):
+        def campaign(self, token, user, cid):
+            result = super().campaign(token, user, cid)
+            result["days"][0]["review_status"] = review_status
+            return result
+
+    store = Store()
+    coordinator = PremiumVideoCoordinator(
+        NotApprovedUsers(), store, Rights(), enabled=True)
+    assert coordinator.create("signed-test-jwt", UID, CID, payload()) == (
+        409, {"error": "DAY_NOT_APPROVED"})
+    assert store.inserted == []
+
+
+def test_review_gate_checked_before_image_rights_and_credit_write():
+    class DraftUsers(Users):
+        def campaign(self, token, user, cid):
+            result = super().campaign(token, user, cid)
+            result["days"][0]["review_status"] = "DRAFT"
+            return result
+
+    class NoRightsShouldBeQueried:
+        def valid_media(self, *args):
+            raise AssertionError("Never inspect or reserve unapproved media")
+
+    store = Store()
+    api = PremiumVideoCoordinator(
+        DraftUsers(), store, NoRightsShouldBeQueried(), enabled=True)
+    assert api.create("signed-test-jwt", UID, CID, payload("image", AID))[0] == 409
+    assert store.inserted == []
~~~~

### tests/media/test_premium_clip_compose.py
~~~~diff
@@ -0,0 +1,122 @@
+"""Offline Part 3 FFmpeg composition tests; never calls Wan or Azure."""
+import sys
+from pathlib import Path
+import tempfile
+import unittest
+from unittest.mock import patch
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
+from premium_compose import (PremiumComposeError, compose_approved_clips,
+                             select_render_mode)
+
+SHOP = "123e4567-e89b-42d3-a456-426614174001"
+OTHER = "123e4567-e89b-42d3-a456-426614174002"
+RIGHTS = {"commercial_use": True, "license": "commercial",
+          "source": "paid commercial Model Studio output",
+          "evidence": "reviewed workspace terms and marketing consent"}
+
+
+class PremiumAssemblyTests(unittest.TestCase):
+    def setUp(self):
+        self.scratch = tempfile.TemporaryDirectory(prefix="retail-compose-test-")
+        self.addCleanup(self.scratch.cleanup)
+        self.root = Path(self.scratch.name)
+        self.assets = self.root / "assets"
+        self.assets.mkdir()
+        for f in ("clip1.mp4", "clip2.mp4"):
+            (self.assets / f).write_bytes(b"mp4-fixture" * 130)
+        self.output = self.root / "output" / "result.mp4"
+        self.clips = [{"shop_id": SHOP, "asset_id": f"clip{i}",
+                       "provider": "alibaba-wan", "status": "SUCCEEDED",
+                       "duration_seconds": 15, "path": f"clip{i}.mp4",
+                       "rights": RIGHTS.copy()} for i in (1, 2)]
+
+    def render(self, *, clips=None, music=None):
+        commands = []
+        def fake_run(cmd, **kwargs):
+            commands.append(cmd)
+            Path(cmd[-1]).write_bytes(b"fake-output")
+        with patch("premium_compose._check_input_clip"), \
+             patch("premium_compose.inspect_staged_audio"), \
+             patch("premium_compose.subprocess.run", side_effect=fake_run), \
+             patch("premium_compose.verify_reel",
+                   return_value={"duration_seconds": 30.0, "video_codec": "h264",
+                                 "audio_codec": "aac"}):
+            result = compose_approved_clips(
+                shop_id=SHOP, clips=self.clips if clips is None else clips,
+                asset_root=self.assets, output=self.output,
+                licensed_music=music, width=720, height=1280,
+                fps=12, preset="ultrafast")
+        return result, commands
+
+    def test_default_render_route_is_free_even_if_premium_model_exists(self):
+        self.assertEqual(select_render_mode(), "ffmpeg")
+        self.assertEqual(select_render_mode(premium_enabled=True), "ffmpeg")
+        self.assertEqual(select_render_mode(premium_enabled=True,
+                         authorized=True, all_clips_ready=True), "premium")
+
+    def test_two_licensed_fifteen_second_clips_make_one_30_second_video(self):
+        result, commands = self.render()
+        self.assertEqual(result["duration_seconds"], 30)
+        self.assertTrue(self.output.exists())
+        self.assertEqual(len(commands), 1)
+        cmd = commands[0]
+        self.assertEqual(cmd[0], "ffmpeg")
+        self.assertIn("concat=n=2:v=1:a=0", " ".join(cmd))
+        self.assertIn("anullsrc", " ".join(cmd))
+        self.assertIn("libx264", cmd)
+        self.assertNotIn("shell=True", " ".join(cmd))
+
+    def test_untrusted_clips_are_rejected_before_any_video_rendering(self):
+        variations = [
+            (0, "shop_id", OTHER), (0, "provider", "unknown"),
+            (0, "status", "PENDING"), (0, "duration_seconds", 16),
+            (0, "duration_seconds", 12), (0, "path", "../../etc/passwd"),
+            (0, "path", "https://example.com/ad.mp4"),
+            (0, "rights", {"license": "commercial", "commercial_use": False,
+                            "source": "unknown", "evidence": "none"}),
+        ]
+        for position, field, value in variations:
+            with self.subTest(field=field, value=value):
+                clips = [dict(item) for item in self.clips]
+                clips[position][field] = value
+                with patch("premium_compose.subprocess.run") as mock_run, \
+                     patch("premium_compose._check_input_clip"):
+                    with self.assertRaises(PremiumComposeError):
+                        compose_approved_clips(shop_id=SHOP, clips=clips,
+                            asset_root=self.assets, output=self.output)
+                    mock_run.assert_not_called()
+
+    def test_real_preflight_rejects_tampered_mp4_instead_of_reencoding(self):
+        # Exercise the REAL ffprobe; mocking subprocess.run also accidentally
+        # mocks the internal subprocess.check_output helper.
+        with self.assertRaises(PremiumComposeError):
+            compose_approved_clips(shop_id=SHOP, clips=self.clips,
+                asset_root=self.assets, output=self.output)
+        self.assertFalse(self.output.exists())
+
+    def test_music_must_be_licensed_and_from_same_shop(self):
+        audio = self.assets / "background.wav"
+        audio.write_bytes(b"audio-test")
+        music = {"shop_id": OTHER, "asset_id": "music", "path": "background.wav",
+                 "rights": RIGHTS}
+        with self.assertRaises(PremiumComposeError):
+            self.render(music=music)
+        music["shop_id"] = SHOP
+        music["rights"] = dict(RIGHTS, commercial_use=False)
+        with self.assertRaises(PremiumComposeError):
+            self.render(music=music)
+        music["rights"] = RIGHTS
+        _, commands = self.render(music=music)
+        self.assertIn(str(audio), commands[0])
+        self.assertNotIn("anullsrc", " ".join(commands[0]))
+
+    def test_no_unsafe_output_into_staged_assets(self):
+        with self.assertRaises(PremiumComposeError):
+            compose_approved_clips(shop_id=SHOP, clips=self.clips,
+                asset_root=self.assets, output=self.assets / "clip1.mp4")
+        self.assertTrue((self.assets / "clip1.mp4").exists())
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

### tests/media/test_premium_compose_real.py
~~~~diff
@@ -0,0 +1,105 @@
+"""Actual offline 30-second Wan-style clip assembly using self-generated FFmpeg media.
+
+No paid provider, external network, user media or credentials are accessed.
+The synthetic 15-second inputs simulate already-imported private H.264 clips.
+"""
+import shutil
+import subprocess
+import sys
+import tempfile
+import unittest
+from pathlib import Path
+
+REPO = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(REPO / "video-engine"))
+from premium_compose import compose_approved_clips, select_render_mode
+from probe import verify_reel
+
+
+class RealPremiumCompositionSmoke(unittest.TestCase):
+    def test_real_30_second_licensed_clip_assembly_with_owned_test_tone(self):
+        # CI is responsible for installing the codecs and must fail, not skip,
+        # if it cannot actually produce or probe the target media.
+        for command in ("ffmpeg", "ffprobe"):
+            self.assertIsNotNone(shutil.which(command), command)
+        shop = "123e4567-e89b-42d3-a456-426614174001"
+        with tempfile.TemporaryDirectory(prefix="p3-real-ffmpeg-") as workspace:
+            root = Path(workspace)
+            private = root / "tenant-staged"
+            private.mkdir()
+            clips = []
+            for index, color in enumerate(("red", "blue"), start=1):
+                filename = f"ai-import-{index}.mp4"
+                absolute = private / filename
+                subprocess.run([
+                    "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
+                    "-f", "lavfi", "-i",
+                    f"color=c={color}:s=720x1280:r=12:d=15",
+                    "-t", "15", "-an", "-c:v", "libx264",
+                    "-preset", "ultrafast", "-pix_fmt", "yuv420p",
+                    "-movflags", "+faststart", str(absolute)
+                ], check=True, capture_output=True, text=True, timeout=120)
+                clips.append({
+                    "shop_id": shop, "asset_id": f"self-generated-{index}",
+                    "provider": "alibaba-wan", "status": "SUCCEEDED",
+                    "duration_seconds": 15, "path": filename,
+                    "rights": {
+                        "license": "owned", "commercial_use": True,
+                        "source": "FFmpeg synthetic offline fixture",
+                        "evidence": "Generated by this local test; no third-party source",
+                    },
+                })
+
+            music_path = private / "owned-fixture-tone.wav"
+            subprocess.run([
+                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
+                "-f", "lavfi", "-i",
+                "sine=frequency=440:sample_rate=44100:duration=30",
+                "-c:a", "pcm_s16le", str(music_path)
+            ], check=True, capture_output=True, text=True, timeout=45)
+            music = {
+                "shop_id": shop, "asset_id": "owned-test-tone",
+                "path": music_path.name,
+                "rights": {
+                    "license": "owned", "commercial_use": True,
+                    "source": "FFmpeg sine synthetic fixture",
+                    "evidence": "Local CI test tone is generated, never marketed as music",
+                },
+            }
+
+            output = root / "outputs" / "premium-30s.mp4"
+            self.assertEqual(select_render_mode(), "ffmpeg")
+            result = compose_approved_clips(
+                shop_id=shop, clips=clips, asset_root=private,
+                output=output, licensed_music=music, width=720,
+                height=1280, fps=12, preset="ultrafast")
+            independent = verify_reel(output, 720, 1280)
+            self.assertTrue(output.is_file())
+            self.assertGreater(output.stat().st_size, 10_000)
+            self.assertAlmostEqual(result["duration_seconds"], 30, delta=.12)
+            self.assertAlmostEqual(independent["duration_seconds"], 30, delta=.12)
+            self.assertEqual(independent["video_codec"], "h264")
+            self.assertEqual(independent["audio_codec"], "aac")
+
+            # Decode one real image from each half of the completed output.
+            # This proves sequential clips are included, not just a valid
+            # 30-second file with a duplicated or blank first clip.
+            def frame_rgb(seconds):
+                raw = subprocess.check_output([
+                    "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
+                    "-ss", str(seconds), "-i", str(output), "-frames:v", "1",
+                    "-vf", "scale=1:1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
+                ], timeout=30)
+                self.assertEqual(len(raw), 3)
+                return tuple(raw)
+            red_frame = frame_rgb(5)
+            blue_frame = frame_rgb(25)
+            self.assertGreater(red_frame[0], red_frame[2] + 70)
+            self.assertGreater(blue_frame[2], blue_frame[0] + 70)
+
+            # The test's output is discarded with the temporary directory;
+            # do not publish this synthetic render as a real Wan example.
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

### tests/reliability/test_premium_outbox.py
~~~~diff
@@ -0,0 +1,154 @@
+"""Offline-only premium UUID queue and at-least-once recovery safety checks."""
+import hashlib
+import sys
+from pathlib import Path
+
+import pytest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
+                       "azure-functions" / "campaign-api"))
+from premium_queue import AzurePremiumQueue, PREMIUM_QUEUE_NAME
+from premium_outbox import (
+    PremiumRuntimeDisabled, dispatch_premium_outbox, record_premium_poison,
+    reconcile_premium_and_dispatch,
+)
+from tenant_store import StorageUnavailable
+
+JID = "123e4567-e89b-42d3-a456-426614174001"
+EID = "123e4567-e89b-42d3-a456-426614174002"
+LEASE = "123e4567-e89b-42d3-a456-426614174003"
+
+
+class QueueClient:
+    def __init__(self, fail=False):
+        self.sent = []
+        self.fail = fail
+
+    def send_message(self, message):
+        self.sent.append(message)
+        if self.fail:
+            raise RuntimeError("Ambiguous Azure Queue response")
+
+
+class Store:
+    def __init__(self, events=None):
+        self.events = ([{"id": EID, "kind": "premium_video",
+                         "lease_token": LEASE, "job_id": JID}]
+                       if events is None else events)
+        self.calls = []
+        self.good = True
+    def claim_outbox(self, limit):
+        self.calls.append(("claim", limit))
+        return self.events
+    def confirm_outbox(self, event_id, lease, sent):
+        self.calls.append(("confirm", event_id, lease, sent))
+        if not self.good:
+            raise StorageUnavailable("Unconfirmed outbox receipt")
+    def record_poison(self, kind, digest, jid):
+        self.calls.append(("poison", kind, digest, jid))
+        return self.good
+    def reconcile(self):
+        self.calls.append(("reconcile",))
+        return {"review_required": 0, "safe_to_replay": 1}
+
+
+def test_sender_never_provisions_queue_and_sends_only_canonical_uuid():
+    client = QueueClient()
+    queue = AzurePremiumQueue(client=client)
+    assert PREMIUM_QUEUE_NAME == "retail-premium-video"
+    queue.enqueue(JID)
+    assert client.sent == [JID]
+    for invalid in ("other-shop", "../malicious", "https://example.com",
+                    JID.upper(), "token:purchased"):
+        with pytest.raises(ValueError):
+            queue.enqueue(invalid)
+    assert client.sent == [JID]
+    with pytest.raises(ValueError):
+        AzurePremiumQueue()
+
+
+def test_disabled_outbox_never_claims_or_sends():
+    store, client = Store(), QueueClient()
+    with pytest.raises(PremiumRuntimeDisabled):
+        dispatch_premium_outbox(store, AzurePremiumQueue(client=client))
+    assert store.calls == [] and client.sent == []
+
+
+def test_claim_then_send_one_uuid_and_cas_confirm():
+    store, client = Store(), QueueClient()
+    count = dispatch_premium_outbox(
+        store, AzurePremiumQueue(client=client), enabled=True)
+    assert count == 1 and client.sent == [JID]
+    assert store.calls == [
+        ("claim", 20), ("confirm", EID, LEASE, True)]
+
+
+def test_uncertain_queue_send_is_not_a_success_and_outbox_remains_replayable():
+    store, client = Store(), QueueClient(fail=True)
+    result = dispatch_premium_outbox(
+        store, AzurePremiumQueue(client=client), enabled=True)
+    assert result == 0 and client.sent == [JID]
+    assert store.calls[-1] == ("confirm", EID, LEASE, False)
+
+
+def test_failed_cas_confirm_raises_even_if_azure_may_have_accepted_message():
+    store, client = Store(), QueueClient()
+    store.good = False
+    with pytest.raises(StorageUnavailable):
+        dispatch_premium_outbox(
+            store, AzurePremiumQueue(client=client), enabled=True)
+    assert client.sent == [JID]
+
+
+@pytest.mark.parametrize("bad_event", [
+    {"id": EID, "kind": "render", "lease_token": LEASE, "job_id": JID},
+    {"id": EID, "kind": "premium_video", "lease_token": LEASE,
+     "job_id": "123e4567-e89b-42d3-a456-426614174999;secret"},
+    {"id": "bad", "kind": "premium_video", "lease_token": LEASE, "job_id": JID},
+    {"id": EID, "kind": "premium_video", "lease_token": "bad", "job_id": JID},
+    {"id": EID, "kind": "premium_video", "lease_token": LEASE},
+])
+def test_invalid_tenant_outbox_event_never_sends_to_queue(bad_event):
+    store, client = Store([bad_event]), QueueClient()
+    with pytest.raises(StorageUnavailable):
+        dispatch_premium_outbox(
+            store, AzurePremiumQueue(client=client), enabled=True)
+    assert client.sent == []
+
+
+def test_poison_hash_only_and_no_job_change_with_malformed_payload():
+    store = Store()
+    assert record_premium_poison(store, JID.encode(), enabled=True) == JID
+    assert store.calls[-1] == (
+        "poison", "premium_video", hashlib.sha256(JID.encode()).hexdigest(), JID)
+    body = b"foreign-token-or-unsafe-payload"
+    assert record_premium_poison(store, body, enabled=True) is None
+    assert store.calls[-1][-1] is None
+    with pytest.raises(PremiumRuntimeDisabled):
+        record_premium_poison(store, b"invalid")
+    with pytest.raises(ValueError):
+        record_premium_poison(store, b"A" * 65537, enabled=True)
+    store.good = False
+    with pytest.raises(StorageUnavailable):
+        record_premium_poison(store, JID.encode(), enabled=True)
+
+
+def test_reconciler_runs_before_db_outbox_and_never_contacts_wan_directly():
+    store, client = Store(), QueueClient()
+    response = reconcile_premium_and_dispatch(
+        store, AzurePremiumQueue(client=client), enabled=True)
+    assert response == {
+        "reconciliation": {"review_required": 0, "safe_to_replay": 1},
+        "dispatched": 1}
+    assert store.calls[0] == ("reconcile",)
+    assert store.calls[-1] == ("confirm", EID, LEASE, True)
+    assert client.sent == [JID]
+
+
+@pytest.mark.parametrize("limit", [0, -1, True, 51, "20"])
+def test_invalid_batch_limit_fail_closed_before_touching_store(limit):
+    store, client = Store(), QueueClient()
+    with pytest.raises(ValueError):
+        dispatch_premium_outbox(
+            store, AzurePremiumQueue(client=client), enabled=True, limit=limit)
+    assert not store.calls and not client.sent
~~~~

### tests/reliability/test_premium_poll_completion.py
~~~~diff
@@ -0,0 +1,188 @@
+"""Part 3: offline provider poll -> private importer, never a paid API call."""
+from __future__ import annotations
+
+from io import BytesIO
+from pathlib import Path
+import sys
+import pytest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
+                       "azure-functions" / "campaign-api"))
+from premium_poll_completion import PremiumPollCompletion, PremiumCompletionError
+
+SID = "123e4567-e89b-42d3-a456-426614174001"
+JID = "123e4567-e89b-42d3-a456-426614174002"
+LEASE = "123e4567-e89b-42d3-a456-426614174003"
+ASSET = "123e4567-e89b-42d3-a456-426614174004"
+TASK = "provider-task-123456"
+URL = "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/clip.mp4?Expires=9999999999"
+MP4 = bytes.fromhex("00000018667479706d703432") + b"A" * 2100
+
+
+class Store:
+    def __init__(self):
+        self.claims = 0
+        self.finalizations = []
+        self.claim = {"id": JID, "shop_id": SID, "attempt_token": LEASE,
+                      "status": "IMPORTING", "reservation_confirmed": True,
+                      "seconds": 5, "provider_task_id": TASK}
+        self.complete = True
+
+    def claim_import(self, job_id):
+        self.claims += 1
+        assert job_id == JID
+        return self.claim
+
+    def finalize(self, job_id, shop_id, token, path):
+        self.finalizations.append((job_id, shop_id, token, path))
+        return ({"status": "SUCCEEDED", "output_asset_id": ASSET}
+                if self.complete else {"status": "FAILED"})
+
+
+class Provider:
+    def __init__(self, status="SUCCEEDED", url=URL):
+        self.calls = []
+        self.status, self.url = status, url
+
+    def poll_private(self, task_id):
+        self.calls.append(task_id)
+        result = {"task_id": task_id, "status": self.status}
+        if self.status == "SUCCEEDED":
+            result["video_url"] = self.url
+        return result
+
+
+class Response:
+    status = 200
+    headers = {"Content-Type": "video/mp4",
+               "Content-Length": str(len(MP4))}
+
+    def __init__(self):
+        self.stream = BytesIO(MP4)
+
+    def read(self, size=-1):
+        return self.stream.read(size)
+
+    def __enter__(self):
+        return self
+
+    def __exit__(self, *args):
+        pass
+
+
+class Opener:
+    def __init__(self):
+        self.calls = []
+
+    def open(self, request, timeout):
+        self.calls.append(request.full_url)
+        return Response()
+
+
+class Media:
+    def __init__(self):
+        self.uploads = []
+
+    def upload(self, shop_id, job_id, path, *, lease_token):
+        self.uploads.append((shop_id, job_id, lease_token, Path(path).stat().st_size))
+        return f"{shop_id}/renders/{job_id}/{lease_token}.mp4"
+
+
+def probe(_path):
+    return {"format": {"duration": "5.0"},
+            "streams": [{"codec_type": "video", "codec_name": "h264",
+                         "width": 720, "height": 1280}]}
+
+
+def construct(store=None, provider=None, media=None, opener=None, *, enabled=True):
+    store, provider, media, opener = (
+        store or Store(), provider or Provider(), media or Media(), opener or Opener()
+    )
+    return (PremiumPollCompletion(store, provider, media, enabled=enabled,
+                                  probe=probe, opener=opener),
+            store, provider, media, opener)
+
+
+def test_disabled_by_default_never_claims_or_contacts_provider():
+    worker, store, provider, media, opener = construct(enabled=False)
+    with pytest.raises(PremiumCompletionError, match="disabled"):
+        worker.run_once(JID)
+    assert store.claims == 0 and provider.calls == [] and opener.calls == []
+
+
+def test_successful_provider_poll_imports_once_and_returns_only_private_asset():
+    worker, store, provider, media, opener = construct()
+    result = worker.run_once(JID)
+    assert result == {"job_id": JID, "status": "SUCCEEDED", "output_asset_id": ASSET}
+    assert provider.calls == [TASK] and opener.calls == [URL]
+    assert media.uploads == [(SID, JID, LEASE, len(MP4))]
+    assert store.finalizations == [
+        (JID, SID, LEASE, f"{SID}/renders/{JID}/{LEASE}.mp4")]
+    assert "video_url" not in result and "provider_task_id" not in result
+
+
+def test_stale_claim_avoids_provider_contact_or_upload():
+    worker, store, provider, media, opener = construct()
+    store.claim = None
+    assert worker.run_once(JID) == {"job_id": JID, "status": "NOT_CLAIMED"}
+    assert provider.calls == [] and media.uploads == []
+
+
+@pytest.mark.parametrize("change", [
+    {"reservation_confirmed": False}, {"status": "PENDING"},
+    {"attempt_token": "foreign-tenant"}, {"shop_id": "other-tenant"},
+    {"id": SID}, {"seconds": 18}, {"provider_task_id": "bad"},
+])
+def test_broken_fence_tenant_or_reservation_prevents_network(change):
+    worker, store, provider, media, opener = construct()
+    store.claim.update(change)
+    with pytest.raises(PremiumCompletionError, match="claim is invalid"):
+        worker.run_once(JID)
+    assert provider.calls == [] and media.uploads == []
+
+
+@pytest.mark.parametrize("status,expected", [
+    ("PENDING", "AWAITING_PROVIDER"),
+    ("RUNNING", "AWAITING_PROVIDER"),
+    ("FAILED", "RECONCILE"),
+    ("CANCELED", "RECONCILE"),
+    ("UNKNOWN", "RECONCILE"),
+])
+def test_non_success_does_not_import_or_resubmit(status, expected):
+    worker, store, provider, media, opener = construct(provider=Provider(status))
+    assert worker.run_once(JID) == {"job_id": JID, "status": expected}
+    assert provider.calls == [TASK]
+    assert media.uploads == [] and opener.calls == []
+
+
+@pytest.mark.parametrize("bad_url", [
+    "https://evil.example/path.mp4?Expires=9999999999",
+    "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/a.mp4?Expires=1",
+    "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/a.mp4?Expires=foo",
+    "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/a.mp4?Expires=9999999999&Expires=9999999999",
+])
+def test_invalid_or_expired_provider_url_is_never_downloaded(bad_url):
+    worker, store, provider, media, opener = construct(provider=Provider(url=bad_url))
+    with pytest.raises(PremiumCompletionError) as info:
+        worker.run_once(JID)
+    assert bad_url not in str(info.value)
+    assert media.uploads == [] and opener.calls == []
+
+
+def test_rejected_database_finalization_does_not_claim_success():
+    worker, store, provider, media, opener = construct()
+    store.complete = False
+    with pytest.raises(PremiumCompletionError):
+        worker.run_once(JID)
+    assert len(media.uploads) == 1 and len(store.finalizations) == 1
+
+
+def test_unexpected_provider_response_is_sanitized_and_not_uploaded():
+    class BadProvider:
+        def poll_private(self, task):
+            raise ValueError("secret signed URL and key")
+    worker, store, provider, media, opener = construct(provider=BadProvider())
+    with pytest.raises(PremiumCompletionError) as info:
+        worker.run_once(JID)
+    assert "secret" not in str(info.value) and opener.calls == []
+    assert store.finalizations == []
~~~~

### tests/reliability/test_premium_private_import.py
~~~~diff
@@ -0,0 +1,171 @@
+"""Part 3 private media delivery tests; no provider network or real cloud writes."""
+from io import BytesIO
+from unittest.mock import patch
+from pathlib import Path
+import sys
+import pytest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
+                       "azure-functions" / "campaign-api"))
+from premium_private_import import (
+    NoRedirect, PremiumImportError, validate_vendor_video_url,
+    fetch_signed_video, verify_video, probe_mp4, import_to_private_storage, MAX_BYTES,
+)
+
+SID = "123e4567-e89b-42d3-a456-426614174001"
+JID = "123e4567-e89b-42d3-a456-426614174002"
+LEASE = "123e4567-e89b-42d3-a456-426614174003"
+ASSET = "123e4567-e89b-42d3-a456-426614174004"
+URL = "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/some/clip.mp4?Expires=9999999999"
+MP4 = bytes.fromhex("00000018667479706d703432") + (b"0" * 2100)
+
+class Response:
+    def __init__(self, data=MP4, *, content_type="video/mp4", status=200, length=None):
+        self.stream = BytesIO(data)
+        self.headers = {"Content-Type": content_type,
+                        "Content-Length": str(len(data) if length is None else length)}
+        self.status = status
+    def read(self, n=-1): return self.stream.read(n)
+    def __enter__(self): return self
+    def __exit__(self, *args): pass
+
+class Transport:
+    def __init__(self, response=None):
+        self.calls = []
+        self.response = response or Response()
+    def open(self, req, timeout):
+        self.calls.append((req.full_url, timeout))
+        return self.response
+
+class Media:
+    def __init__(self): self.calls = []
+    def upload(self, shop, job, file, *, lease_token):
+        self.calls.append((shop, job, lease_token, Path(file).stat().st_size))
+        return f"{shop}/renders/{job}/{lease_token}.mp4"
+
+class Store:
+    def __init__(self, success=True): self.calls = []; self.success = success
+    def finalize(self, job, shop, token, path):
+        self.calls.append((job, shop, token, path))
+        return {"status":"SUCCEEDED","output_asset_id":ASSET} if self.success else {"status":"FAILED"}
+
+def probe(_):
+    return {"format":{"duration":"5.02"},
+            "streams":[{"codec_type":"video","codec_name":"h264",
+                        "width":720,"height":1280}]}
+
+def test_official_alibaba_video_download_example_is_allowed():
+    # Official Alibaba Wan2.7 I2V API docs return this OSS hostname shape.
+    url = "https://dashscope-a717.oss-accelerate.aliyuncs.com/demo.mp4?Expires=9999999999"
+    assert validate_vendor_video_url(url) == url
+
+
+def test_approved_signed_vendor_origin_is_not_client_storage_url():
+    assert validate_vendor_video_url(URL) == URL
+    assert NoRedirect().redirect_request(None, None, 302, "", {}, "http://169.254.169.254") is None
+
+@pytest.mark.parametrize("bad", [
+    "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/video.mp4?Expires=99",
+    "https://169.254.169.254/meta.mp4?Expires=99",
+    "https://127.0.0.1/video.mp4?Expires=99",
+    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com.evil.invalid/x.mp4?Expires=99",
+    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com:8443/x.mp4?Expires=99",
+    "https://evil@dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/x.mp4?Expires=99",
+    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/x.mp4",
+    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/../x.mp4?Expires=99",
+    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/x.html?Expires=99",
+    "https://jeearzffnjbvghwjjjrf.supabase.co/storage/v1/object/public/b/x.mp4?Expires=99",
+])
+def test_output_origin_rejects_redirects_and_ssrf(bad):
+    with pytest.raises(PremiumImportError):
+        validate_vendor_video_url(bad)
+
+def test_private_clip_is_downloaded_in_bounded_chunks(tmp_path):
+    target = tmp_path / "media.mp4"
+    transport = Transport()
+    assert fetch_signed_video(URL, target, opener=transport) == len(MP4)
+    assert target.read_bytes() == MP4
+    assert len(transport.calls) == 1
+
+def test_failed_size_or_content_type_never_creates_media(tmp_path):
+    cases = [Response(content_type="text/html"), Response(length=MAX_BYTES+1),
+             Response(data=b"hi"), Response(data=b"X"*2100)]
+    for response in cases:
+        with pytest.raises(PremiumImportError):
+            fetch_signed_video(URL, tmp_path / "media.mp4",
+                               opener=Transport(response))
+
+def test_codec_duration_and_dimensions_must_match_reserved_job():
+    verify_video(probe(None), expected_seconds=5)
+    invalid = [
+        ({"format":{"duration":5},"streams":[{"codec_type":"video","codec_name":"hevc",
+          "width":720,"height":1280}]},5),
+        (probe(None),10),
+        ({"format":{"duration":5},"streams":[{"codec_type":"video","codec_name":"h264",
+          "width":1919,"height":1080}]},5),
+    ]
+    for metadata, seconds in invalid:
+        with pytest.raises(PremiumImportError):
+            verify_video(metadata, expected_seconds=seconds)
+
+def test_private_output_and_db_fenced_completion_are_required():
+    transport, media, store = Transport(), Media(), Store()
+    result = import_to_private_storage(
+        provider_url=URL, shop_id=SID, job_id=JID, lease_token=LEASE,
+        expected_seconds=5, media=media, store=store, opener=transport,
+        probe=probe
+    )
+    assert result == {"job_id":JID, "status":"SUCCEEDED","output_asset_id":ASSET}
+    assert media.calls[0][:3] == (SID, JID, LEASE)
+    assert store.calls[0][3] == f"{SID}/renders/{JID}/{LEASE}.mp4"
+    assert "url" not in result
+
+def test_failed_db_finalization_is_not_misrepresented_as_video_ready():
+    media, store = Media(), Store(success=False)
+    with pytest.raises(PremiumImportError):
+        import_to_private_storage(
+            provider_url=URL, shop_id=SID, job_id=JID, lease_token=LEASE,
+            expected_seconds=5, media=media, store=store,
+            opener=Transport(), probe=probe)
+    assert len(media.calls)==1 and len(store.calls)==1
+
+
+@pytest.mark.parametrize("returned_path", [
+    f"{SID}/renders/{JID}/{LEASE}-evil.mp4",
+    f"{SID}/renders/{JID}/{LEASE}.mp4/subdir",
+    f"{SID}/renders/{JID}/{LEASE}.MP4",
+    f"{SID}/renders/{JID}/{LEASE}",
+    f"{SID}/renders/other/{LEASE}.mp4",
+    f"{SID}/renders/{JID}/{LEASE}.mp4?token=malicious",
+])
+def test_private_upload_receipt_must_equal_exact_fenced_object(returned_path):
+    class SuspiciousMedia(Media):
+        def upload(self, shop, job, file, *, lease_token):
+            self.calls.append((shop, job, lease_token))
+            return returned_path
+    media, store = SuspiciousMedia(), Store()
+    with pytest.raises(PremiumImportError, match="receipt mismatch"):
+        import_to_private_storage(
+            provider_url=URL, shop_id=SID, job_id=JID, lease_token=LEASE,
+            expected_seconds=5, media=media, store=store,
+            opener=Transport(), probe=probe)
+    assert len(media.calls) == 1
+    assert store.calls == []
+
+
+def test_ffprobe_cannot_read_remote_protocol_references(tmp_path):
+    """Even a crafted uploaded MP4 cannot make ffprobe open HTTP/HTTPS."""
+    target = tmp_path / "provider-output.mp4"
+    target.write_bytes(MP4)
+    class ProbeResult:
+        stdout = '{"format":{"duration":"5"},"streams":[]}'
+    with patch("premium_private_import.subprocess.run",
+               return_value=ProbeResult()) as execute:
+        assert probe_mp4(target)["format"]["duration"] == "5"
+    args = execute.call_args.args[0]
+    assert args[:5] == [
+        "ffprobe", "-v", "error", "-protocol_whitelist", "file"
+    ]
+    assert args[-1] == str(target)
+    assert execute.call_args.kwargs["timeout"] == 30
+    assert execute.call_args.kwargs["check"] is True
~~~~

### tests/reliability/test_premium_worker.py
~~~~diff
@@ -0,0 +1,138 @@
+"""Offline lifecycle tests; no Azure, Supabase, or paid provider network calls."""
+import sys
+from pathlib import Path
+import pytest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
+from premium_worker import Claim, PremiumJobWorker, PremiumLifecycleError
+
+JID = "123e4567-e89b-42d3-a456-426614174000"
+SID = "223e4567-e89b-42d3-a456-426614174000"
+TID = "323e4567-e89b-42d3-a456-426614174000"
+AID = "423e4567-e89b-42d3-a456-426614174000"
+
+
+class Store:
+    def __init__(self, mode="text"):
+        self.claim = Claim(JID, SID, TID, mode, "Produce a short boutique video",
+                           5, "720P", 0.50,
+                           asset_id=AID if mode == "image" else None)
+        self.state = "QUEUED"
+        self.events = []
+        self.ack = True
+
+    def claim_queued(self, jid):
+        self.events.append("claim")
+        return self.claim if jid == JID and self.state == "QUEUED" else None
+
+    def mark_submitting(self, jid, token):
+        if jid != JID or token != TID or self.state != "QUEUED":
+            return False
+        self.state = "SUBMITTING"
+        self.events.append("submitting")
+        return True
+
+    def mark_pending(self, jid, token, provider_task_id):
+        self.events.append("ack")
+        if not self.ack or jid != JID or token != TID:
+            return False
+        self.state = "PENDING"
+        self.provider_task_id = provider_task_id
+        return True
+
+    def mark_unknown(self, jid, token):
+        if jid != JID or token != TID or self.state != "SUBMITTING":
+            return False
+        self.state = "UNKNOWN"
+        self.events.append("unknown")
+        return True
+
+
+class Provider:
+    def __init__(self, *, outcome=None):
+        self.calls = 0
+        self.outcome = outcome
+
+    def estimated_usd(self, spec):
+        return spec.duration_seconds * (0.10 if spec.resolution == "720P" else 0.15)
+
+    def submit(self, spec):
+        self.calls += 1
+        self.last_spec = spec
+        if isinstance(self.outcome, Exception):
+            raise self.outcome
+        return self.outcome or {"status": "PENDING", "task_id": "abc-defghi-123456"}
+
+
+def test_disabled_does_not_claim_or_incur_provider_cost():
+    store, provider = Store(), Provider()
+    with pytest.raises(PremiumLifecycleError, match="disabled"):
+        PremiumJobWorker(store, provider).submit_queued(JID)
+    assert provider.calls == 0 and store.events == []
+
+
+def test_successful_queued_to_pending_and_replay_is_not_new_post():
+    store, provider = Store(), Provider()
+    worker = PremiumJobWorker(store, provider, enabled=True)
+    assert worker.submit_queued(JID)["status"] == "PENDING"
+    assert store.state == "PENDING" and provider.calls == 1
+    assert store.provider_task_id == "abc-defghi-123456"
+    assert worker.submit_queued(JID)["status"] == "ALREADY_CLAIMED"
+    assert provider.calls == 1
+
+
+def test_uncertain_provider_submit_is_not_retried():
+    store, provider = Store(), Provider(outcome=TimeoutError("response lost"))
+    worker = PremiumJobWorker(store, provider, enabled=True)
+    assert worker.submit_queued(JID)["status"] == "UNKNOWN"
+    assert worker.submit_queued(JID)["status"] == "ALREADY_CLAIMED"
+    assert provider.calls == 1 and store.state == "UNKNOWN"
+
+
+def test_failed_db_ack_never_reposts_after_provider_acceptance():
+    store, provider = Store(), Provider()
+    store.ack = False
+    worker = PremiumJobWorker(store, provider, enabled=True)
+    with pytest.raises(PremiumLifecycleError, match="acknowledgment"):
+        worker.submit_queued(JID)
+    assert store.state == "SUBMITTING"
+    assert worker.submit_queued(JID)["status"] == "ALREADY_CLAIMED"
+    assert provider.calls == 1
+
+
+def test_provider_cost_never_exceeds_atomic_reservation():
+    store, provider = Store(), Provider()
+    store.claim = Claim(JID, SID, TID, "text", "Brand-safe video",
+                        5, "1080P", 0.50)
+    worker = PremiumJobWorker(store, provider, enabled=True)
+    assert worker.submit_queued(JID)["status"] == "UNKNOWN"
+    assert provider.calls == 0
+
+
+def test_image_mode_requires_signed_resolver_before_provider():
+    store, provider = Store(mode="image"), Provider()
+    worker = PremiumJobWorker(store, provider, enabled=True)
+    assert worker.submit_queued(JID)["status"] == "UNKNOWN"
+    assert provider.calls == 0
+
+
+def test_image_resolves_from_server_and_not_user_payload():
+    store, provider = Store(mode="image"), Provider()
+    frame = ("https://jeearzffnjbvghwjjjrf.supabase.co"
+             f"/storage/v1/object/sign/retailgrowth-media/{SID}/images/a.png?token=test")
+    resolver_args = []
+    def resolve(shop, asset):
+        resolver_args.append((shop, asset))
+        return frame
+    worker = PremiumJobWorker(store, provider, enabled=True, resolve_signed_frame=resolve)
+    assert worker.submit_queued(JID)["status"] == "PENDING"
+    assert resolver_args == [(SID, AID)]
+    assert provider.last_spec.signed_first_frame == frame
+    assert provider.last_spec.shop_id == SID
+
+
+def test_invalid_uuid_raises_before_storage_call():
+    store, provider = Store(), Provider()
+    with pytest.raises(ValueError):
+        PremiumJobWorker(store, provider, enabled=True).submit_queued("../other")
+    assert store.events == [] and provider.calls == 0
~~~~

### tests/security/premium_video_ui.test.mjs
~~~~diff
@@ -0,0 +1,45 @@
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import { DEFAULT_VIDEO_ENGINE, PREMIUM_VIDEO_STATUS, premiumVideoChoices,
+         validatePremiumRequest } from '../../frontend/src/features/premium-video/premium-video-model.mjs'
+
+const DID = '123e4567-e89b-42d3-a456-426614174004'
+const AID = '123e4567-e89b-42d3-a456-426614174005'
+
+test('FFmpeg is always the default and premium cannot be selected by default', () => {
+  assert.equal(DEFAULT_VIDEO_ENGINE, 'ffmpeg')
+  assert.equal(PREMIUM_VIDEO_STATUS, 'AWAITING_PROVIDER_AND_CREDIT_APPROVAL')
+  const choices = premiumVideoChoices()
+  assert.equal(choices[0].available, true)
+  assert.equal(choices[1].available, false)
+})
+
+test('frontend feature flag alone is never an entitlement', () => {
+  assert.equal(premiumVideoChoices({ featureEnabled:true })[1].available, false)
+  assert.equal(premiumVideoChoices({ featureEnabled:true, endpointReady:true })[1].available, false)
+  assert.equal(premiumVideoChoices({ featureEnabled:true, entitlement:true })[1].available, false)
+})
+
+test('disabled premium request is rejected even with a valid UUID', () => {
+  assert.throws(() => validatePremiumRequest({
+    day_id:DID,mode:'text',resolution:'720P',duration_seconds:5,input_asset_id:null,
+  }), /not activated/)
+})
+
+test('fully approved contract only admits valid premium input options', () => {
+  const gate = { entitlement:true, endpointReady:true, featureEnabled:true }
+  const input = { day_id:DID,mode:'text',resolution:'720P',duration_seconds:5,input_asset_id:null }
+  assert.deepEqual(validatePremiumRequest(input, gate), input)
+  for (const candidate of [
+    { ...input, day_id:'../escape' },
+    { ...input, duration_seconds:0 },
+    { ...input, duration_seconds:3.5 },
+    { ...input, resolution:'4K' },
+    { ...input, mode:'image', input_asset_id:null },
+    { ...input, mode:'text', input_asset_id:AID },
+  ]) {
+    assert.throws(() => validatePremiumRequest(candidate, gate), /Invalid premium video/)
+  }
+  assert.equal(validatePremiumRequest({ ...input, mode:'image', input_asset_id:AID }, gate)
+               .input_asset_id, AID)
+})
~~~~

### video-engine/premium_compose.py
~~~~diff
@@ -0,0 +1,155 @@
+#!/usr/bin/env python3
+"""Optional, offline FFmpeg assembly of already-imported licensed Wan clips.
+
+This NEVER sends a Wan API request or reserves/charges usage. A trusted worker
+must derive receipts from a tenant-scoped DB query, not from browser JSON.
+FFmpeg standard image renderer is unchanged and remains the free default.
+"""
+from __future__ import annotations
+
+import json
+import math
+import subprocess
+import tempfile
+from pathlib import Path
+
+from render import checked_path, validate_rights, RenderError
+from probe import verify_reel
+from asset_preflight import inspect_staged_audio, AssetPreflightError
+
+MP4 = {".mp4"}
+AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
+MAX_CLIP_BYTES = 80 * 1024 * 1024
+
+
+class PremiumComposeError(RuntimeError):
+    """No raw FFmpeg error output, provider URL or private paths in response."""
+
+
+def _check_input_clip(path, seconds):
+    """Each input was previously imported privately; re-probe local bytes."""
+    try:
+        if path.stat().st_size < 1024 or path.stat().st_size > MAX_CLIP_BYTES:
+            raise ValueError("invalid clip size")
+        result = subprocess.check_output([
+            "ffprobe", "-v", "error", "-protocol_whitelist", "file",
+            "-show_streams", "-show_format",
+            "-of", "json", str(path)
+        ], text=True, timeout=30)
+        info = json.loads(result)
+        videos = [v for v in info["streams"] if v.get("codec_type") == "video"]
+        actual = float(info["format"]["duration"])
+        if (len(videos) != 1 or videos[0].get("codec_name") != "h264" or
+            int(videos[0]["width"]) not in (720, 1080) or
+            int(videos[0]["height"]) not in (1280, 1920) or
+            int(videos[0]["width"]) * 16 != int(videos[0]["height"]) * 9 or
+            not math.isfinite(actual) or abs(actual - seconds) > 0.5):
+            raise ValueError("unsupported clip")
+    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
+        raise PremiumComposeError("Imported clip preflight failed") from None
+
+
+def select_render_mode(*, premium_enabled=False, authorized=False,
+                       all_clips_ready=False):
+    """Free FFmpeg is ALWAYS the default; selection does not incur usage."""
+    if premium_enabled is True and authorized is True and all_clips_ready is True:
+        return "premium"
+    return "ffmpeg"
+
+
+def compose_approved_clips(*, shop_id, clips, asset_root, output,
+                           licensed_music=None, width=1080, height=1920,
+                           fps=24, preset="veryfast"):
+    """Join private clips to exactly 30s H.264/AAC; no customer-provided URLs.
+
+    clips are DB-origin receipt maps: shop_id, asset_id, path, status,
+    provider, duration_seconds and reviewed rights. Source rights, account
+    access, job ownership and billing must ALSO be enforced in the database.
+    licensed_music, if given, is another server-owned rights-bearing asset.
+    """
+    if (not isinstance(shop_id, str) or not shop_id or not isinstance(clips, list)
+        or not 2 <= len(clips) <= 8):
+        raise PremiumComposeError("Invalid premium clip manifest")
+    if ((width, height) not in ((1080, 1920), (720, 1280))
+        or fps not in (12, 15, 24, 25, 30)
+        or preset not in ("ultrafast", "superfast", "veryfast", "faster", "fast")):
+        raise PremiumComposeError("Unsupported premium output preset")
+
+    try:
+        root = Path(asset_root).resolve(strict=True)
+        target = Path(output)
+        if not target.is_absolute():
+            raise ValueError("Output must be a worker-owned absolute path")
+        target = target.resolve()
+        if target.is_relative_to(root):
+            raise ValueError("Never overwrite staged input assets")
+        inputs, intervals = [], []
+        for record in clips:
+            if not isinstance(record, dict):
+                raise ValueError("Invalid clip record")
+            seconds = record.get("duration_seconds")
+            if (record.get("shop_id") != shop_id or
+                record.get("status") != "SUCCEEDED" or
+                record.get("provider") != "alibaba-wan" or
+                not isinstance(record.get("asset_id"), str) or
+                type(seconds) is not int or not 2 <= seconds <= 15):
+                raise ValueError("Untrusted premium clip receipt")
+            validate_rights(record.get("rights"), record["asset_id"])
+            path = checked_path(root, record.get("path"), record["asset_id"], MP4)
+            _check_input_clip(path, seconds)
+            inputs.append(path)
+            intervals.append(seconds)
+        if sum(intervals) != 30:
+            raise ValueError("Premium clips must fill precisely thirty seconds")
+        music_path = None
+        if licensed_music is not None:
+            if not isinstance(licensed_music, dict) or licensed_music.get("shop_id") != shop_id:
+                raise ValueError("Foreign music asset")
+            validate_rights(licensed_music.get("rights"), licensed_music.get("asset_id"))
+            music_path = checked_path(root, licensed_music.get("path"),
+                                      licensed_music.get("asset_id"), AUDIO)
+            inspect_staged_audio(music_path)
+    except (OSError, ValueError, TypeError, RenderError, AssetPreflightError,
+            PremiumComposeError):
+        raise PremiumComposeError("Tenant media, rights or duration preflight failed") from None
+
+    with tempfile.TemporaryDirectory(prefix="retail-premium-compose-") as scratch:
+        temporary = Path(scratch) / "composed.mp4"
+        ff = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
+        for path in inputs:
+            ff += ["-i", str(path)]
+        if music_path is None:
+            ff += ["-f", "lavfi", "-t", "30", "-i",
+                   "anullsrc=channel_layout=stereo:sample_rate=44100"]
+        else:
+            ff += ["-stream_loop", "-1", "-i", str(music_path)]
+        filters = []
+        for i, seconds in enumerate(intervals):
+            filters.append(
+                f"[{i}:v]fps={fps},scale={width}:{height}:"
+                f"force_original_aspect_ratio=decrease,"
+                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
+                f"setsar=1,format=yuv420p,trim=duration={seconds},"
+                f"setpts=PTS-STARTPTS[v{i}]"
+            )
+        joined = "".join(f"[v{i}]" for i in range(len(inputs)))
+        filters.append(f"{joined}concat=n={len(inputs)}:v=1:a=0,"
+                       "fps=" + str(fps) + ",trim=duration=30,"
+                       "setpts=PTS-STARTPTS,format=yuv420p[vout]")
+        ff += ["-filter_complex", ";".join(filters),
+               "-map", "[vout]", "-map", f"{len(inputs)}:a:0",
+               "-af", "atrim=duration=30,asetpts=PTS-STARTPTS,"
+                      "afade=t=out:st=29:d=1",
+               "-t", "30", "-threads", "2", "-c:v", "libx264",
+               "-preset", preset, "-crf", "24", "-pix_fmt", "yuv420p",
+               "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
+               "-movflags", "+faststart", str(temporary)]
+        try:
+            subprocess.run(ff, check=True, capture_output=True, text=True,
+                           timeout=780)
+            info = verify_reel(temporary, width, height)
+            target.parent.mkdir(parents=True, exist_ok=True)
+            temporary.replace(target)
+            return info
+        except (OSError, ValueError, subprocess.SubprocessError):
+            raise PremiumComposeError("Premium FFmpeg assembly failed") from None
~~~~

## Historical archive is NOT source integration
Original #125 can be retired as a superseded draft only after this archive merges with 4/4 PR and exact fresh-main CI; this is never a declaration of actual Wan inference/rights, tenant billing, private media or original task DONE.