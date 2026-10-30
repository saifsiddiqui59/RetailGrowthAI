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
POSTER = ROOT / "poster-engine"
AGENTS = ROOT / "ai-agents" / "src" / "ai_agents"
# Only modules imported by registered Azure Functions, their safe workers and
# optional source-controlled Feature2 AI routes belong in the small Functions
# HTTP/queue package. Offline voice/ASR/reel research modules stay in source
# control but need a separately approved worker and signed endpoint before use.
# Adding a runtime import without extending this reviewed manifest fails closed.
RUNTIME_AGENT_MODULES = frozenset({
    "__init__", "schemas", "providers", "planner", "reviewer",
    "observability", "content_intelligence", "trend_intelligence",
    "trend_runtime", "marketing_guidance", "seasonal_calendar",
    "subscriptions", "feature2_ai_writer", "feature2_llm",
    "prompt_improver",
})


def verify_runtime_agent_imports(entries: dict[str, bytes]):
    """Fail closed for undeclared static ai_agents imports in packaged code.

    Future variable-built imports still need human import-closure review and a
    deployed-from-ZIP indexing smoke; do not mistake AST for dynamic proof.
    """
    available = {p[:-3].split("/")[-1] for p in entries
                 if p.startswith("ai_agents/") and p.endswith(".py")}
    # Detect package-form imports of source modules excluded from the ZIP.
    # Names that are not source modules may be symbols exported by __init__.
    known_modules = {path.stem for path in AGENTS.glob("*.py")}
    for name, payload in entries.items():
        if not name.endswith(".py"):
            continue
        # Include all Azure HTTP/queue, poster/video workers and packaged
        # agents, not just currently enabled Feature2 routes.
        tree = ast.parse(payload, filename=name)
        for node in ast.walk(tree):
            required = set()
            if isinstance(node, ast.Import):
                required.update(a.name.split(".")[1]
                                for a in node.names
                                if a.name.startswith("ai_agents."))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("ai_agents."):
                    required.add(node.module.split(".")[1])
                elif node.module == "ai_agents":
                    required.update(a.name for a in node.names
                                    if a.name in known_modules)
                elif name.startswith("ai_agents/") and node.level == 1:
                    if node.module:
                        required.add(node.module.split(".")[0])
                    else:
                        required.update(a.name for a in node.names
                                        if a.name in known_modules)
            elif (isinstance(node, ast.Call) and
                  isinstance(node.func, ast.Attribute) and
                  node.func.attr == "import_module" and node.args and
                  isinstance(node.args[0], ast.Constant) and
                  isinstance(node.args[0].value, str) and
                  node.args[0].value.startswith("ai_agents.")):
                required.add(node.args[0].value.split(".")[1])
            elif (isinstance(node, ast.Call) and
                  isinstance(node.func, ast.Name) and
                  node.func.id == "__import__" and node.args and
                  isinstance(node.args[0], ast.Constant) and
                  isinstance(node.args[0].value, str) and
                  node.args[0].value.startswith("ai_agents.")):
                required.add(node.args[0].value.split(".")[1])
            missing = required - available
            if missing:
                raise ValueError(
                    "Undeclared ai_agents runtime import in " + name +
                    ": " + ", ".join(sorted(missing)))
    return True


TIMESTAMP = (2026, 1, 1, 0, 0, 0)
MAX_BINARY_BYTES = 180 * 1024 * 1024
MAX_ARCHIVE_BYTES = 300 * 1024 * 1024
MAX_UNPACKED_BYTES = 400 * 1024 * 1024
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
    # Azure Storage Queue SDK sends raw UUID text by default. Queue triggers
    # otherwise assume base64 and reject jobs before Python claims them.
    bundle = host.get("extensionBundle", {})
    if bundle.get("id") != "Microsoft.Azure.Functions.ExtensionBundle" or \
       bundle.get("version") != "[4.0.0, 5.0.0)":
        raise ValueError("Python queue/timer triggers require Functions extension bundle v4")
    if host.get("extensions", {}).get("queues", {}).get("messageEncoding") != "none":
        raise ValueError("Raw UUID queues must use messageEncoding=none, not base64")
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
        POSTER / "render.py",
        AGENTS / "__init__.py", AGENTS / "schemas.py",
        AGENTS / "providers.py", AGENTS / "planner.py", AGENTS / "reviewer.py",
    ]
    for path in required:
        if not path.is_file():
            raise ValueError("Required source missing: " + str(path.relative_to(ROOT)))
    entries = {}
    for folder in (SERVICE, RENDER, POSTER):
        for path in sorted(folder.glob("*.py")):
            entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    # Versioned production import closure, not a broad source-tree sweep.
    # F2's offline model/ASR research modules must not silently exhaust the
    # protected 120-member Functions ZIP when feature branches are merged.
    for module in sorted(RUNTIME_AGENT_MODULES):
        path = AGENTS / (module + ".py")
        if not path.is_file():
            raise ValueError("Approved Functions agent dependency missing: " + module)
        entries["ai_agents/" + path.name] = path.read_bytes()
    verify_runtime_agent_imports(entries)
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



