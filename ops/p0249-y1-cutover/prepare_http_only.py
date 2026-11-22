#!/usr/bin/env python3
"""Source-only Y1 *HTTP* package conversion for Issue #249.

Uses the existing reviewed full Flex ZIP as input, preserving exact HTTP API,
JWT/RLS/store/queue/outbox code and pinned FFmpeg/media bytes. Strips ONLY the
known queue/timer Azure registrations from the nested original function_app.
Background workers remain on Flex until a separately tested single-owner
transition; this artifact must never be mistaken for complete Flex retirement.

No Azure login, deploy, secrets, network requests, appsettings or stop/delete.
"""
from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "azure-functions/campaign-api/function_app.py"
MEMBER = "azure-functions/campaign-api/function_app.py"
HOST = ROOT / "ops/p0249-y1-v1-canary/host.json"
SHORT_HOST = ROOT / "ops/p0249-y1-cutover/host-short-workers.json"

# Explicitly pin the functions actually registered in the original Flex
# source. Any newly added worker or HTTP route demands a new affected review.
WORKERS = frozenset({
    "plan_campaign", "render_campaign_reel", "recover_stale_jobs",
    "planning_poison", "render_poison", "dispatch_onboarding_emails",
    "dispatch_pending_posters", "render_campaign_poster",
    "feature2_collect_india_trends",
})
HTTP = frozenset({
    "feature3_registered_source", "feature3_private_png_download",
    "feature3_private_png", "feature3_private_job_history",
    "feature3_gpu_private_download", "list_feature3_models",
    "register_feature3_model_original", "import_feature3_pending_model",
    "review_feature3_model", "revoke_feature3_model", "feature3_designs",
    "create_campaign", "read_campaign", "create_poster_draft",
    "list_saved_posters", "get_poster_draft", "select_poster_banner",
    "request_poster_render", "read_poster_render", "download_poster_render",
    "save_campaign_day", "create_render", "get_render", "get_render_download",
    "get_retailer_trends", "create_retailer_trend_draft",
    "improve_retailer_prompt", "improve_retailer_prompt_with_ai",
    "create_retailer_trend_draft_with_ai", "create_private_voicestudio_job",
    # Seven exact Feature2→Feature4 routes newly integrated in main
    # 6c376c3a; never replace their reviewed code with the stale 30-route API.
    "create_feature4_render", "get_feature4_render", "download_feature4_render",
    "issue_feature4_creative_plan", "read_feature4_creative_plan",
    "review_feature4_creative_plan", "revoke_feature4_creative_plan",
})
CORE_HTTP = frozenset({
    "create_campaign", "read_campaign", "save_campaign_day", "create_render",
    "get_render", "get_render_download", "create_poster_draft",
    "get_poster_draft", "list_saved_posters", "select_poster_banner",
    "request_poster_render", "read_poster_render", "download_poster_render",
    "create_feature4_render", "get_feature4_render", "download_feature4_render",
    "issue_feature4_creative_plan", "read_feature4_creative_plan",
    "review_feature4_creative_plan", "revoke_feature4_creative_plan",
})


def registrations(source: bytes):
    tree = ast.parse(source.decode("utf-8"))
    methods = {}
    locations = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        marked = []
        for decorator in node.decorator_list:
            if (not isinstance(decorator, ast.Call)
                or not isinstance(decorator.func, ast.Attribute)
                or not isinstance(decorator.func.value, ast.Name)
                or decorator.func.value.id != "app"):
                # Helpers have no app decorators; any nonstandard decorator on a
                # registered handler changes code and must be reviewed.
                continue
            marked.append(decorator.func.attr)
        if marked:
            if len(marked) != 1 or marked[0] not in {
                    "route", "queue_trigger", "timer_trigger"}:
                raise ValueError("Unknown/multiple Azure Function registration")
            methods[node.name] = marked[0]
            locations[node.name] = (
                min(d.lineno for d in node.decorator_list) - 1,
                node.end_lineno,
            )
    return methods, locations


