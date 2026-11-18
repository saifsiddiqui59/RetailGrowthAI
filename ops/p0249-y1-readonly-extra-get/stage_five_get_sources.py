"""Stage the five GET-only Y1 source files; never deploy or vend dependencies.

This is a source-only, non-deployable staging directory. A separately reviewed
protected workflow must install pinned dependencies, build the actual ZIP,
verify the Azure identity and enforce rollback before any DEV mutation.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import shutil

# Deliberately exhaustive: never copy function_app.py, workers, queues,
# service credentials, mutable deployment settings or entire source folders.
SOURCES = {
    "host.json": "ops/p0249-y1-v1-canary/host.json",
    "requirements.txt": "ops/p0249-y1-readonly-campaign/requirements.txt",
    "p0249_health/__init__.py": "ops/p0249-y1-v1-canary/p0249_health/__init__.py",
    "p0249_health/function.json": "ops/p0249-y1-v1-canary/p0249_health/function.json",
    "campaign_read/__init__.py": "ops/p0249-y1-readonly-campaign/campaign_read/__init__.py",
    "campaign_read/function.json": "ops/p0249-y1-readonly-campaign/campaign_read/function.json",
    "render_job_read/__init__.py": "ops/p0249-y1-readonly-extra-get/render_job_read/__init__.py",
    "render_job_read/function.json": "ops/p0249-y1-readonly-extra-get/render_job_read/function.json",
    "poster_job_read/__init__.py": "ops/p0249-y1-readonly-extra-get/poster_job_read/__init__.py",
    "poster_job_read/function.json": "ops/p0249-y1-readonly-extra-get/poster_job_read/function.json",
    "poster_draft_read/__init__.py": "ops/p0249-y1-readonly-extra-get/poster_draft_read/__init__.py",
    "poster_draft_read/function.json": "ops/p0249-y1-readonly-extra-get/poster_draft_read/function.json",
    "p0249_readonly_jobs.py": "ops/p0249-y1-readonly-extra-get/p0249_readonly_jobs.py",
    "http_api.py": "azure-functions/campaign-api/http_api.py",
    "security.py": "azure-functions/campaign-api/security.py",
    "tenant_store.py": "azure-functions/campaign-api/tenant_store.py",
    "draft_api.py": "azure-functions/campaign-api/draft_api.py",
    "render_api.py": "azure-functions/campaign-api/render_api.py",
    "poster_render_api.py": "azure-functions/campaign-api/poster_render_api.py",
    "poster_draft_api.py": "azure-functions/campaign-api/poster_draft_api.py",
    "request_diagnostics.py": "azure-functions/campaign-api/request_diagnostics.py",
    "ai_agents/__init__.py": "ai-agents/src/ai_agents/__init__.py",
    "ai_agents/schemas.py": "ai-agents/src/ai_agents/schemas.py",
}
ROUTES = {
    "p0249_health": "p0249/health",
    "campaign_read": "campaigns/{campaign_id}",
    "render_job_read": "render-jobs/{job_id}",
    "poster_job_read": "poster-jobs/{job_id}",
    "poster_draft_read": "poster-drafts/{draft_id}",
}


def _validated_manifest(source: Path, route: str) -> None:
    manifest = json.loads(source.read_text(encoding="utf-8"))
    if (set(manifest) != {"scriptFile", "entryPoint", "bindings"}
            or manifest["scriptFile"] != "__init__.py"
            or manifest["entryPoint"] != "main"
            or not isinstance(manifest["bindings"], list)
            or len(manifest["bindings"]) != 2):
        raise ValueError("unexpected Y1 function manifest structure")
    triggers = [binding for binding in manifest["bindings"]
                if binding.get("type") == "httpTrigger"]
    outputs = [binding for binding in manifest["bindings"]
               if binding.get("type") == "http"]
    if (len(triggers) != 1 or len(outputs) != 1
            or triggers[0] != {
                "authLevel": "anonymous", "type": "httpTrigger",
                "direction": "in", "name": "req",
                "methods": ["get"], "route": route,
            }
            or outputs[0] != {
                "type": "http", "direction": "out", "name": "$return",
            }):
        raise ValueError("Y1 package must contain only approved GET routes")


def stage_sources(repo: Path, target: Path) -> Path:
    repo = repo.resolve(strict=True)
    raw_target = target.absolute()
    # Check symlink itself before resolving parents and dot-dot path segments.
    if raw_target.exists() or raw_target.is_symlink():
        raise ValueError("staging target already exists")
    target = raw_target.resolve(strict=False)
    # Reject prior or partially assembled packages and repo-relative output.
    if repo == target or repo in target.parents or target in repo.parents:
        raise ValueError("staging target overlaps source repository")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise ValueError("staging parent must already exist and not be a symlink")

    # Preflight every byte and route before creating any output directory.
    for dest, relative in SOURCES.items():
        source = repo / relative
        if not source.is_file() or source.is_symlink() or repo not in source.resolve().parents:
            raise ValueError("missing or symlinked allowlisted Y1 source: " + relative)
        if dest.endswith(".py"):
            ast.parse(source.read_text(encoding="utf-8"), filename=relative)
        elif dest.endswith("function.json"):
            _validated_manifest(source, ROUTES[Path(dest).parent.name])
    host = json.loads((repo / SOURCES["host.json"]).read_text(encoding="utf-8"))
    if host.get("version") != "2.0":
        raise ValueError("unexpected Azure Functions host version")
    pins = (repo / SOURCES["requirements.txt"]).read_text(encoding="utf-8").splitlines()
    if pins != ["azure-functions==1.24.0", "PyJWT[crypto]==2.10.1"]:
        raise ValueError("pinned Y1 Python requirements changed; review needed")

    target.mkdir()
    for dest, relative in SOURCES.items():
        outfile = target / dest
        outfile.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / relative, outfile)
        if outfile.read_bytes() != (repo / relative).read_bytes():
            raise ValueError("original Y1 source changed during staging")
    actual = {str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()}
    if actual != set(SOURCES):
        raise ValueError("unexpected file in Y1 source staging")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage ONLY five Y1 GET sources (NOT deployable)")
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    stage_sources(root, args.target)
    print("P0249_Y1_FIVE_GET_SOURCE_STAGE=PASS; NOT_DEPLOYABLE; NO_AZURE_WRITES")


if __name__ == "__main__":
    main()
