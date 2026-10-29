"""Coordinator-only guarded Functions runtime manifest regression for issue #650."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"deploy"/"package.py"
spec=importlib.util.spec_from_file_location("issue650_runtime_packager",P)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_versioned_functions_runtime_allowlist_is_complete_and_under_zip_budget():
    source=mod.source_files()
    assert len(source)+3<=120  # FFmpeg, ffprobe and third-party notices
    assert "function_app.py" in source and "host.json" in source
    assert "azure-functions/campaign-api/render_worker.py" in source
    assert "ai_agents/feature2_ai_writer.py" in source
    assert "ai_agents/feature2_llm.py" in source
    assert "ai_agents/prompt_improver.py" in source
    assert mod.verify_runtime_agent_imports(source) is True
    assert all("feature2_kokoro" not in name for name in source)
    assert "ai_agents/feature2_voice_quality.py" not in source


def test_twenty_offline_feature2_modules_do_not_get_accidentally_packaged():
    with tempfile.TemporaryDirectory() as temp:
        home=Path(temp)
        for module in mod.RUNTIME_AGENT_MODULES:
            (home/(module+".py")).write_bytes((mod.AGENTS/(module+".py")).read_bytes())
        for count in range(20):
            (home/("feature2_offline_research_"+str(count)+".py")).write_text(
                "OFFLINE_SOURCE_ONLY=True\n",encoding="utf-8")
        with patch.object(mod,"AGENTS",home):
            entries=mod.source_files()
        assert len(entries)+3<=120
        assert not any("offline_research" in path for path in entries)


def test_new_registered_dependency_cannot_be_silently_excluded():
    candidate=mod.source_files()
    candidate["azure-functions/campaign-api/future_private_voice.py"]=(
        b"from ai_agents.feature2_kokoro_local import synthesize_local\n")
    with pytest.raises(ValueError,match="Undeclared ai_agents runtime import"):
        mod.verify_runtime_agent_imports(candidate)


def test_mandatory_agent_module_cannot_be_missing_or_renamed():
    with tempfile.TemporaryDirectory() as temp:
        home=Path(temp)
        for module in mod.RUNTIME_AGENT_MODULES:
            if module!="schemas":
                (home/(module+".py")).write_bytes((mod.AGENTS/(module+".py")).read_bytes())
        with patch.object(mod,"AGENTS",home):
            with pytest.raises(ValueError):  # fail-closed, including guarded path check
                mod.source_files()


def test_packaged_runtime_imports_fail_if_source_bytes_were_removed():
    candidate=mod.source_files()
    candidate.pop("ai_agents/providers.py")
    with pytest.raises(ValueError,match="Undeclared ai_agents runtime import"):
        mod.verify_runtime_agent_imports(candidate)
