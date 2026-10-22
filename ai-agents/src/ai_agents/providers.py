"""Foundry-compatible provider boundary; mock never makes outbound requests.

A live client adapter must be supplied explicitly by a later deployment milestone,
with authentication, JSON-output validation, quotas and observability implemented.
"""
from __future__ import annotations
from collections.abc import Callable
from typing import Protocol

from .planner import generate_campaign
from .schemas import CampaignBrief, validate_campaign


class CampaignProvider(Protocol):
    def generate(self, request: CampaignBrief, *, campaign_id: str) -> dict: ...


class MockFoundryProvider:
    """Offline deterministic stand-in; makes no model calls and costs nothing."""

    def generate(self, request: CampaignBrief, *, campaign_id: str) -> dict:
        return generate_campaign(request, campaign_id=campaign_id)


class AzureFoundryProvider:
    """Explicit-injection adapter; cannot silently use a production cloud account."""

    def __init__(self, generate_json: Callable[[CampaignBrief, str], dict] | None = None):
        self._generate_json = generate_json

    def generate(self, request: CampaignBrief, *, campaign_id: str) -> dict:
        if self._generate_json is None:
            raise RuntimeError("Azure AI Foundry is not configured; use MockFoundryProvider for offline tests")
        result = self._generate_json(request, campaign_id)
        validate_campaign(result, expected_count=request.duration_days)
        if result["id"] != campaign_id or result["shop_id"] != request.shop_id:
            raise ValueError("Foundry output does not match requested campaign/shop")
        return result
