"""Feature4 isolated worker packaging guard. Never builds/deploys cloud assets."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scripts" / "deploy" / "package_feature4_cpu.py"
spec = importlib.util.spec_from_file_location("f4_cpu_packager", PACKAGE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_worker_has_its_own_source_manifest_and_no_v1_api():
    entries = module.sources()
    assert "function_app.py" in entries
    assert "cpu_backend.py" in entries
    assert "admin_store.py" in entries
    assert "feature4_worker_handoff.py" in entries
    assert "render_adapter.py" in entries
    assert "hyperframes/render.mjs" in entries
    assert "host.json" in entries
    assert "render_worker.py" not in entries
    assert "http_api.py" not in entries
    assert len(entries) == len(set(entries))
    for entry in entries:
        assert entry not in ("", "..") and ".." not in Path(entry).parts


def test_cold_source_check_runs_with_no_hosted_credentials_or_binaries():
    result = subprocess.run([sys.executable, str(PACKAGE), "--check"],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "PASS Feature4 isolated worker sources" in result.stdout


def test_zip_build_requires_pinned_binaries_and_native_python_minor():
    class Args:
        node = ffmpeg = ffprobe = python_site_packages = puppeteer_cache = output = None
    with pytest.raises((TypeError, ValueError)):
        module.build(Args())


def test_native_worker_does_not_change_v1_release_manifest():
    v1 = (ROOT / "scripts" / "deploy" / "package.py").read_text(encoding="utf-8")
    assert 'RUNTIME_VIDEO_MODULES = frozenset({"render", "probe", "asset_preflight"})' in v1
    isolated = (ROOT / "azure-functions" / "feature4-cpu-worker" /
                "function_app.py").read_text(encoding="utf-8")
    assert "retail-reel-render" not in isolated
    assert "PUPPETEER_EXECUTABLE_PATH" in isolated
    assert "_DenyRedirects" in isolated
