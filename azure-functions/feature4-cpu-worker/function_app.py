"""Feature4 native CPU worker candidate, NOT in existing v1 Azure ZIP.

Release must package F4 HyperFrames/Node/FFmpeg and verified service-only
backend dependencies in a separate reviewed artifact. This source alone
does not provision queues or activate a cloud Function App.
"""
import os
from pathlib import Path
from urllib.request import build_opener
import azure.functions as func
from admin_store import AdminStore, _DenyRedirects

app = func.FunctionApp()

# F2→F4 CPU queue/timer are NOT indexed at all until a reviewed worker
# deployment explicitly enables the worker. The default existing DEV package
# does not require the new queue, migration or CPU cost.
if os.environ.get("RETAIL_FEATURE4_CPU_WORKER_ENABLED") == "true":
    # The separately built native artifact must carry its own Node22, FFmpeg,
    # ffprobe, @hyperframes dependencies and headless-browser cache. Never
    # fall back to an unreviewed system executable when a package is missing.
    _root = Path(__file__).resolve().parent
    _bin = _root / "bin"
    _cache = _root / "puppeteer-cache"
    for _executable in ("node", "ffmpeg", "ffprobe"):
        _path = _bin / _executable
        if not _path.is_file() or _path.is_symlink():
            raise RuntimeError("Feature4 native artifact missing packaged executable")
    if not _cache.is_dir() or not (
            _root / "hyperframes" / "node_modules" /
            "@hyperframes" / "producer").is_dir():
        raise RuntimeError("Feature4 native artifact missing browser/renderer")
    os.environ["PATH"] = str(_bin) + os.pathsep + os.environ.get("PATH", "")
    os.environ["PUPPETEER_CACHE_DIR"] = str(_cache)
    _browsers = list(_cache.glob(
        "chrome-headless-shell/*/chrome-headless-shell-linux64/chrome-headless-shell"))
    if len(_browsers) != 1 or _browsers[0].is_symlink():
        raise RuntimeError("Feature4 pinned headless-browser executable not found")
    os.environ["PUPPETEER_EXECUTABLE_PATH"] = str(_browsers[0])

    def _feature4_cpu_dependencies():
        from private_media import PrivateMedia
        from queue_adapter import AzureFeature4CpuQueue
        origin = os.environ["RETAIL_SUPABASE_URL"]
        secret = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
        connection = os.environ["RETAIL_STORAGE"]
        store = AdminStore(origin, secret)
        # Never forward worker-role credentials across HTTP redirects.
        private = PrivateMedia(origin, secret,
                               transport=build_opener(_DenyRedirects()).open)
        return (store, private,
                AzureFeature4CpuQueue(connection))

    @app.queue_trigger(
        arg_name="message", queue_name="retail-feature4-cpu-render",
        connection="RETAIL_STORAGE")
    def feature4_cpu_render_message(message: func.QueueMessage):
        from tenant_store import canonical_uuid
        from feature4_worker_handoff import process_feature4_cpu_render
        admin, media, _ = _feature4_cpu_dependencies()
        job_id = canonical_uuid(message.get_body().decode("ascii", "strict"))
        # A malformed queue message is never interpreted as a worker grant.
        process_feature4_cpu_render(job_id, admin, media)

    @app.queue_trigger(
        arg_name="message", queue_name="retail-feature4-cpu-render-poison",
        connection="RETAIL_STORAGE")
    def feature4_cpu_poison_message(message: func.QueueMessage):
        from recovery_runtime import record_feature4_cpu_poison
        admin, _, _ = _feature4_cpu_dependencies()
        # No job status or credit mutation from a possibly malformed payload.
        record_feature4_cpu_poison(admin, message.get_body())

    @app.timer_trigger(
        schedule="0 */2 * * * *", arg_name="timer", run_on_startup=False)
    def feature4_cpu_dispatch_timer(timer: func.TimerRequest):
        from recovery_runtime import reconcile_feature4_cpu
        admin, _, queue = _feature4_cpu_dependencies()
        reconcile_feature4_cpu(admin, queue)
