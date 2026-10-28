"""Source-only staging of pinned MIT director files for a future approved ZIP.

No Node binary download, cloud deployment, cost or GPU execution.
"""
from pathlib import Path

REQUIRED = frozenset((
    "director-cli.js","director.js","upstream/LICENSE",
    "upstream/explainer-plan.js","upstream/explainer-cues.js",
    "upstream/explainer-revise.js","upstream/explainer-scene.js",
    "upstream/music-video-plan.js","upstream/motion-html.js",
))
class PackageSourceRejected(ValueError):
    pass

def source_entries(repository_root: Path) -> dict[str, bytes]:
    if not isinstance(repository_root, Path) or not repository_root.is_dir():
        raise PackageSourceRejected("Missing repository root")
    directory = repository_root / "ai-agents/creative-director"
    if not directory.is_dir() or directory.is_symlink():
        raise PackageSourceRejected("Pinned MIT source missing")
    entries = {}
    total = 0
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise PackageSourceRejected("Source contains symlink")
        if not path.is_file():
            continue
        rel = path.relative_to(directory).as_posix()
        if (any(part.startswith(".") or part == ".." for part in rel.split("/"))
            or not (rel.endswith((".js",".json",".md")) or rel == "upstream/LICENSE")):
            raise PackageSourceRejected("Unreviewed file extension or member")
        data = path.read_bytes()
        if not data or len(data)>250_000:
            raise PackageSourceRejected("Source is missing or oversized")
        total += len(data)
        if total > 2_000_000:
            raise PackageSourceRejected("Source bundle exceeds budget")
        entries["ai_agents/creative-director/"+rel]=data
    if not REQUIRED.issubset(set(k.removeprefix("ai_agents/creative-director/") for k in entries)):
        raise PackageSourceRejected("Missing required pinned upstream source")
    license = entries["ai_agents/creative-director/upstream/LICENSE"]
    if b"MIT License" not in license or b"Copyright (c) 2026 Kuble AG" not in license:
        raise PackageSourceRejected("MIT attribution missing")
    return entries
