"""F2-19/F2-20 fail-closed one-shot and tenant boundary regression cases."""
from uuid import uuid4
import pytest

from ai_agents.feature2_voicestudio_adapter import VoiceStudioUnavailable
from test_feature2_voicestudio_private_workflow import PrivateHarness, SHOP, CAMPAIGN, JOB


def test_foreign_shop_request_cannot_claim_or_infer():
    h = PrivateHarness()
    with pytest.raises(VoiceStudioUnavailable):
        h.execute(shop_id=str(uuid4()))
    assert h.claimed is False
    assert h.provider_calls == h.write_calls == 0


def test_foreign_campaign_request_cannot_claim_or_infer():
    h = PrivateHarness()
    with pytest.raises(VoiceStudioUnavailable):
        h.execute(campaign_id=str(uuid4()))
    assert h.claimed is False
    assert h.provider_calls == h.write_calls == 0


def test_claim_receipt_cross_tenant_mismatch_never_calls_provider():
    h = PrivateHarness()
    def foreign_claim(shop, campaign, request, digest):
        receipt = h.claim(shop, campaign, request, digest)
        receipt["shop_id"] = str(uuid4())
        return receipt
    with pytest.raises(VoiceStudioUnavailable, match="claim"):
        h.execute(claim_once=foreign_claim)
    assert h.provider_calls == h.write_calls == 0


@pytest.mark.parametrize("field,value", [
    ("campaign_id", str(uuid4())),
    ("request_id", str(uuid4())),
    ("plan_sha256", "0" * 64),
    ("original_sha256", "0" * 64),
    ("render_sha256", "0" * 64),
    ("review_status", "APPROVED_FOR_EDITING"),
    ("publish_approved", True),
    ("commercial_rights_confirmed", False),
    ("private", False),
])
def test_forged_or_approved_receipt_cannot_escape_human_review(field, value):
    h = PrivateHarness()
    def corrupt_receipt(shop, campaign, request):
        receipt = h.read(shop, campaign, request)
        receipt[field] = value
        return receipt
    with pytest.raises(VoiceStudioUnavailable, match="receipt"):
        h.execute(read_private_receipt=corrupt_receipt)
    assert h.provider_calls == h.write_calls == 1
