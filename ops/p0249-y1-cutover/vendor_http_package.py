#!/usr/bin/env python3
"""Build/test a vendored classic Y1 artifact; never publish to Azure."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
from prepare_http_only import HTTP, WORKERS, MEMBER, registrations

PREFIX = ".python_packages/lib/site-packages/"
MAX_TOTAL = 700 * 1024 * 1024
MAX_FILES = 20000

def safe_name(name):
    path = PurePosixPath(name)
    return (bool(name) and not path.is_absolute() and not any(p in ("", ".", "..")
            for p in name.split("/")) and "\\" not in name and ":" not in name)

def build(source, deps, output):
    if output.exists() or not deps.is_dir() or deps.is_symlink():
        raise ValueError("UNSAFE_ARTIFACT_TARGET")
    with ZipFile(source) as original:
        entries = original.infolist()
        names = [e.filename for e in entries]
        if (len(names) != len(set(names)) or any(not safe_name(n) or n.startswith(".python_packages/") for n in names)
                or registrations(original.read(MEMBER))[0] != {n:"route" for n in HTTP | {"p0249_health"}}):
            raise ValueError("UNVERIFIED_HTTP_SOURCE")
        if original.testzip() is not None:
            raise ValueError("SOURCE_ZIP_CORRUPT")
        files = []
        for item in sorted(deps.rglob("*")):
            if item.is_symlink():
                raise ValueError("DEPENDENCY_SYMLINK")
            if item.is_dir():
                continue
            if not item.is_file():
                raise ValueError("DEPENDENCY_NOT_FILE")
            rel = item.relative_to(deps).as_posix()
            if not safe_name(rel):
                raise ValueError("DEPENDENCY_PATH")
            if "__pycache__" in item.parts or item.suffix in (".pyc", ".pyo"):
                continue
            files.append((item, PREFIX + rel))
        if not 0 < len(files) <= MAX_FILES or sum(i.stat().st_size for i,_ in files) + sum(e.file_size for e in entries) > MAX_TOTAL:
            raise ValueError("DEPENDENCY_SIZE")
        try:
            with ZipFile(output, "x", ZIP_DEFLATED) as target:
                for e in entries:
                    target.writestr(e, original.read(e))
                for item, name in files:
                    target.write(item, name)
            with ZipFile(output) as target:
                if target.testzip() is not None or any(target.read(e.filename) != original.read(e) for e in entries):
                    raise ValueError("SOURCE_BYTES_DRIFT")
                if set(target.namelist()) != set(names) | {n for _,n in files}:
                    raise ValueError("VENDORED_INVENTORY_DRIFT")
        except Exception:
            output.unlink(missing_ok=True)
            raise

def smoke(package):
    # Isolated interpreter: no installed runner packages, checkout paths,
    # credentials or network calls from application import.
    with tempfile.TemporaryDirectory(prefix="p0249-index-") as tmp:
        root = Path(tmp)
        with ZipFile(package) as z:
            entries = z.infolist()
            if (len(entries) > MAX_FILES + 120 or sum(e.file_size for e in entries) > MAX_TOTAL
                    or len({e.filename for e in entries}) != len(entries)
                    or any(not safe_name(e.filename) or stat.S_ISLNK(e.external_attr >> 16) for e in entries)):
                raise ValueError("UNSAFE_SMOKE_ZIP")
            z.extractall(root)
        program = r'''
import sys, os, socket, json
from pathlib import Path
root = Path(sys.argv[1])
expected = set(sys.argv[2:])
sys.path[:0] = [str(root), str(root / ".python_packages/lib/site-packages")]
def deny(*args, **kwargs):
    raise RuntimeError("NETWORK_FORBIDDEN_DURING_INDEX")
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny
import function_app
import azure.functions, azure.storage.queue, jwt, PIL
functions = function_app.app.get_functions()
names = {f.get_function_name() for f in functions}
assert len(functions) == 38 and names == expected
for f in functions:
    bindings = json.loads(f.get_function_json())["bindings"]
    assert sum(b["type"] == "httpTrigger" for b in bindings) == 1
    assert all(b["type"] in ("httpTrigger", "http") for b in bindings)
print("P0249_VENDORED_REAL_SDK_INDEX=38_HTTP_ZERO_WORKERS")
'''
        result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", program, str(root),
                                 *sorted(HTTP | {"p0249_health"})],
                                cwd=root, env={"PATH": os.defpath, "LANG": "C.UTF-8"},
                                text=True, capture_output=True, timeout=120)
        if result.returncode or result.stdout.strip() != "P0249_VENDORED_REAL_SDK_INDEX=38_HTTP_ZERO_WORKERS":
            # Synthetic package only; exception type and traceback are useful
            # for import closure, but never inherit credentials from runner.
            print(result.stderr[-4000:], file=sys.stderr)
            raise RuntimeError("VENDORED_RUNTIME_IMPORT_OR_INDEX_FAILED")
        print(result.stdout.strip())

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--deps", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a=p.parse_args()
    build(a.source,a.deps,a.output)
    smoke(a.output)
    with a.output.open("rb") as f:
        print("P0249_VENDORED_PACKAGE_SHA256="+hashlib.file_digest(f,"sha256").hexdigest())

if __name__ == "__main__":
    main()
