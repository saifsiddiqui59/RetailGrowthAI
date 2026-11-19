"""Source-page/license review must never be interpreted as model or product rights."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1] / "test-fixtures" / "clothing-shop-pexels"

def test_provider_general_license_review_still_blocks_original_asset_import():
    manifest=json.loads((ROOT / "manifest.json").read_text())
    review=json.loads((ROOT / "rights-provider-general-review.json").read_text())
    assert review["provider_commercial_ads_general_license_verified"] is True
    assert review["overall_status"].endswith("PENDING")
    assert {r["candidate_id"] for r in review["source_pages_verified"]} == {
        c["candidate_id"] for c in manifest["source_media"]}
    assert all(item["provider_source_page_exists"] for item in review["source_pages_verified"])
    for item in review["source_pages_verified"]:
        assert item["original_sha256"] is None
        assert item["tenant_storage_receipt"] is None
        assert not item["original_bytes_imported"]
        assert not item["commercial_individual_rights_verified"]
        assert not item["independent_model_release_verified"]
        assert not item["garment_identity_verified"]
        assert not item["can_publish"]
