"""Feature2 professional creative director: optional source-only Azure GPT-4.1-mini adapter.

Reuses the EXISTING AzureFeature2ContentLLM origin validation, conservative
prepaid per-tenant reserve callback and token rates. Its additional Node bridge
runs the actual pinned MIT upstream planning/clock/revision code; no new model,
GPU, OpenRouter, video provider, shop subscription or cloud service.
NOT wired to a public HTTP route; RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED
defaults OFF and verified runtime Node availability is a deployment prerequisite.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

from .feature2_ai_writer import AzureFeature2ContentLLM
from .providers import FoundryUnavailable

def _director_path() -> Path:
    """Resolve checkout and intended Python Functions ZIP without untrusted cwd/env."""
    source = Path(__file__).resolve()
    candidates = (
        source.parent / "creative-director" / "director-cli.js",
        source.parents[2] / "creative-director" / "director-cli.js",
    )
    for cli in candidates:
        root = cli.parent
        if (cli.is_file() and not cli.is_symlink()
            and (root / "director.js").is_file()
            and not (root / "director.js").is_symlink()
            and (root / "upstream" / "LICENSE").is_file()
            and (root / "upstream" / "explainer-plan.js").is_file()
            and (root / "upstream" / "explainer-cues.js").is_file()
            and (root / "upstream" / "explainer-revise.js").is_file()):
            notice = (root / "upstream" / "LICENSE").read_text("utf-8")
            if "MIT License" in notice and "Copyright (c) 2026 Kuble AG" in notice:
                return cli
    raise FoundryUnavailable("Pinned MIT Creative Director sources missing from approved package")
_OUTPUT_BOUNDS = {15: 4200, 30: 8500, 60: 15000}


def _run_director(action: str, payload: dict) -> dict:
    if action not in {"prompt", "compile", "revise"}:
        raise ValueError("Unrecognized creative operation")
    director = _director_path()
    node = shutil.which("node")
    if node is None:
        raise FoundryUnavailable("Pinned source creative planner unavailable: Node runtime missing")
    try:
        serialized = json.dumps(payload, ensure_ascii=False)
        if len(serialized) > 320_000:
            raise ValueError("Creative request too large")
        completed = subprocess.run(
            [node, str(director), action], input=serialized,
            capture_output=True, text=True, timeout=12, check=False,
        )
        if completed.returncode or len(completed.stdout) > 500_000:
            raise ValueError("Creative direction failed validation")
        result = json.loads(completed.stdout)
        if not isinstance(result, dict):
            raise ValueError("Creative planner returned non-object")
        return result
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError, ValueError) as exc:
        raise FoundryUnavailable("Creative director validation failed closed (no automatic retry)") from exc


class AzureFeature2DirectorLLM(AzureFeature2ContentLLM):
    """One opt-in, durably reserved Azure call; never silently retries a charge.

    Only a server JWT/RLS-authorized caller may supply verified source context,
    approved shop media and documented offer approval IDs. This class does not
    grant or verify database rights itself. Callers must enforce the same
    subscription, tenant, atomic budget, and receipt controls used by Feature2.
    """

    def __call__(self, *, verified_brief: dict) -> dict:
        self.last_usage = None
        if os.environ.get("RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED") != "true":
            raise PermissionError("Professional AI director is OFF unless explicitly enabled")
        if not isinstance(verified_brief, dict):
            raise ValueError("Requires authoritative signed server brief")
        # Local pinned OSS preflight BEFORE budget reserve and BEFORE model egress.
        prompts = _run_director("prompt", {"request": verified_brief})
        duration = verified_brief.get("duration_seconds")
        if type(duration) is not int or duration not in _OUTPUT_BOUNDS:
            raise ValueError("Only 15, 30, 60-second source approved briefs")
        if not self._client.configured or len(self._client.api_key) < 8:
            raise FoundryUnavailable("Existing approved Azure model is not configured")
        url = self._client._url()
        output_bound = _OUTPUT_BOUNDS[duration]
        body = json.dumps({
            "model": self._client.deployment,
            "messages": [
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.45,
            "max_tokens": output_bound,
        }, ensure_ascii=False).encode("utf-8")
        input_bound = len(body) + 256
        maximum = (
            Decimal(input_bound) * self._input_rate +
            Decimal(output_bound) * self._output_rate
        ) / 1_000_000
        if maximum > self._cap:
            raise PermissionError("Director plan exceeds approved atomic shop cost cap")
        receipt = self._reserve_cost(float(maximum))
        if not isinstance(receipt, str) or not receipt.strip():
            raise PermissionError("Durable tenant budget reservation rejected")
        try:
            response = self._client._transport(
                url, {"Content-Type": "application/json",
                      "api-key": self._client.api_key,
                      "User-Agent": "RetailGrowthAI-Feature2-Director/1.0"}, body,
            )
            # Capture actual billable usage BEFORE output review. A failed
            # review can still be charged. Caller must settle/journal safely.
            usage = response["usage"]
            p, c = usage["prompt_tokens"], usage["completion_tokens"]
            if (type(p) is not int or type(c) is not int
                or not 1 <= p <= input_bound or not 1 <= c <= output_bound):
                raise ValueError("Provider usage invalid or beyond prepaid bound")
            actual = (Decimal(p) * self._input_rate +
                      Decimal(c) * self._output_rate) / 1_000_000
            if actual > maximum or actual > self._cap:
                raise ValueError("Provider spend beyond approved reservation")
            self.last_usage = {
                "prompt_tokens": p, "completion_tokens": c,
                "actual_cost_usd": float(actual), "reservation_recorded": True,
                "reservation_receipt": receipt,
            }
            choices = response["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError("Expected one reviewed model response")
            choice = choices[0]
            if choice.get("finish_reason") != "stop" or choice["message"].get("refusal") or choice["message"].get("tool_calls"):
                raise ValueError("Refused/truncated/tool-calling completion")
            text = choice["message"]["content"]
            if not isinstance(text, str) or len(text) > 200_000:
                raise ValueError("Model direction too large")
            candidate = json.loads(text)
            # Full upstream-grounded constraints, garment match, exact offer,
            # shot timing and approval review before any outbound asset use.
            return _run_director("compile", {"request": verified_brief, "candidate": candidate})
        except Exception as exc:
            # Single charged attempt can be ambiguous. Never replay.
            raise FoundryUnavailable("Azure director request or creative review failed; no automatic retry") from exc
