"""Fail-closed source-only checks for the isolated six-file F4 DEV SQL bundle."""
import importlib.util
from pathlib import Path
import shutil
import tempfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts" / "deploy" / "feature4_cpu_release_bundle.py"
SPEC = importlib.util.spec_from_file_location("feature4_cpu_release_bundle", MODULE)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


def _copy_candidates(tmp_path):
    for name in bundle.CANDIDATES:
        src = ROOT / name
        dst = tmp_path / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def test_release_bundle_has_one_outer_transaction_and_exact_six_sources():
    sql, receipt = bundle.build_bundle(ROOT)
    assert sql.count("-- SOURCE: supabase/candidates/") == 6
    assert sql.startswith("-- SOURCE-ONLY:")
    assert sql.rstrip().endswith("commit;")
    assert sql.lower().count("\nbegin;") == 1
    assert sql.lower().count("\ncommit;") == 1
    assert "partially installed schema detected" in sql
    assert receipt["expected_dev_project"] == bundle.DEV_PROJECT
    assert receipt["hosted_deployed"] is False
    assert len(receipt["files"]) == 6
    assert {f["path"] for f in receipt["files"]} == set(bundle.CANDIDATES)


def test_release_bundle_rejects_missing_source(tmp_path):
    _copy_candidates(tmp_path)
    (tmp_path / bundle.CANDIDATES[0]).unlink()
    with pytest.raises(bundle.ReleaseGuardError, match="Missing or linked"):
        bundle.build_bundle(tmp_path)


def test_release_bundle_rejects_sql_outside_transaction(tmp_path):
    _copy_candidates(tmp_path)
    candidate = tmp_path / bundle.CANDIDATES[0]
    candidate.write_text(candidate.read_text() + "\nselect 1;\n")
    with pytest.raises(bundle.ReleaseGuardError, match="SQL after COMMIT"):
        bundle.build_bundle(tmp_path)


def test_release_bundle_rejects_nested_begin(tmp_path):
    _copy_candidates(tmp_path)
    candidate = tmp_path / bundle.CANDIDATES[1]
    candidate.write_text(candidate.read_text().replace("begin;", "begin;\nbegin;", 1))
    with pytest.raises(bundle.ReleaseGuardError, match="exactly one BEGIN/COMMIT"):
        bundle.build_bundle(tmp_path)


def test_release_bundle_rejects_candidate_symlink(tmp_path):
    _copy_candidates(tmp_path)
    candidate = tmp_path / bundle.CANDIDATES[0]
    real = tmp_path / "outside.sql"
    shutil.copy2(candidate, real)
    candidate.unlink()
    candidate.symlink_to(real)
    with pytest.raises(bundle.ReleaseGuardError, match="Missing or linked"):
        bundle.build_bundle(tmp_path)


def test_release_bundle_check_never_writes_to_checkout(tmp_path):
    _copy_candidates(tmp_path)
    sql, receipt = bundle.build_bundle(tmp_path)
    assert "CREATE FUNCTION" in sql.upper() or "create function" in sql.lower()
    assert receipt["kind"].endswith("NOT_APPLIED")
    assert not (tmp_path / "feature4_release.sql").exists()
