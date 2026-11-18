"""Stage exact original Y1 two-route rollback or five-route GET package sources.

No network, Azure CLI, dependency installs or runtime side effects. The output is
NOT deployable without the separately reviewed Linux Python 3.12 vendoring and
release workflow. Never stage queue/timer functions or service-role credentials.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from stage_five_get_sources import ROUTES, SOURCES, stage_sources

TWO_ROUTES = frozenset(("p0249_health", "campaign_read"))
FIVE_ROUTES = frozenset(ROUTES)
TWO_FILES = frozenset((
    "host.json", "requirements.txt",
    "p0249_health/__init__.py", "p0249_health/function.json",
    "campaign_read/__init__.py", "campaign_read/function.json",
    "http_api.py", "security.py", "tenant_store.py",
    "draft_api.py", "request_diagnostics.py",
    "ai_agents/__init__.py", "ai_agents/schemas.py",
))
FIVE_FILES = frozenset(SOURCES)
MODES = {"five": (FIVE_ROUTES, FIVE_FILES),
         "rollback-two": (TWO_ROUTES, TWO_FILES)}


def stage_release(repo: Path, target: Path, mode: str) -> Path:
    if mode not in MODES:
        raise ValueError("unapproved Y1 release mode")
    target = stage_sources(repo, target)
    # Stage the original five-GET source snapshot first, so the rollback
    # baseline is checked with the SAME strict manifest/pin and source audit.
    allowed_routes, allowed_files = MODES[mode]
    if mode == "rollback-two":
        for path in sorted(FIVE_FILES - TWO_FILES):
            (target / path).unlink()
        for route in FIVE_ROUTES - TWO_ROUTES:
            (target / route).rmdir()
    actual = frozenset(str(p.relative_to(target))
                       for p in target.rglob("*") if p.is_file())
    indexed = frozenset(p.parent.name for p in target.glob("*/function.json"))
    if actual != allowed_files or indexed != allowed_routes:
        raise ValueError("Y1 release source file/route allowlist mismatch")
    if (target / "function_app.py").exists():
        raise ValueError("Y1 release must never start original worker triggers")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare safe source-only Y1 GET release")
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--mode", choices=sorted(MODES), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    stage_release(root, args.target, args.mode)
    print("P0249_Y1_STAGE_MODE=" + args.mode + " VERIFIED_SOURCE_ONLY NO_AZURE_WRITES")


if __name__ == "__main__":
    main()