def verify_static_linux_elf(payload: bytes, name: str):
    """Require self-contained Linux x86_64 ELF without a dynamic loader."""
    if not 100_000 <= len(payload) <= MAX_BINARY_BYTES:
        raise ValueError("Invalid FFmpeg executable size: " + name)
    if (payload[:7] != b"\x7fELF\x02\x01\x01"
            or struct.unpack_from("<H", payload, 18)[0] != 62):
        raise ValueError("Not Linux x86_64 ELF: " + name)
    offset = struct.unpack_from("<Q", payload, 32)[0]
    stride, count = struct.unpack_from("<HH", payload, 54)
    if not offset or stride < 56 or not 1 <= count <= 1024:
        raise ValueError("Invalid ELF headers: " + name)
    if offset + stride * count > len(payload):
        raise ValueError("Truncated ELF headers: " + name)
    for index in range(count):
        if struct.unpack_from("<I", payload, offset + stride * index)[0] == 3:
            raise ValueError("Dynamically linked FFmpeg binary unsupported: " + name)


def verify_zip(path: Path):
    """Validate ZIP and licensing without touching Azure or executing binaries."""
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Missing or oversized 300 MiB Functions ZIP")
    with ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)) or len(names) > 120:
            raise ValueError("Duplicate or excessive ZIP members")
        if sum(info.file_size for info in infos) > MAX_UNPACKED_BYTES:
            raise ValueError("400 MiB uncompressed package budget exceeded")
        for name in names:
            if (name.startswith("/") or ".." in name.split("/")
                    or "\\" in name or name.startswith(".")
                    or name.endswith(".env") or "local.settings.json" in name):
                raise ValueError("Unsafe or secret-like ZIP member: " + name)
        required = {
            "function_app.py", "requirements.txt", "host.json",
            "ai_agents/schemas.py", "azure-functions/campaign-api/render_worker.py",
            "video-engine/render.py", "poster-engine/render.py",
            "azure-functions/campaign-api/poster_worker.py",
            "bin/ffmpeg", "bin/ffprobe",
            "bin/THIRD_PARTY_NOTICES.txt",
        }
        if not required.issubset(names):
            raise ValueError("Incomplete Functions ZIP")
        if archive.testzip() is not None:
            raise ValueError("Corrupt Functions ZIP")
        host = json.loads(archive.read("host.json"))
        queue = host.get("extensions", {}).get("queues", {})
        if (host.get("functionTimeout") != "00:20:00"
                or any(queue.get(key) != val for key, val in {
                    "batchSize": 1, "newBatchThreshold": 0, "maxDequeueCount": 3
                }.items())):
            raise ValueError("Unsafe packaged Functions timeout or queue controls")
        if not archive.read("bin/THIRD_PARTY_NOTICES.txt").strip():
            raise ValueError("Missing third-party license notices")
        for name in ("bin/ffmpeg", "bin/ffprobe"):
            if not (archive.getinfo(name).external_attr >> 16) & 0o111:
                raise ValueError("Missing executable permission: " + name)
            verify_static_linux_elf(archive.read(name), name)
    return True


def ffmpeg_files(folder: Path):
    if not folder.is_dir():
        raise ValueError("Missing approved FFmpeg directory")
    found = {}
    for name in ("ffmpeg", "ffprobe"):
        file = folder / name
        if not file.is_file() or file.stat().st_size > MAX_BINARY_BYTES:
            raise ValueError("Missing or oversized Linux x86_64 executable: " + name)
        payload = file.read_bytes()
        verify_static_linux_elf(payload, name)
        found["bin/" + name] = payload
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
    parser.add_argument("--verify-zip", type=Path, help="Verify deployment ZIP offline")
    parser.add_argument("--ffmpeg-dir", type=Path, help="Approved Linux x64 FFmpeg + notices directory")
    parser.add_argument("--output", type=Path, default=ROOT / ".artifacts" / "retailgrowth-functions.zip")
    args = parser.parse_args(argv)
    if args.verify_zip:
        verify_zip(args.verify_zip)
        print("PASS: offline ZIP verified:", args.verify_zip)
        return 0
    entries = source_files()
    if args.check:
        assert "azure-functions/campaign-api/render_worker.py" in entries
        assert "video-engine/render.py" in entries
        assert "poster-engine/render.py" in entries
        assert "ai_agents/schemas.py" in entries
        print("PASS: source layout, import wrapper, queue settings and lease/timeout checks; no cloud calls")
        return 0
    if args.ffmpeg_dir is None:
        parser.error("Must supply approved Linux FFmpeg: --ffmpeg-dir")
    entries.update(ffmpeg_files(args.ffmpeg_dir))
    write_zip(args.output, entries)
    verify_zip(args.output)
    print("PASS: packaged offline, not deployed:", args.output)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("PACKAGING FAILED:", exc, file=sys.stderr)
        sys.exit(2)
