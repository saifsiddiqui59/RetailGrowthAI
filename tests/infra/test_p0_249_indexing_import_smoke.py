"""Exercise real Functions module indexing without HTTP/database/queue packages.

The subprocess runs Python -S with fake Azure decorator plumbing and the real
sanitized RequestDiagnostics module. It must index every existing entrypoint
without importing JWT, PostgREST, Azure Storage Queue, poster, or video workers.
This is an offline import boundary, NOT Azure production latency evidence.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "azure-functions" / "campaign-api"
CODE = r'''
import importlib.util
import sys
import types
import time

azure = types.ModuleType("azure")
azure.__path__ = []
functions = types.ModuleType("azure.functions")
class FunctionApp:
    def __init__(self, **kwargs):
        self.registered = []
    def _decorate(self, typ, **kwargs):
        def wrapped(fn):
            self.registered.append((typ, fn.__name__))
            return fn
        return wrapped
    def route(self, **kwargs):
        return self._decorate("http", **kwargs)
    def queue_trigger(self, **kwargs):
        return self._decorate("queue", **kwargs)
    def timer_trigger(self, **kwargs):
        return self._decorate("timer", **kwargs)
class AuthLevel:
    ANONYMOUS = object()
for key, value in {
    "FunctionApp": FunctionApp, "AuthLevel": AuthLevel,
    "HttpRequest": type("HttpRequest", (), {}),
    "HttpResponse": type("HttpResponse", (), {}),
    "QueueMessage": type("QueueMessage", (), {}),
    "TimerRequest": type("TimerRequest", (), {}),
}.items():
    setattr(functions, key, value)
azure.functions = functions
sys.modules["azure"] = azure
sys.modules["azure.functions"] = functions
sys.path.insert(0, sys.argv[1])

start = time.monotonic()
spec = importlib.util.spec_from_file_location("rgai_index_probe", sys.argv[1] + "/function_app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
elapsed = time.monotonic() - start
assert elapsed < 5, "Index import unexpectedly slow"
routes = {name for kind, name in module.app.registered if kind == "http"}
queues = {name for kind, name in module.app.registered if kind == "queue"}
timers = {name for kind, name in module.app.registered if kind == "timer"}
assert {"read_campaign","create_campaign","save_campaign_day","get_render",
        "get_poster_draft","request_poster_render"}.issubset(routes)
assert {"plan_campaign","render_campaign_reel","planning_poison",
        "render_poison","render_campaign_poster"}.issubset(queues)
assert {"recover_stale_jobs","dispatch_onboarding_emails",
        "dispatch_pending_posters"}.issubset(timers)
assert not set(sys.modules) & {
    "http_api", "security", "tenant_store", "queue_adapter", "admin_store",
    "planning_worker", "render_worker", "recovery_runtime",
    "poster_admin", "poster_worker", "feature3_v2_api",
}
print("P0249_IMPORT_INDEX_OK")
'''


def test_minimal_function_indexing_without_installed_backend_packages():
    proc = subprocess.run(
        [sys.executable, "-S", "-c", CODE, str(SERVICE)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=15,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip() == "P0249_IMPORT_INDEX_OK"
