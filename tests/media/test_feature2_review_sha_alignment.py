"""Cross-language cryptographic golden fixture: F2 approved-plan SHA.

The disposable PostgreSQL `feature4_review_cpu_plan` produces the digest from
the same source proposal as Python. NEVER silently turn \\0 into a literal
backslash and 0; this caused a real latent mismatch even though offline
Python consumers were self-consistent.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from feature2_feature4_bridge import direction_review_digest  # noqa: E402

SHOP = "f4000000-0000-4000-8000-000000000001"
CAMPAIGN = "f4100000-0000-4000-8000-000000000001"
ASSET = "f4200000-0000-4000-8000-000000000001"
APPROVAL = "f4300000-0000-4000-8000-000000000001"
PROPOSAL_SHA = "63aa02ddf00c76b7d0e65068dc14176f302d733802731cc7867051b54180b5c4"
REVIEW_SHA = "c59b66bf6402afb634fc383f1b8254f7e19de5a4bafcb14d8cc21b175969e138"


def proposal():
    return {
        "version":"creative_direction_v1","source_feature":"feature2",
        "approved":False,"shop_id":SHOP,"campaign_id":CAMPAIGN,
        "duration_seconds":30,"template":"cinematic","cta":"Visit our studio",
        "script":{"source_feature":"feature2","approved":False,
                  "approved_text":["New arrivals","Visit our studio"],
                  "cta":"Visit our studio"},
        "scenes":[
            {"duration":15,"headline":"New arrivals","asset_id":ASSET,
             "animation_preset":"subtle_zoom","transition":"fade"},
            {"duration":15,"headline":"Visit our studio","asset_id":ASSET,
             "animation_preset":"subtle_zoom","transition":"fade"},
        ],
    }


def test_exact_source_proposal_sha_matches_disposable_sql():
    source = proposal()
    encoded = json.dumps(source,sort_keys=True,separators=(",",":"),
                         ensure_ascii=True).encode()
    assert hashlib.sha256(encoded).hexdigest() == PROPOSAL_SHA


def test_full_review_sha_matches_postgres_nul_domain_separation():
    direction = proposal()
    direction.update(approved=True,approval_id=APPROVAL)
    direction["script"].update(approved=True,approval_id=APPROVAL)
    assert direction_review_digest(direction) == REVIEW_SHA
    direction["review_hash"] = REVIEW_SHA
    assert direction_review_digest(direction) == REVIEW_SHA
    direction["scenes"][0]["headline"] = "Unapproved offer"
    assert direction_review_digest(direction) != REVIEW_SHA