def strip_only_background_triggers(source: bytes) -> bytes:
    methods, positions = registrations(source)
    names = set(methods)
    if (names != WORKERS | HTTP
        or {name for name in names if methods[name] != "route"} != WORKERS
        or {name for name in names if methods[name] == "route"} != HTTP
        or not CORE_HTTP <= names):
        raise ValueError("Original Flex registrations drifted; Y1 source review required")
    text = source.decode("utf-8").splitlines(keepends=True)
    deleted = set()
    for name in WORKERS:
        start, end = positions[name]
        if start < 0 or end > len(text) or not start < end:
            raise ValueError("Invalid worker source span")
        if deleted.intersection(range(start, end)):
            raise ValueError("Overlapping worker source spans")
        deleted.update(range(start, end))
    # Reuse original byte-for-byte HTTP handlers and build_api, rather than
    # reimplementing token verification, billing or queue/outbox behavior.
    # Keep the existing Y1 health contract unchanged through replacement.
    # Only original HTTP code is copied; this is the sole additive health handler.
    health = '''
@app.route(route="p0249/health", methods=["GET"])
def p0249_health(req: func.HttpRequest) -> func.HttpResponse:
    import uuid
    del req
    return func.HttpResponse(
        json.dumps({"status":"ok","canary":"classic-y1-v1-p0249"}),
        status_code=200, mimetype="application/json",
        headers={"X-Request-ID":str(uuid.uuid4()),"Cache-Control":"no-store"},
    )
'''
    result = ("".join(line for i, line in enumerate(text) if i not in deleted)
              + health).encode()
    staged, _ = registrations(result)
    if staged != {name: "route" for name in HTTP | {"p0249_health"}}:
        raise ValueError("Y1 package registered a background trigger")
    compile(result, str(ORIGINAL), "exec")
    return result


def strip_only_long_render_trigger(source: bytes) -> bytes:
    """Stage only short bounded background consumers after Flex handoff.

    The 780-second FFmpeg queue MUST move to the separate 1800-second CPU
    job; classic Consumption Y1 cannot run it safely under its 600s cap.
    This variant MUST NOT be deployed while any Flex consumers are active.
    """
    original, spans = registrations(source)
    if (set(original) != HTTP | WORKERS
            or {name for name in HTTP if original[name] != "route"}
            or any(original[name] not in ("queue_trigger", "timer_trigger")
                   for name in WORKERS)
            or original["render_campaign_reel"] != "queue_trigger"):
        raise ValueError("Unreviewed original worker registration drift")
    text = source.decode("utf-8").splitlines(keepends=True)
    start, end = spans["render_campaign_reel"]
    if not 0 <= start < end <= len(text):
        raise ValueError("Unreviewed original render worker source span")
    # Pure source surgery; no worker code is evaluated or queue subscribed.
    base = "".join(line for i, line in enumerate(text)
                   if not start <= i < end).encode()
    # The appended Y1 health route is identical in both stage modes; take
    # it from the verified HTTP-only stage and never fork security logic.
    only_http = strip_only_background_triggers(source)
    health_start = only_http.rfind(b'\n@app.route(route="p0249/health"')
    if health_start < 0:
        raise ValueError("Y1 health handler source missing")
    converted = base + only_http[health_start:]
    staged, _ = registrations(converted)
    expected = {name: "route" for name in HTTP | {"p0249_health"}}
    expected.update({name: original[name] for name in WORKERS
                     if name != "render_campaign_reel"})
    if staged != expected:
        raise ValueError("Y1 classic worker-stage trigger mismatch")
    compile(converted, str(ORIGINAL), "exec")
    return converted


def check_source():
    transformed = strip_only_background_triggers(ORIGINAL.read_bytes())
    if b"@app.queue_trigger" in transformed or b"@app.timer_trigger" in transformed:
        raise ValueError("Y1 core HTTP still registers a worker")
    print("P0249_Y1_FULL_HTTP_ROUTES=" + str(len(HTTP) + 1))
    print("P0249_Y1_BACKGROUND_TRIGGER_REGISTRATIONS=0")
    print("P0249_Y1_HTTP_SOURCE_CHECK=PASS_SOURCE_ONLY_NOT_DEPLOYED")
    short = strip_only_long_render_trigger(ORIGINAL.read_bytes())
    short_methods, _ = registrations(short)
    if ("render_campaign_reel" in short_methods
            or sum(k != "route" for k in short_methods.values()) != len(WORKERS) - 1):
        raise ValueError("Y1 classic long render worker was not removed")
    print("P0249_Y1_SHORT_WORKER_REGISTRATIONS=" + str(len(WORKERS) - 1))
    print("P0249_Y1_SHORT_WORKER_SOURCE_CHECK=PASS_NOT_DEPLOYED")


