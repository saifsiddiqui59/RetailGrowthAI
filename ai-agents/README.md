# RetailGrowthAI Workstream B — offline campaign drafts

This package implements the frozen docs/INTERFACES_V1.md shape using Python 3.13
standard library only. No Azure resources, live models, external media fetching
or social publishing are invoked.

Example from repository root after uv sync:

    uv run --project ai-agents python -c "from ai_agents.schemas import CampaignBrief; from ai_agents.providers import MockFoundryProvider; from uuid import uuid4; s=str(uuid4()); a=str(uuid4()); req=CampaignBrief.from_dict({'shop_id':s,'brief':'Seven everyday style tips for our clothing boutique','duration_days':7,'start_date':'2026-11-01','timezone':'Asia/Kolkata','language':'en-IN','platforms':['linkedin','instagram'],'media_asset_ids':[a],'offer':None}); result=MockFoundryProvider().generate(req,campaign_id=str(uuid4())); print(len(result['days']))"

Output is exactly seven draft days, including seven LinkedIn text posts,
seven Instagram captions and seven contiguous 30-second storyboard manifests.
The planner does not generate actual images or videos. Media UUIDs are only
references and must be checked against a tenant-authorized media store by the
application boundary before use. Campaign IDs supplied by the caller make
generated content repeatable.

Use:

    uv run --project ai-agents --with pytest -- python -m pytest -q tests/ai

AzureFoundryProvider currently accepts an explicitly injected test callable to
demonstrate future Foundry JSON output validation. With no callable it fails
closed. Do not supply cloud credentials in a client-facing app or in CI.

Reviewer results are kept separately from the canonical JSON:
- impossible timelines, missing keys and wrong tenant IDs are rejected
- offers are only copied from the user's explicit description before expiry
- unapproved discounts and unknown asset references are rejected
- regulated/offer campaigns require human policy or claim approval
- every output stays DRAFT, never scheduled or published

See ai-agents/HANDOFF.md and azure-functions/campaign-api/README.md for
integration gaps to resolve with the coordinator.
