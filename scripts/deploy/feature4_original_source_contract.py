#!/usr/bin/env python3
"""Offline source compatibility check; never authorizes a hosted release."""
import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/feature4/original_flex_source_bindings_20261026.json"
SOURCE = ROOT / "azure-functions/campaign-api/function_app.py"
KINDS = {"route", "queue_trigger", "timer_trigger"}


def binding(call):
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        raise ValueError("non-call binding")
    if not isinstance(call.func.value, ast.Name) or call.func.value.id != "app":
        raise ValueError("non-app binding")
    if call.func.attr not in KINDS or call.args:
        raise ValueError("unsupported binding")
    values = {}
    for kw in call.keywords:
        if kw.arg is None or kw.arg in values:
            raise ValueError("non-literal or duplicate binding argument")
        values[kw.arg] = ast.literal_eval(kw.value)
    return call.func.attr, values


def collect(source):
    module = ast.parse(source)
    result = {}
    accepted = set()
    for node in module.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if not (isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name) and target.value.id == "app"):
                continue
            if node.name in result:
                raise ValueError("duplicate app binding")
            result[node.name] = binding(decorator)
            accepted.add(id(decorator))
    # Reject other direct app method calls (for example additional trigger
    # registration or a blueprint) instead of silently treating them as safe.
    for node in ast.walk(module):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "app"
                and id(node) not in accepted):
            raise ValueError("unreviewed direct app registration")
    return result


def decode(entries):
    return {name: binding(ast.parse(expr, mode="eval").body)
            for name, expr in entries.items()}


def verify(source, manifest):
    legacy = decode(manifest["legacy_bindings"])
    f4 = decode(manifest["required_feature4_http_bindings"])
    if (manifest["schema_version"] != 1 or len(legacy) != 24 or len(f4) != 7
            or set(legacy) & set(f4) or any(v[0] != "route" for v in f4.values())):
        raise ValueError("invalid reviewed baseline")
    actual = collect(source)
    for name, expected in {**legacy, **f4}.items():
        if actual.get(name) != expected:
            raise ValueError("legacy/F4 binding missing or changed: " + name)
    workers = {name: value for name, value in actual.items() if value[0] != "route"}
    expected_workers = {name: value for name, value in legacy.items() if value[0] != "route"}
    if len(expected_workers) != 9 or workers != expected_workers:
        raise ValueError("original worker binding drift or duplicate worker")
    return {"legacy_bindings_preserved": len(legacy),
            "required_feature4_http_bindings": len(f4),
            "original_worker_bindings": len(workers),
            "total_direct_bindings": len(actual),
            "restore_proved": False, "deployment_permitted": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=SOURCE)
    args = p.parse_args()
    try:
        report = verify(args.source.read_text(encoding="utf-8"),
                        json.loads(MANIFEST.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError, SyntaxError) as exc:
        print("BLOCKED: source compatibility not verified:", type(exc).__name__)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