def convert_zip(source: Path, destination: Path, *, mode: str = "http-only"):
    if mode not in ("http-only", "http-with-short-workers"):
        raise ValueError("Unreviewed Y1 classic package mode")
    # Source ZIP must pass the ORIGINAL release packager's immutable inventory,
    # ELF/FFprobe, licensing, compression and path safety gates.
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location("p0249_original_release_packager",
                                  ROOT / "scripts/deploy/package.py")
    original_packager = module_from_spec(spec)
    spec.loader.exec_module(original_packager)
    original_packager.verify_zip(source)

    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError("Refuse to overwrite any source/previous release artifact")
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise ValueError("Output directory must already exist and be trusted")
    if ROOT in destination.resolve().parents:
        raise ValueError("No generated production ZIP inside the repository")
    expected_source = ORIGINAL.read_bytes()
    transformed = (strip_only_background_triggers(expected_source)
                   if mode == "http-only"
                   else strip_only_long_render_trigger(expected_source))
    # The original Flex's 1200s timeout is invalid on legacy Consumption.
    # HTTP-only uses the already-approved five-GET Y1 host. The separately
    # guarded short-worker stage uses an exact <=600s host with queue bounds.
    y1_host = (HOST if mode == "http-only" else SHORT_HOST).read_bytes()
    host = json.loads(y1_host)
    if (host.get("version") != "2.0"
        or host.get("logging", {}).get("logLevel", {}).get("default") != "Warning"):
        raise ValueError("Unreviewed Y1 host configuration")
    if mode == "http-only":
        if ("functionTimeout" in host or "extensions" in host
                or "extensionBundle" in host):
            raise ValueError("Unreviewed Y1 HTTP-only host configuration")
    else:
        queue = host.get("extensions", {}).get("queues", {})
        if (host.get("functionTimeout") != "00:09:00"
            or queue.get("batchSize") != 1
            or queue.get("newBatchThreshold") != 0
            or queue.get("maxDequeueCount") != 3
            or queue.get("messageEncoding") != "none"
            or host.get("extensionBundle", {}).get("id")
                != "Microsoft.Azure.Functions.ExtensionBundle"):
            raise ValueError("Unreviewed Y1 short-worker host configuration")
    try:
        with ZipFile(source) as original, ZipFile(destination, "x", ZIP_DEFLATED) as y1:
            listing = original.infolist()
            names = [item.filename for item in listing]
            if Counter(names)[MEMBER] != 1 or Counter(names)["host.json"] != 1:
                raise ValueError("Original ZIP lacks reviewed root members")
            for entry in listing:
                data = original.read(entry)
                if entry.filename == MEMBER:
                    if data != expected_source:
                        raise ValueError("Source ZIP does not match the checked-out original")
                    data = transformed
                elif entry.filename == "host.json":
                    data = y1_host
                y1.writestr(entry, data)
        # Full original package was checked by its exact existing verifier.
        # The new Consumption-compatible host intentionally cannot pass the
        # *Flex-only* 20-minute verifier. Compare every other original byte
        # with the independent original; verify archive/metadata/safety again.
        with ZipFile(source) as original, ZipFile(destination) as staged:
            source_members = original.infolist()
            staged_members = staged.infolist()
            if (len(source_members) != len(staged_members)
                or len(source_members) > 120
                or staged.testzip() is not None):
                raise ValueError("Y1 staged ZIP integrity failed")
            if sum(e.file_size for e in staged_members) > original_packager.MAX_UNPACKED_BYTES:
                raise ValueError("Y1 staged ZIP unpacked budget exceeded")
            for old, new in zip(source_members, staged_members):
                if (old.filename != new.filename or
                    old.external_attr != new.external_attr or
                    old.compress_type != new.compress_type or
                    old.date_time != new.date_time):
                    raise ValueError("Unexpected Y1 ZIP member or metadata drift")
                actual = staged.read(new)
                if new.filename == MEMBER:
                    if actual != transformed:
                        raise ValueError("Modified Y1 HTTP source mismatch")
                elif new.filename == "host.json":
                    if actual != y1_host:
                        raise ValueError("Y1 Consumption host.json mismatch")
                elif actual != original.read(old):
                    raise ValueError("Non-HTTP source or worker package byte drift")
            actual_methods, _ = registrations(staged.read(MEMBER))
            if mode == "http-only":
                if any(kind != "route" for kind in actual_methods.values()):
                    raise ValueError("Generated Y1 ZIP contains an unexpected trigger")
            else:
                if ("render_campaign_reel" in actual_methods
                    or set(actual_methods) != HTTP | (WORKERS - {"render_campaign_reel"}) | {"p0249_health"}):
                    raise ValueError("Generated Y1 ZIP contains an unexpected long renderer")
        print("P0249_Y1_PACKAGE_MODE=" + mode)
        print("P0249_Y1_FULL_HTTP_ZIP=STAGED_NOT_DEPLOYED")
        print("P0249_Y1_HTTP_HOST_CLASSIC_CONSUMPTION_SAFE=PASS")
        print("P0249_Y1_WORKER_MIGRATION_REQUIRED=true")
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--output-zip", type=Path)
    parser.add_argument("--mode", choices=("http-only", "http-with-short-workers"),
                        default="http-only")
    args = parser.parse_args()
    if args.check and args.source_zip is None and args.output_zip is None:
        check_source()
    elif not args.check and args.source_zip and args.output_zip:
        convert_zip(args.source_zip, args.output_zip, mode=args.mode)
    else:
        parser.error("Choose --check OR both --source-zip and --output-zip")


if __name__ == "__main__":
    main()
