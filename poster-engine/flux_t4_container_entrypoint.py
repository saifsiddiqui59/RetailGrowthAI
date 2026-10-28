"""Isolated one-shot FLUX.2 Klein 4B Azure T4 job. NOT a public web API.

Only consumes already-authorized, private, immutable, operator-staged model
weights and a private bounded job request. Never downloads weights at runtime,
connects to a tenant database, reserves arbitrary GPU spend, or publishes
outputs. Model outputs remain DRAFT/unreviewed until reviewed and registered.
"""
from __future__ import annotations
import argparse
import json
import os
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from time import monotonic
from uuid import UUID

from ai_providers_v2 import InferenceJob, ProviderBlocked, _verified_png
from flux_t4_snapshot import verify_reviewed_flux_snapshot
from gpu_worker_v2 import OfflineFluxKlein4B

MAX_JOB_BYTES = 4096
MAX_SECONDS = 600
MAX_CONTAINER_SECONDS = 900


def _verify_one_shot_budget():
    """No GPU job without an operator's complete estimated all-in compute rate.

    This cannot cap Azure storage/egress or billing outside the container
    lifetime; those require a separate resource budget and cleanup review.
    """
    if os.environ.get("RETAIL_FLUX_PAID_ONE_SHOT_APPROVED") != "1":
        raise ProviderBlocked("Protected FLUX one-shot spend approval is absent")
    try:
        rate = Decimal(os.environ["RETAIL_FLUX_TOTAL_RATE_USD_PER_SECOND"])
        cap = Decimal(os.environ["RETAIL_FLUX_MAX_USD_PER_RUN"])
    except (KeyError, InvalidOperation) as exc:
        raise ProviderBlocked("Verified Azure GPU+CPU+RAM price and spend cap required") from exc
    if (not rate.is_finite() or not cap.is_finite() or rate <= 0 or cap <= 0
        or rate * MAX_CONTAINER_SECONDS > cap):
        raise ProviderBlocked("FLUX worst-case GPU job exceeds approved spending estimate")
    return str(rate * MAX_CONTAINER_SECONDS)


def _private_dir(value):
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        raise ProviderBlocked("An absolute private output path is required")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ProviderBlocked("Output must be a new or empty private directory")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path.resolve(strict=True)


def _read_job(path):
    if not path.is_absolute() or not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_JOB_BYTES:
        raise ProviderBlocked("A bounded private job JSON file is required")
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or set(data) !=
        {"schema", "shop_id", "job_id", "capability", "prompt"}
        or data["schema"] != "retailgrowth.feature3.flux-single-sample.v1"
        or data["capability"] not in ("text_to_image", "human_model")
        or not isinstance(data["prompt"], str) or not 5 <= len(data["prompt"].strip()) <= 500
        or any(term in data["prompt"].lower() for term in ("child model", "underage model", "minor model"))
    ):
        raise ProviderBlocked("Invalid, non-adult or excessive FLUX job")
    try:
        if str(UUID(data["shop_id"])) != data["shop_id"] or str(UUID(data["job_id"])) != data["job_id"]:
            raise ValueError("Invalid scope")
    except (TypeError, KeyError, ValueError) as exc:
        raise ProviderBlocked("Scoped job UUIDs are required") from exc
    return InferenceJob(
        shop_id=data["shop_id"], job_id=data["job_id"],
        capability=data["capability"], prompt=data["prompt"],
    )


def run_one(*, weights, approval, request, output):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["DIFFUSERS_OFFLINE"] = "1"
    maximum_estimated_compute_usd = _verify_one_shot_budget()
    manifest = verify_reviewed_flux_snapshot(weights, approval)
    if manifest.get("weight_shards_sha256_verified") is not True:
        raise ProviderBlocked("All FLUX shard digests must be verified before GPU billing")
    job = _read_job(Path(request))
    dest = _private_dir(output)
    t0 = monotonic()
    worker = OfflineFluxKlein4B(weights, height=512, width=512)
    payload = _verified_png(worker(job, {}))
    seconds = monotonic() - t0
    # A mocked Pillow PNG is NOT real inference. Fail closed unless the
    # concrete CUDA worker confirmed actual GPU execution and synchronization.
    if getattr(worker, "actual_cuda_verified", False) is not True:
        raise ProviderBlocked("FLUX runtime CUDA inference has not been verified")
    if seconds > MAX_SECONDS:
        raise ProviderBlocked("FLUX exceeded the approved per-execution time")
    output_file = dest / "flux-unreviewed.png"
    if output_file.exists():
        raise ProviderBlocked("Immutable output already exists")
    with output_file.open("xb") as fd:
        fd.write(payload)
    receipt = {
        "schema": "retailgrowth.feature3.flux-t4-result.v1",
        "shop_id": job.shop_id, "job_id": job.job_id,
        "repository": manifest["repository"], "revision_sha": manifest["revision_sha"],
        "image_sha256": sha256(payload).hexdigest(),
        "generation_executed": True, "actual_cuda_verified": True,
        "human_reviewed": False, "registered_private_media": False,
        "commercial_publishing_allowed": False,
        "image_size": len(payload), "inference_seconds": round(seconds, 3),
        "operator_estimated_max_process_compute_usd": maximum_estimated_compute_usd,
    }
    with (dest / "unreviewed-receipt.json").open("x", encoding="utf-8") as fd:
        json.dump(receipt, fd, indent=2)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(run_one(weights=a.weights, approval=a.approval,
                             request=a.request, output=a.output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
