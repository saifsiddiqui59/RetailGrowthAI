"""Azure Functions v2 HTTP entrypoint; cloud deployment is NOT performed by CI."""
import json
import os
from request_diagnostics import RequestDiagnostics

import azure.functions as func

from http_api import HTTPAPI
from security import SupabaseJWTVerifier
from tenant_store import TenantStore
from queue_adapter import AzurePlanningQueue, AzureRenderQueue
from admin_store import AdminStore
from planning_worker import process_campaign
from render_api import RenderAPI
from render_worker import process_render
from private_media import PrivateMedia
from recovery_runtime import dispatch_outbox, record_poison, reconcile_and_dispatch

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def build_api():
    # Fail closed when environment settings are absent or malformed.
    url = os.environ["RETAIL_SUPABASE_URL"]
    key = os.environ["RETAIL_SUPABASE_PUBLISHABLE_KEY"]
    # Queue is only usable if an existing Azure Storage Queue has been configured.
    connection = os.environ.get("RETAIL_STORAGE")
    queue = AzurePlanningQueue(connection) if connection else None
    store = TenantStore(url, key)
    admin_key = os.environ.get("RETAIL_SUPABASE_SERVICE_ROLE_KEY")
    admin = AdminStore(url, admin_key) if admin_key else None
    render_api = (
        RenderAPI(store, admin, AzureRenderQueue(connection), durable_outbox=True)
        if connection and admin else None
    )
    return HTTPAPI(SupabaseJWTVerifier(url), store, queue, render_api,
                   failure_store=admin, durable_outbox=bool(connection and admin))


def dispatch(request, path):
    """One sanitized response path, including malformed JSON and server failures.

    Diagnostics never log customer copy, shop IDs, JWTs, signed links or
    exception details. No automatic POST/PATCH replay is performed.
    """
    diagnostics = RequestDiagnostics(request.method, path)
    try:
        api = build_api()
        try:
            body = request.get_json() if request.method in ("POST", "PATCH") else None
        except ValueError:
            code, payload = 400, {"error": "INVALID_REQUEST"}
        else:
            code, payload = api.handle(
                request.method, path, request.headers.get("Authorization", ""), body
            )
    except (KeyError, ValueError):
        code, payload = 503, {"error": "SERVICE_NOT_CONFIGURED"}
    except Exception:
        # Return a fixed error code; never expose or log secrets from an exception.
        code, payload = 500, {"error": "INTERNAL_ERROR"}
    return func.HttpResponse(
        json.dumps(payload), status_code=code, mimetype="application/json",
        headers=diagnostics.complete(code, payload),
    )

@app.route(route="campaigns", methods=["POST"])
def create_campaign(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns")


@app.route(route="campaigns/{campaign_id}", methods=["GET"])
def read_campaign(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns/" + req.route_params["campaign_id"])


@app.queue_trigger(arg_name="message", queue_name="retail-campaign-planning",
                   connection="RETAIL_STORAGE")
def plan_campaign(message: func.QueueMessage):
    # The message contains ONLY a canonical UUID; no user tokens or media URLs.
    admin = AdminStore(
        os.environ["RETAIL_SUPABASE_URL"],
        os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"],
    )
    cid = message.get_body().decode("ascii")
    process_campaign(
        cid, admin,
        mock_enabled=os.environ.get("RETAIL_ENABLE_MOCK_CAMPAIGNS") == "true",
    )


@app.route(route="campaigns/{campaign_id}/days/{day_id}", methods=["PATCH"])
def save_campaign_day(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns/" + req.route_params["campaign_id"]
                    + "/days/" + req.route_params["day_id"])


@app.route(route="campaigns/{campaign_id}/renders", methods=["POST"])
def create_render(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns/" + req.route_params["campaign_id"] + "/renders")


@app.route(route="render-jobs/{job_id}", methods=["GET"])
def get_render(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/render-jobs/" + req.route_params["job_id"])


@app.route(route="render-jobs/{job_id}/download", methods=["GET"])
def get_render_download(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/render-jobs/" + req.route_params["job_id"] + "/download")


@app.queue_trigger(arg_name="message", queue_name="retail-reel-render",
                   connection="RETAIL_STORAGE")
def render_campaign_reel(message: func.QueueMessage):
    # Queue message contains only a validated job UUID. No paths, tokens or URLs.
    origin = os.environ["RETAIL_SUPABASE_URL"]
    key = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    process_render(
        message.get_body().decode("ascii"),
        AdminStore(origin, key), PrivateMedia(origin, key),
    )


def _recovery_dependencies():
    origin = os.environ["RETAIL_SUPABASE_URL"]
    key = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    connection = os.environ["RETAIL_STORAGE"]
    return (AdminStore(origin, key), AzurePlanningQueue(connection),
            AzureRenderQueue(connection))


@app.timer_trigger(schedule="0 */2 * * * *", arg_name="timer",
                   run_on_startup=False, use_monitor=True)
def recover_stale_jobs(timer: func.TimerRequest):
    # Never silently swallow a database failure; retry on the next scheduled tick.
    admin, planning, rendering = _recovery_dependencies()
    reconcile_and_dispatch(admin, planning, rendering)


@app.queue_trigger(arg_name="message", queue_name="retail-campaign-planning-poison",
                   connection="RETAIL_STORAGE")
def planning_poison(message: func.QueueMessage):
    # A DB receipt is mandatory before the trigger acknowledges/removes poison.
    admin, _, _ = _recovery_dependencies()
    record_poison(admin, "planning", message.get_body())


@app.queue_trigger(arg_name="message", queue_name="retail-reel-render-poison",
                   connection="RETAIL_STORAGE")
def render_poison(message: func.QueueMessage):
    admin, _, _ = _recovery_dependencies()
    record_poison(admin, "render", message.get_body())
