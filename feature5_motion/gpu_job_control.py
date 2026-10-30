"""Guarded A100 manual GPU job control for RetailGrowthAI Feature5.

No Azure provisioning, image build or model download. Start defaults to dry-run;
stop targets only the fixed DEV job and verifies Azure execution states.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
from decimal import Decimal, InvalidOperation
from feature5_motion.shared_model_mount import (
    ACCOUNT as MODEL_ACCOUNT, SHARE as MODEL_SHARE,
    STORAGE_NAME as MODEL_STORAGE_NAME, VOLUME_NAME as MODEL_VOLUME_NAME,
    MOUNT_PATH as MODEL_MOUNT_PATH,
)

GROUP = "rg-retailgrowth-dev"
ENV = "rgai-f5-gpu-canary-eastus"
JOB = "rgai-f5-wan22-a100-canary"
PROFILE_TYPE = "Consumption-GPU-NC24-A100"
TERMINAL = {"succeeded", "failed", "stopped", "cancelled", "canceled"}
ACTIVE = {"running", "pending", "processing", "starting", "queued", "created"}
UUID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")

class SafetyError(RuntimeError):
    pass

def az(*args):
    try:
        output = subprocess.run(["az", *args, "-o", "json"], check=True,
                                capture_output=True, text=True, timeout=60)
        return json.loads(output.stdout) if output.stdout.strip() else None
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise SafetyError("Azure command failed/unreadable; no successful action can be assumed") from exc

def subscription():
    expected = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    if not UUID.fullmatch(expected):
        raise SafetyError("Set AZURE_SUBSCRIPTION_ID to exact DEV subscription UUID")
    account = az("account", "show")
    if not isinstance(account, dict) or account.get("id", "").lower() != expected.lower() or account.get("state") != "Enabled":
        raise SafetyError("Azure subscription does not match enabled DEV subscription")
    return expected

def rgflags(sub):
    return ("-g", GROUP, "--subscription", sub)

def owned(tags, feature=False):
    if not isinstance(tags, dict):
        return False
    t = {str(k).lower(): str(v).lower() for k, v in tags.items()}
    return (t.get("app") == "retailgrowthai" and t.get("environment") == "dev"
            and (not feature or t.get("feature") == "feature5"))

def check_group(sub):
    g = az("group", "show", "-n", GROUP, "--subscription", sub)
    if not isinstance(g, dict) or g.get("name") != GROUP or not owned(g.get("tags")):
        raise SafetyError("DEV resource group ownership not verified")

def job(sub):
    jobs = az("containerapp", "job", "list", *rgflags(sub))
    if not isinstance(jobs, list):
        raise SafetyError("Cannot list DEV jobs")
    matches = [j for j in jobs if isinstance(j, dict) and j.get("name") == JOB]
    if len(matches) > 1:
        raise SafetyError("Ambiguous GPU job match")
    if not matches:
        return None
    found = az("containerapp", "job", "show", "-n", JOB, *rgflags(sub))
    if not isinstance(found, dict) or found.get("name") != JOB:
        raise SafetyError("GPU job lookup mismatch")
    return found

def executions(sub):
    items = az("containerapp", "job", "execution", "list", "-n", JOB, *rgflags(sub))
    if not isinstance(items, list):
        raise SafetyError("Cannot verify GPU executions")
    states = []
    for item in items:
        if not isinstance(item, dict):
            raise SafetyError("Malformed GPU execution")
        state = str((item.get("properties") or {}).get("status") or item.get("status") or "").lower()
        if state not in TERMINAL | ACTIVE or not item.get("name"):
            raise SafetyError("Unknown GPU execution state; cannot assume stopped")
        states.append((item["name"], state))
    return states

def check_model_share_mount(sub, j):
    """No paid job can launch without the one private read-only model share."""
    template = (j.get("properties") or {}).get("template") or {}
    volumes = template.get("volumes") or []
    matches = [v for v in volumes if isinstance(v, dict) and v.get("name") == MODEL_VOLUME_NAME]
    if len(matches) != 1 or matches[0].get("storageType") != "AzureFile" or matches[0].get("storageName") != MODEL_STORAGE_NAME:
        raise SafetyError("Missing expected classic Azure Files job volume")
    containers = template.get("containers") or []
    if len(containers) != 1:
        raise SafetyError("Only one model worker is permitted")
    mounts = containers[0].get("volumeMounts") or []
    expected = [v for v in mounts if isinstance(v, dict) and v.get("volumeName") == MODEL_VOLUME_NAME]
    if len(expected) != 1 or expected[0].get("mountPath") != MODEL_MOUNT_PATH or expected[0].get("subPath"):
        raise SafetyError("Missing or misdirected shared model mount")
    config = az("containerapp", "env", "storage", "show", "-n", ENV,
                "--storage-name", MODEL_STORAGE_NAME, *rgflags(sub))
    af = (config.get("properties") or {}).get("azureFile") if isinstance(config, dict) else None
    if not isinstance(af, dict) or (af.get("accountName"), af.get("shareName"), af.get("accessMode")) != (
            MODEL_ACCOUNT, MODEL_SHARE, "ReadOnly"):
        raise SafetyError("Expected private Azure Files environment storage is not ReadOnly")


def check_preflight(sub, j):
    if not owned(j.get("tags"), feature=True):
        raise SafetyError("Job must be tagged RetailGrowthAI DEV Feature5")
    env = az("containerapp", "env", "show", "-n", ENV, *rgflags(sub))
    if (not isinstance(env, dict) or env.get("name") != ENV or
            str(env.get("location", "")).lower().replace(" ", "") != "eastus" or
            not owned(env.get("tags"), feature=True)):
        raise SafetyError("Expected East US Feature5 environment not found")
    p = j.get("properties") or {}
    config = p.get("configuration") or {}
    manual = config.get("manualTriggerConfig") or {}
    if str(config.get("triggerType", "")).lower() != "manual":
        raise SafetyError("Only Manual jobs; no automatic schedule/queue")
    if type(config.get("replicaRetryLimit")) is not int or config["replicaRetryLimit"] != 0:
        raise SafetyError("Automatic GPU retries must be zero")
    timeout = config.get("replicaTimeout")
    if type(timeout) is not int or not 1 <= timeout <= 1800:
        raise SafetyError("GPU timeout must be between 1 and 1800 seconds")
    if manual.get("parallelism") != 1 or manual.get("replicaCompletionCount") != 1:
        raise SafetyError("Require one replica and one completion")
    if not str(p.get("environmentId", "")).lower().endswith("/managedenvironments/" + ENV):
        raise SafetyError("Job linked to unexpected environment")
    profiles = (env.get("properties") or {}).get("workloadProfiles") or []
    matching = [x for x in profiles if isinstance(x, dict) and x.get("name") == p.get("workloadProfileName")]
    if len(matching) != 1 or matching[0].get("workloadProfileType") != PROFILE_TYPE:
        raise SafetyError("Only A100 Consumption GPU supported; V100 is not this GPU")
    template = p.get("template") or {}
    containers = template.get("containers") or []
    if len(containers) != 1 or template.get("initContainers"):
        raise SafetyError("Require one worker container and no init containers")
    check_model_share_mount(sub, j)
    if not re.fullmatch(r"[^@\s]+@sha256:[0-9a-fA-F]{64}", str(containers[0].get("image", ""))):
        raise SafetyError("Immutable image digest required")
    usage = az("containerapp", "env", "list-usages", "-n", ENV, *rgflags(sub))
    if isinstance(usage, dict):
        usage = usage.get("value")
    if not isinstance(usage, list):
        raise SafetyError("A100 quota unreadable")
    rows = [x for x in usage if isinstance(x, dict) and "NCA100" in str(
        x.get("name", {}).get("value", "") if isinstance(x.get("name"), dict) else x.get("name", "")).upper()]
    if len(rows) != 1:
        raise SafetyError("A100 quota missing/ambiguous")
    try:
        available = float(rows[0]["limit"]) - float(rows[0].get("currentValue", rows[0].get("value", 0)))
    except (KeyError, TypeError, ValueError) as exc:
        raise SafetyError("Invalid A100 quota response") from exc
    if available < 1:
        raise SafetyError("No unused A100 quota")

def status(sub):
    if job(sub) is None:
        print("SAFE: Feature5 GPU job not provisioned, no execution")
        return
    states = executions(sub)
    for name, state in states:
        print(f"{name}: {state}")
    if any(s not in TERMINAL for _, s in states):
        raise SafetyError("A GPU execution may still be billing; invoke stop")
    print("No active execution reported. Storage/registry/logging can still charge.")


def require_priced_test_envelope(j):
    """Read operator-verified quote inputs; not Azure billing enforcement."""
    def amount(name, allow_zero=False):
        raw = os.getenv(name, "").strip()
        try:
            value = Decimal(raw)
        except (InvalidOperation, ValueError) as exc:
            raise SafetyError("Missing/invalid operator cost quote: " + name) from exc
        if not value.is_finite() or (value < 0 if allow_zero else value <= 0):
            raise SafetyError("Non-positive/non-finite quote: " + name)
        return value
    if os.getenv("RETAIL_F5_COST_QUOTE_CURRENCY") != "USD":
        raise SafetyError("A reviewed USD-denominated A100 quote is required")
    quote_id = os.getenv("RETAIL_F5_COST_QUOTE_REFERENCE", "").strip()
    if len(quote_id) < 12 or len(quote_id) > 160:
        raise SafetyError("Independent A100 quote reference is required")
    seconds = ((j.get("properties") or {}).get("configuration") or {}).get("replicaTimeout")
    if type(seconds) is not int or not 1 <= seconds <= 1800:
        raise SafetyError("Cannot price an unknown GPU execution timeout")
    rate = amount("RETAIL_F5_QUOTED_ALL_IN_USD_PER_GPU_SECOND")
    fixed = amount("RETAIL_F5_QUOTED_FIXED_OVERHEAD_USD", allow_zero=True)
    limit = amount("RETAIL_F5_OWNER_APPROVED_PER_TEST_MAX_USD")
    reserved = rate * Decimal(seconds) + fixed
    if reserved > limit:
        raise SafetyError("Maximum test runtime + overhead exceeds approved test budget")
    # This is admission gating, NOT a cloud-enforced USD charge ceiling.
    print(f"Operator quote check: worst-case USD {reserved} <= approved USD {limit}; "
          "validate actual Azure invoice and stop separately")
    return reserved


def require_approved_runtime_image(j):
    """Paid start must use the exact operator-reviewed immutable image, not just any digest.

    This is independent of the model checksum and price approvals. A digest
    formatted correctly but not explicitly approved must never pass.
    """
    expected = os.getenv("RETAIL_F5_REVIEWED_RUNTIME_IMAGE", "").strip()
    actual = ((((j.get("properties") or {}).get("template") or {}).get("containers") or [{}])[0].get("image") or "")
    pattern = r"[^@\s]+@sha256:[0-9a-fA-F]{64}"
    if not re.fullmatch(pattern, expected) or actual != expected:
        raise SafetyError("Paid start requires the exact reviewed OCI image digest")
    return expected


def start(sub, execute, acknowledged):
    j = job(sub)
    if j is None:
        raise SafetyError("Manual GPU job not provisioned; cannot start")
    check_preflight(sub, j)
    if any(s not in TERMINAL for _, s in executions(sub)):
        raise SafetyError("GPU execution already active/uncertain; duplicate start blocked")
    print("A100 preflight passed: Manual, one replica, no retry, <=30m, pinned image")
    if not execute:
        print("DRY RUN: no paid GPU started")
        return
    if (not acknowledged or os.getenv("RETAIL_F5_PAID_RUN_APPROVED") != "YES" or
            os.getenv("RETAIL_F5_MODEL_LICENSE_APPROVED") != "YES"):
        raise SafetyError("Paid start requires cost acknowledgment and both YES approval flags")
    require_priced_test_envelope(j)
    require_approved_runtime_image(j)
    az("containerapp", "job", "start", "-n", JOB, *rgflags(sub))
    print("Paid start requested. Inspect execution and stop after gathering evidence.")

def stop(sub):
    # Even a misconfigured job must be stoppable; do not require start preflight.
    if job(sub) is None:
        print("SAFE: no Feature5 GPU job exists")
        return
    print("Requesting STOP on all executions of exact DEV Feature5 job")
    az("containerapp", "job", "stop", "-n", JOB, *rgflags(sub))
    for attempt in range(8):
        if not any(s not in TERMINAL for _, s in executions(sub)):
            print("STOP CONFIRMED by Azure execution list; check ancillary charges")
            return
        if attempt < 7:
            time.sleep(3)
    raise SafetyError("STOP requested but not confirmed: check Azure Portal immediately")

def main(args=None):
    ap = argparse.ArgumentParser(description="Guarded no-provisioning A100 job control")
    ap.add_argument("action", choices=["status", "start", "stop"])
    ap.add_argument("--gpu", default="A100")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--acknowledge-paid-cost", action="store_true")
    a = ap.parse_args(args)
    try:
        if a.gpu.upper() != "A100":
            raise SafetyError("Existing Azure quota is A100, not V100; V100 unsupported")
        sub = subscription()
        check_group(sub)
        if a.action == "status":
            status(sub)
        elif a.action == "start":
            start(sub, a.execute, a.acknowledge_paid_cost)
        else:
            stop(sub)
        return 0
    except SafetyError as exc:
        print(f"BLOCKED / UNCONFIRMED: {exc}", file=sys.stderr)
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
