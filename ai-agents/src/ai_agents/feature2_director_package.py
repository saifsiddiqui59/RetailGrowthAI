"""Source-only staging of pinned MIT director files for a future approved ZIP.

No Node binary download, cloud deployment, cost or GPU execution.
"""
from pathlib import Path
from hashlib import sha1
from hmac import compare_digest

REQUIRED = frozenset((
    "director-cli.js","director.js","upstream/LICENSE",
    "upstream/explainer-plan.js","upstream/explainer-cues.js",
    "upstream/explainer-revise.js","upstream/explainer-scene.js",
    "upstream/music-video-plan.js","upstream/motion-html.js",
))
# Git blob pins for unmodified MIT originals at upstream commit
# 4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f. Modified source must
# never masquerade as the audited upstream engine during packaging.
PINNED_UPSTREAM_BLOBS = {
    "upstream/explainer-plan.js": "610cf8cfcdedd26c2487566a09d2e03c6ad059be",
    "upstream/music-video-plan.js": "4f347b4f484710fe31d553b23a570bc63c4cbd04",
    "upstream/explainer-cues.js": "6b147079754cf6669ce0c8bf284f72559db8f300",
    "upstream/explainer-revise.js": "f5ea858637f252d30cfded24dd23f2e7c9491849",
}

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
        if rel in PINNED_UPSTREAM_BLOBS:
            git_blob = sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
            if not compare_digest(git_blob, PINNED_UPSTREAM_BLOBS[rel]):
                raise PackageSourceRejected("Pinned original MIT Git blob differs: " + rel)
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
