#!/usr/bin/env python3
"""Build a deterministic Functions ZIP offline. No cloud calls or binary downloads.

Retain nested Azure source directories: render_worker.py locates video-engine by
walking two parents. A generated root wrapper exposes the decorated 'app' object.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import struct
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "azure-functions" / "campaign-api"
RENDER = ROOT / "video-engine"
AGENTS = ROOT / "ai-agents" / "src" / "ai_agents"
TIMESTAMP = (2026, 1, 1, 0, 0, 0)
ENTRY = '''"""Generated entrypoint; source lives at azure-functions/campaign-api/function_app.py."""
from pathlib import Path
import importlib.util
import os
import sys

root = Path(__file__).resolve().parent
service = root / "azure-functions" / "campaign-api"
os.environ["PATH"] = str(root / "bin") + os.pathsep + os.environ.get("PATH", "")
sys.path.insert(0, str(service))
spec = importlib.util.spec_from_file_location("retailgrowth_entry", service / "function_app.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
app = module.app
'''


def verify_worker_budget(host, lease_sql, renderer_source):
    """Fail closed if the fixed host, DB lease, or encoder budget drifts."""
    if host.get("functionTimeout") != "00:20:00":
        raise ValueError("Expected bounded 20-minute Flex Functions host timeout")
    for name in ("claim_campaign_job", "claim_render_job"):
        marker = "create or replace function public." + name + "("
        body = lease_sql.partition(marker)[2].partition("\n$;")[0]
        if not body or "interval '25 minutes'" not in body:
            raise ValueError("Worker claim lease must be 25 minutes for " + name)
    parsed = ast.parse(renderer_source)
    timeouts = [
        keyword.value.value
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess" and node.func.attr == "run"
        for keyword in node.keywords
        if keyword.arg == "timeout" and isinstance(keyword.value, ast.Constant)
    ]
    if timeouts != [780]:
        raise ValueError("FFmpeg subprocess must retain its 780-second hard limit")


def source_files():
    required = [
        SERVICE / "function_app.py", SERVICE / "render_worker.py",
        SERVICE / "requirements.txt", SERVICE / "host.json",
        RENDER / "render.py", RENDER / "probe.py",
        AGENTS / "__init__.py", AGENTS / "schemas.py",
        AGENTS / "providers.py", AGENTS / "planner.py", AGENTS / "reviewer.py",
    ]
    for path in required:
        if not path.is_file():
            raise ValueError("Required source missing: " + str(path.relative_to(ROOT)))
    entries = {}
    for folder in (SERVICE, RENDER):
        for path in sorted(folder.glob("*.py")):
            entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for path in sorted(AGENTS.glob("*.py")):
        entries["ai_agents/" + path.name] = path.read_bytes()
    entries["function_app.py"] = ENTRY.encode()
    entries["requirements.txt"] = (SERVICE / "requirements.txt").read_bytes()
    host = json.loads((SERVICE / "host.json").read_text("utf-8"))
    verify_worker_budget(
        host,
        (ROOT / "supabase/migrations/20261022205000_p1_worker_execution_budget.sql").read_text("utf-8"),
        (RENDER / "render.py").read_text("utf-8"),
    )
    queues = host.setdefault("extensions", {}).setdefault("queues", {})
    queues.update({"batchSize": 1, "newBatchThreshold": 0, "maxDequeueCount": 3})
    entries["host.json"] = (json.dumps(host, indent=2) + "\n").encode()
    return entries


def ffmpeg_files(folder: Path):
    if not folder.is_dir():
        raise ValueError("Missing approved FFmpeg directory")
    found = {}
    for name in ("ffmpeg", "ffprobe"):
        file = folder / name
        if not file.is_file() or file.stat().st_size < 100000:
            raise ValueError("Missing full Linux x86_64 executable: " + name)
        with file.open("rb") as stream:
            header = stream.read(20)
        if not (len(header) == 20 and header[:4] == b"\x7fELF"
                and header[4:6] == bytes((2, 1))
                and struct.unpack("<H", header[18:20])[0] == 62):
            raise ValueError("Not Linux x86_64 ELF: " + name)
        found["bin/" + name] = file.read_bytes()
    notices = folder / "THIRD_PARTY_NOTICES.txt"
    if not notices.is_file() or not notices.read_text("utf-8").strip():
        raise ValueError("An audited FFmpeg distribution and licensing notice is required")
    found["bin/THIRD_PARTY_NOTICES.txt"] = notices.read_bytes()
    return found


def write_zip(path: Path, entries: dict[str, bytes]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=6) as zip_file:
        for name in sorted(entries):
            info = ZipInfo(name, TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o100755 if name in ("bin/ffmpeg", "bin/ffprobe") else 0o100644) << 16
            zip_file.writestr(info, entries[name])
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Only validate source/layout")
    parser.add_argument("--ffmpeg-dir", type=Path, help="Approved Linux x64 FFmpeg + notices directory")
    parser.add_argument("--output", type=Path, default=ROOT / ".artifacts" / "retailgrowth-functions.zip")
    args = parser.parse_args(argv)
    entries = source_files()
    if args.check:
        assert "azure-functions/campaign-api/render_worker.py" in entries
        assert "video-engine/render.py" in entries
        assert "ai_agents/schemas.py" in entries
        print("PASS: source layout, import wrapper, queue settings and lease/timeout checks; no cloud calls")
        return 0
    if args.ffmpeg_dir is None:
        parser.error("Must supply approved Linux FFmpeg: --ffmpeg-dir")
    entries.update(ffmpeg_files(args.ffmpeg_dir))
    write_zip(args.output, entries)
    with ZipFile(args.output) as archive:
        if set(archive.namelist()) != set(entries):
            raise ValueError("Incomplete ZIP")
    print("PASS: packaged offline, not deployed:", args.output)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("PACKAGING FAILED:", exc, file=sys.stderr)
        sys.exit(2)
