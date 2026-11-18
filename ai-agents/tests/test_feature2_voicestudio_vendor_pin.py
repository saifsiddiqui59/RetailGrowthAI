"""Pinned upstream VoiceStudio source integrity (offline, no model downloads)."""
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REVISION = "e5da4aa6461eeea913232bc25be13609e377965c"


def test_vendor_submodule_is_exact_upstream_revision():
    text = (ROOT / ".gitmodules").read_text(encoding="utf-8")
    assert '[submodule "vendor/VoiceStudio"]' in text
    assert "path = vendor/VoiceStudio" in text
    assert "url = https://github.com/debpalash/VoiceStudio.git" in text
    result = subprocess.run(
        ["git", "ls-tree", "HEAD", "vendor/VoiceStudio"],
        cwd=ROOT, capture_output=True, text=True, check=True, timeout=10,
    )
    # A Gitlink references original source without copying or executing it.
    assert result.stdout.strip() == (
        "160000 commit " + SOURCE_REVISION + "\tvendor/VoiceStudio"
    )


def test_documented_source_and_license_boundaries_present():
    text = (ROOT / "vendor" / "VOICESTUDIO_ADOPTION.md").read_text(encoding="utf-8")
    for required in (SOURCE_REVISION, "AGPL-3.0", "CC-BY-NC",
                     "git submodule update --init", "no WineShopPOS"):
        assert required.lower() in text.lower()
