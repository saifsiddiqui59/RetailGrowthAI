"""Verify that RetailGrowthAI reuses exact pinned MIT Git blobs, not new algorithms."""
from pathlib import Path
from hashlib import sha1

UPSTREAM_BLOBS = {
    "explainer-plan.js": "610cf8cfcdedd26c2487566a09d2e03c6ad059be",
    "music-video-plan.js": "4f347b4f484710fe31d553b23a570bc63c4cbd04",
    "explainer-cues.js": "6b147079754cf6669ce0c8bf284f72559db8f300",
    "explainer-revise.js": "f5ea858637f252d30cfded24dd23f2e7c9491849",
}


def test_unmodified_kuble_engine_files_have_exact_original_git_blob_hashes():
    source = Path(__file__).resolve().parents[1] / "creative-director"
    notice = (source / "upstream/LICENSE").read_text(encoding="utf8")
    assert "MIT License" in notice
    assert "Copyright (c) 2026 Kuble AG" in notice
    readme = (source / "README.md").read_text(encoding="utf8")
    assert "4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f" in readme
    for name, expected in UPSTREAM_BLOBS.items():
        blob = (source / "upstream" / name).read_bytes()
        actual = sha1(b"blob " + str(len(blob)).encode("ascii") + b"\0" + blob).hexdigest()
        assert actual == expected, f"Vendored original upstream was modified: {name}"
        assert expected in readme
    director = (source / "director.js").read_text(encoding="utf8")
    for module in (
        "./upstream/explainer-plan",
        "./upstream/explainer-cues",
        "./upstream/explainer-revise",
    ):
        assert module in director
    caption = (source / "caption-preview.js").read_text(encoding="utf8")
    assert "./upstream/explainer-cues" in caption
    assert "cues.timingOf" in caption
    assert "cues.parseTiming" in caption
