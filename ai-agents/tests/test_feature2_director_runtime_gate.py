"""Actual Functions source package must reject unbundled Node director."""
import importlib.util
from pathlib import Path

from ai_agents.feature2_director_runtime_gate import audit_entries, REQUIRED, PIN


def test_current_python_flex_packaging_reports_genuine_blocker():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "deploy" / "package.py"
    spec = importlib.util.spec_from_file_location("rg_f2_package_readonly", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entries = module.source_files()
    result = audit_entries(entries)
    assert not result.ready_to_enable
    assert "PINNED_DIRECTOR_SOURCE_NOT_PACKAGED" in result.blocking_reasons
    assert "NODE_RUNTIME_NOT_IN_FUNCTION_ZIP" in result.blocking_reasons
    assert "DEPLOYED_LINUX_NODE22_RUNTIME_UNVERIFIED" in result.blocking_reasons
    assert PIN == "4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f"


def test_fake_node_file_or_ci_node_cannot_claim_live_readiness():
    members = {name: b"'use strict';" for name in REQUIRED}
    members["ai_agents/creative-director/upstream/LICENSE"] = (
        b"MIT License\nCopyright (c) 2026 Kuble AG\n"
    )
    assert not audit_entries(members).ready_to_enable
    members["bin/node"] = b"fake!"
    assert not audit_entries(members).ready_to_enable
    assert not audit_entries(members, runtime_linux_node22_verified=True).ready_to_enable


def test_missing_license_never_readiness():
    members = {name: b"source" for name in REQUIRED}
    members["bin/node"] = b"fake!"
    result = audit_entries(members, runtime_linux_node22_verified=True, operator_approved_runtime=True)
    assert not result.ready_to_enable
    assert "PINNED_MIT_NOTICE_NOT_PACKAGED" in result.blocking_reasons
