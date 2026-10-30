"""The Free SWA no-trend release must verify actual lazy route chunk, not entry JS."""
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/deploy/verify_feature2_lazy_swa.py"
module = runpy.run_path(str(SOURCE))


def test_extracts_route_chunk_from_live_entry_but_not_from_index_text():
    entry = "<html><script type='module' crossorigin src='/assets/index-Abc_123.js'></script></html>"
    assert module["find_entry_js"](entry) == "/assets/index-Abc_123.js"
    main = 'const Z=()=>import("./TrendWorkspace-Def_456.js");'
    assert module["find_lazy_trends_js"](main) == "/assets/TrendWorkspace-Def_456.js"
    assert module["MESSAGE"] not in main
    module["verify_lazy_text"]('const a="Create a standard campaign without a trend"')


@pytest.mark.parametrize("index", [
    "<html></html>",
    "<script src='http://example.com/assets/index-Abc.js'></script>",
    "<script src='/assets/index-A.js'></script><script src='/assets/index-B.js'></script>",
])
def test_missing_or_ambiguous_entry_denied(index):
    with pytest.raises(ValueError):
        module["find_entry_js"](index)


@pytest.mark.parametrize("bundle", [
    "no lazy route chunk",
    'import("./TrendWorkspace-ABC.js");import("./TrendWorkspace-DEF.js")',
])
def test_absent_or_ambiguous_trend_chunk_denied(bundle):
    with pytest.raises(ValueError):
        module["find_lazy_trends_js"](bundle)


def test_never_accepts_missing_fallback_or_fake_trend():
    with pytest.raises(ValueError):
        module["verify_lazy_text"]("unrelated article")
    with pytest.raises(ValueError):
        module["verify_lazy_text"]('Create a standard campaign without a trend; trend_id: evergreen')


def test_live_verification_is_readonly_exact_public_swa():
    source = SOURCE.read_text()
    assert "urllib.request.urlopen" in source
    assert "https://" in source
    assert "purple-dune-06b5da200.2.azurestaticapps.net" in source
    for forbidden in ("method=\"POST\"", "method=\"DELETE\"", "AZURE_CLIENT_SECRET",
                      "RETAIL_SUPABASE_SERVICE_ROLE_KEY", "az login", "supabase db push"):
        assert forbidden not in source
