"""Offline source-only Azure Functions JS path and original-license checks."""
from pathlib import Path
import tempfile
import importlib.util

import pytest

from ai_agents.feature2_director_ai import _director_path
from ai_agents.feature2_director_package import source_entries, REQUIRED, PackageSourceRejected
from ai_agents.feature2_director_runtime_gate import audit_entries

def test_current_dev_checkout_uses_real_pinned_mit_director():
    cli=_director_path()
    assert cli.is_file()
    assert "MIT License" in (cli.parent/"upstream/LICENSE").read_text("utf8")

def test_valid_future_zip_staging_is_still_nonoperational_without_verified_node():
    root=Path(__file__).resolve().parents[2]
    entries=source_entries(root)
    assert REQUIRED.issubset(set(k.removeprefix("ai_agents/creative-director/") for k in entries))
    assert sum(map(len,entries.values())) < 2_000_000
    readiness=audit_entries(entries)
    assert readiness.missing_code==()
    assert readiness.license_verified
    assert not readiness.ready_to_enable
    assert "NODE_RUNTIME_NOT_IN_FUNCTION_ZIP" in readiness.blocking_reasons

def test_actual_current_python_functions_packager_has_not_deployed_js_or_node():
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location("feature2_package_audit",root/"scripts/deploy/package.py")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    files=m.source_files()
    assert "ai_agents/creative-director/director.js" not in files
    assert "bin/node" not in files

def test_fail_closed_on_missing_license_and_malformed_source():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        source=root/"ai-agents/creative-director"
        for rel in REQUIRED:
            p=source/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(("MIT License\nCopyright (c) 2026 Kuble AG\n" if rel=="upstream/LICENSE" else "'use strict';\n"))
        assert len(source_entries(root))==len(REQUIRED)
        (source/"upstream/LICENSE").write_text("proprietary")
        with pytest.raises(PackageSourceRejected,match="attribution"):
            source_entries(root)
        (source/"upstream/LICENSE").unlink()
        with pytest.raises(PackageSourceRejected,match="required"):
            source_entries(root)
