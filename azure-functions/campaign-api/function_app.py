"""Azure Functions v2 HTTP entrypoint; cloud deployment is NOT performed by CI."""
import json
import os

import azure.functions as func

from http_api import HTTPAPI
from security import SupabaseJWTVerifier
from tenant_store import TenantStore
from queue_adapter import AzurePlanningQueue
from admin_store import AdminStore
from planning_worker import process_campaign

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def build_api():
    # Fail closed when environment settings are absent or malformed.
    url = os.environ["RETAIL_SUPABASE_URL"]
    key = os.environ["RETAIL_SUPABASE_PUBLISHABLE_KEY"]
    # Queue is only usable if an existing Azure Storage Queue has been configured.
    connection = os.environ.get("RETAIL_STORAGE")
    queue = AzurePlanningQueue(connection) if connection else None
    return HTTPAPI(SupabaseJWTVerifier(url), TenantStore(url, key), queue)


def dispatch(request, path):
    try:
        api = build_api()
        try:
            body = request.get_json() if request.method == "POST" else None
        except ValueError:
            return func.HttpResponse('{"error":"INVALID_REQUEST"}', status_code=400,
                                     mimetype="application/json")
        code, payload = api.handle(
            request.method, path, request.headers.get("Authorization", ""), body
        )
    except (KeyError, ValueError):
        code, payload = 503, {"error": "SERVICE_NOT_CONFIGURED"}
    return func.HttpResponse(
        json.dumps(payload), status_code=code, mimetype="application/json",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
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
