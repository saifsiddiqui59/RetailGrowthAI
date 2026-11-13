"""No-network license/snapshot integrity gate for local FLUX.2 Klein 4B.

The operator generates a pinned JSON manifest only after checking the model's
upstream commercial license and exact downloaded snapshot. Merely naming a
folder 'klein-4b' is NOT evidence of an Apache-2.0 model. This check is not a
cryptographic software supply-chain signature: operator must trust the source,
review all dependencies, and protect this manifest against tampering.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from ai_providers_v2 import ProviderBlocked

MODEL_REPO = "black-forest-labs/FLUX.2-klein-4B"
MANIFEST_NAME = "retailgrowth.flux2-klein-4b.approval.v1"
SHA256 = re.compile(r"^[a-f0-9]{64}$")
COMMIT_SHA = re.compile(r"^[a-f0-9]{40}$")


def verify_local_flux_snapshot(weights_directory, approval_manifest):
    weights = Path(weights_directory).expanduser()
    path = Path(approval_manifest).expanduser()
    if (not weights.is_dir() or weights.is_symlink()
        or not (weights / "model_index.json").is_file()
        or (weights / "model_index.json").is_symlink()
        or not path.is_file() or path.is_symlink()
        or path.stat().st_size > 8192):
        raise ProviderBlocked("Approved local FLUX.2 model snapshot/manifest required")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        index = json.loads((weights / "model_index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ProviderBlocked("Unparseable local model approval or index") from exc
    required = {"schema", "repository", "revision_sha", "weight_license",
                "model_index_sha256", "commercial_operator_approved",
                "dependencies_operator_approved"}
    if (not isinstance(data, dict) or set(data) != required
        or data["schema"] != MANIFEST_NAME
        or data["repository"] != MODEL_REPO
        or data["weight_license"] != "Apache-2.0"
        or data["commercial_operator_approved"] is not True
        or data["dependencies_operator_approved"] is not True
        or not isinstance(data["revision_sha"], str)
        or not COMMIT_SHA.fullmatch(data["revision_sha"])
        or not isinstance(data["model_index_sha256"], str)
        or not SHA256.fullmatch(data["model_index_sha256"])
        or not isinstance(index, dict)
        or index.get("_class_name") != "Flux2KleinPipeline"):
        raise ProviderBlocked("Unapproved FLUX repository, pipeline, license or dependencies")
    digest = sha256((weights / "model_index.json").read_bytes()).hexdigest()
    if digest != data["model_index_sha256"]:
        raise ProviderBlocked("Local model index differs from reviewed snapshot")
    # The operator-provided revision pins provenance; this does NOT prove
    # every multi-GB safetensors shard has been hash-verified. Hosted release
    # still needs a complete manifest/shard audit before customer usage.
    return {
        "repository": MODEL_REPO, "revision_sha": data["revision_sha"],
        "weight_license": "Apache-2.0", "model_index_sha256": digest,
        "offline_only": True, "commercial_dependency_review": True,
        "weight_shards_sha256_verified": False,
        "saas_deployment_authorized": False,
    }
