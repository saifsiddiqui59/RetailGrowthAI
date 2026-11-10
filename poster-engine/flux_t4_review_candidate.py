"""Build a *review candidate* for the genuine, locally staged FLUX 4B files.

No Hugging Face download, CUDA import or commercial license auto-approval.
Actual operators must independently inspect origin, files and dependency
licenses, then review the manifest outside the immutable snapshot mount.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

from ai_providers_v2 import ProviderBlocked
from flux_t4_snapshot import (MODEL, OFFICIAL_REVISION, REQUIRED_CONFIG_FILES,
                              SCHEMA, MAX_MANIFEST)

MIN_SHARDS = {
    "text_encoder/model-00001-of-00002.safetensors",
    "text_encoder/model-00002-of-00002.safetensors",
    "transformer/diffusion_pytorch_model.safetensors",
    "vae/diffusion_pytorch_model.safetensors",
}


def _hash_file(root: Path, name: str) -> str:
    path = root / name
    if any((root.joinpath(*Path(name).parts[:i])).is_symlink()
           for i in range(1, len(Path(name).parts)+1)):
        raise ProviderBlocked("Private snapshot contains symbolic-link components")
    if not path.is_file() or path.stat().st_size <= 0:
        raise ProviderBlocked("Missing or empty staged snapshot file")
    digest = sha256()
    with path.open("rb") as reader:
        for block in iter(lambda: reader.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_review_candidate(weights_directory: Path) -> dict:
    root = Path(weights_directory)
    if not root.is_dir() or root.is_symlink():
        raise ProviderBlocked("Real private snapshot directory required")
    index = root / "model_index.json"
    if index.is_symlink() or not index.is_file():
        raise ProviderBlocked("Missing private model_index.json")
    try:
        obj = json.loads(index.read_text("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ProviderBlocked("Unparseable FLUX checkpoint index") from exc
    if not isinstance(obj, dict) or obj.get("_class_name") != "Flux2KleinPipeline":
        raise ProviderBlocked("Unapproved FLUX pipeline class")
    shards = {p.relative_to(root).as_posix() for p in root.rglob("*.safetensors")}
    if not MIN_SHARDS.issubset(shards) or not 4 <= len(shards) <= 20:
        raise ProviderBlocked("Missing expected FLUX.2 4B checkpoint shards")
    # Reject noncanonical path separators and nested linked directories.
    for item in shards:
        if any(seg in ("", ".", "..") for seg in item.split("/")):
            raise ProviderBlocked("Unsafe staged shard path")
    manifest = {
        "schema": SCHEMA,
        "repository": MODEL,
        "revision_sha": OFFICIAL_REVISION,
        "weights_license": "Apache-2.0",
        "model_index_sha256": _hash_file(root, "model_index.json"),
        "shards_sha256": {name:_hash_file(root,name) for name in sorted(shards)},
        "configs_sha256": {name:_hash_file(root,name) for name in sorted(REQUIRED_CONFIG_FILES)},
        # This cannot become True by hashing files. An operator must review
        # the official revision, checkpoint provenance and dependency licenses.
        "dependencies_operator_approved": False,
    }
    if len(json.dumps(manifest).encode("utf-8")) > MAX_MANIFEST:
        raise ProviderBlocked("Snapshot manifest exceeds integrity limit")
    return manifest


def write_candidate(weights_directory: Path, destination: Path) -> Path:
    root, dest = Path(weights_directory), Path(destination)
    # An approval document is outside the model snapshot and never embedded
    # in a model/container image or overwritten on repeated execution.
    if not dest.is_absolute() or dest.exists() or dest.is_symlink():
        raise ProviderBlocked("New absolute private review file required")
    if root.resolve() == dest.parent.resolve() or root.resolve() in dest.parents:
        raise ProviderBlocked("Review document must not live inside checkpoint")
    data = build_review_candidate(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except BaseException:
        dest.unlink(missing_ok=True)
        raise
    return dest


def main(argv=None):
    parser=argparse.ArgumentParser(description="Create unapproved private FLUX 4B snapshot review candidate")
    parser.add_argument("--weights",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args(argv)
    print(write_candidate(args.weights,args.output))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
