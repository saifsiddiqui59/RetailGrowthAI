"""Offline full FLUX.2 Klein 4B snapshot attestation for GPU execution.

All safetensors files present must be recorded and checked, including multiple
text encoder shards. This does not make user garments or human reference
images licensed; it approves only the local public Apache-2.0 FLUX weights.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

from ai_providers_v2 import ProviderBlocked

MODEL = "black-forest-labs/FLUX.2-klein-4B"
OFFICIAL_REVISION = "e7b7dc27f91deacad38e78976d1f2b499d76a294"
SHA = re.compile(r"^[a-f0-9]{64}$")
SCHEMA = "retailgrowth.flux2-klein-4b.full-snapshot.v3"
MAX_MANIFEST = 16384
# Verified against the publisher's exact FLUX.2 Klein 4B Diffusers layout.
# Shards alone are insufficient for a loadable, untampered pipeline.
REQUIRED_CONFIG_FILES = frozenset({
    "LICENSE.md",
    "scheduler/scheduler_config.json",
    "text_encoder/config.json",
    "text_encoder/generation_config.json",
    "text_encoder/model.safetensors.index.json",
    "transformer/config.json",
    "vae/config.json",
    "tokenizer/added_tokens.json",
    "tokenizer/chat_template.jinja",
    "tokenizer/merges.txt",
    "tokenizer/special_tokens_map.json",
    "tokenizer/tokenizer.json",
    "tokenizer/tokenizer_config.json",
    "tokenizer/vocab.json",
})


def _digest(path):
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_reviewed_flux_snapshot(directory, approval_manifest):
    root, manifest_path = Path(directory), Path(approval_manifest)
    if (not root.is_dir() or root.is_symlink()
        or not manifest_path.is_file() or manifest_path.is_symlink()
        or manifest_path.stat().st_size > MAX_MANIFEST):
        raise ProviderBlocked("Private staged FLUX weights and reviewed manifest required")
    try:
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or set(record) != {
            "schema", "repository", "revision_sha", "weights_license",
            "model_index_sha256", "shards_sha256", "configs_sha256", "dependencies_operator_approved",
        } or record["schema"] != SCHEMA or record["repository"] != MODEL or \
            record["revision_sha"] != OFFICIAL_REVISION or \
            record["weights_license"] != "Apache-2.0" or \
            record["dependencies_operator_approved"] is not True or \
            not SHA.fullmatch(record["model_index_sha256"]):
            raise ProviderBlocked("Unapproved FLUX model revision or dependency license")
        hashes = record["shards_sha256"]
        if not isinstance(hashes, dict) or len(hashes) < 4 or len(hashes) > 20:
            raise ProviderBlocked("Complete FLUX safetensors manifest required")
        actual = {p.relative_to(root).as_posix() for p in root.rglob("*.safetensors")}
        if set(hashes) != actual or not {
            "text_encoder/model-00001-of-00002.safetensors",
            "text_encoder/model-00002-of-00002.safetensors",
            "transformer/diffusion_pytorch_model.safetensors",
            "vae/diffusion_pytorch_model.safetensors",
        } <= actual:
            raise ProviderBlocked("Incomplete or replaced model shards")
        configs = record["configs_sha256"]
        if not isinstance(configs, dict) or set(configs) != REQUIRED_CONFIG_FILES:
            raise ProviderBlocked("Complete verified FLUX tokenizer/config manifest required")
        for name, digest in {**hashes, **configs}.items():
            ref = PurePosixPath(name)
            if (ref.is_absolute() or ".." in ref.parts or
                any(part in ("", ".") for part in ref.parts) or
                not isinstance(digest, str) or not SHA.fullmatch(digest)):
                raise ProviderBlocked("Unsafe model file manifest")
            path = root.joinpath(*ref.parts)
            # Reject symlinks at every interior level, not only at the leaf.
            if (any((root.joinpath(*ref.parts[:i])).is_symlink()
                    for i in range(1, len(ref.parts) + 1))
                or not path.is_file() or path.stat().st_size == 0
                or _digest(path) != digest):
                raise ProviderBlocked("FLUX model bytes do not match approval")
        index = root / "model_index.json"
        if index.is_symlink() or not index.is_file() or _digest(index) != record["model_index_sha256"]:
            raise ProviderBlocked("FLUX model index changed")
        if json.loads(index.read_text(encoding="utf-8")).get("_class_name") != "Flux2KleinPipeline":
            raise ProviderBlocked("Unapproved FLUX pipeline")
        return {
            "repository": MODEL, "revision_sha": OFFICIAL_REVISION,
            "weight_license": "Apache-2.0", "model_index_sha256": record["model_index_sha256"],
            "weight_shards_sha256_verified": True,
            "configs_sha256_verified": True,
            "dependencies_operator_approved": True, "offline_only": True,
            "saas_deployment_authorized": False,
        }
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        raise ProviderBlocked("Malformed or inaccessible FLUX approval/snapshot") from exc
