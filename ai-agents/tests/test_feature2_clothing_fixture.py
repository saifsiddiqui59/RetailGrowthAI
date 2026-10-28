"""Cross-feature Pexels discovery-only clothing shop fixture: no fictional rights."""
import json
from pathlib import Path


MANIFEST = (Path(__file__).resolve().parents[1] / "test-fixtures" /
            "clothing-shop-pexels" / "manifest.json")


def test_clothing_shop_reference_catalog_has_genuine_discovery_pages_and_no_forged_assets():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["shop"]["category"] == "clothing"
    assert set(data["usage"]["intended_features"]) >= {2, 3, 4, 5, 7}
    assert data["usage"]["approved_product_identity"] is False
    assert data["usage"]["can_publish"] is False
    assert len(data["source_media"]) >= 4
    assert {r["media_type"] for r in data["source_media"]} == {"IMAGE", "VIDEO"}
    assert len({r["candidate_id"] for r in data["source_media"]}) == len(data["source_media"])
    for row in data["source_media"]:
        assert row["source_page"].startswith("https://www.pexels.com/")
        assert row["license_page"] == "https://www.pexels.com/license/"
        assert row["rights_review_status"].startswith("NOT_IMPORTED")
        assert row["original_sha256"] is None
        assert row["private_storage_ref"] is None
        assert row["purpose"].endswith(("ONLY", "REFERENCE")) is True
