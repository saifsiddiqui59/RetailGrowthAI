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
from worker_span_store import configured_worker_span_sink
from planning_worker import process_campaign
from render_api import RenderAPI
from poster_draft_api import PosterDraftAPI
from recovery_runtime import dispatch_outbox, record_poison, reconcile_and_dispatch
from notification_store import NotificationStore
from notification_worker import dispatch_notifications, SmtpSender
from poster_render_api import PosterRenderAPI
from feature3_v2_api import Feature3V2API
from feature3_v2_store import Feature3V2Store
from poster_admin import PosterAdmin
from poster_queue import AzurePosterQueue

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
    poster_api = (PosterDraftAPI(store)
                  if os.environ.get("RETAIL_ENABLE_POSTER_DRAFTS") == "true" else None)
    poster_render_api = (PosterRenderAPI(store)
                         if os.environ.get("RETAIL_ENABLE_POSTER_RENDERING") == "true" else None)
    feature3_api = (Feature3V2API(
                        store, Feature3V2Store(url, key),
                        model_review_enabled=(
                            os.environ.get("RETAIL_FEATURE3_MODEL_REVIEW_ENABLED") == "true"))
                    if os.environ.get("RETAIL_FEATURE3_V2_ENABLED") == "true" else None)
    return HTTPAPI(SupabaseJWTVerifier(url), store, queue, render_api,
                   failure_store=admin, durable_outbox=bool(connection and admin),
                   poster_api=poster_api, poster_render_api=poster_render_api,
                   feature3_api=feature3_api)


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

# Source-only endpoint, disabled unless the reviewed Feature3 v2 flag is enabled.
@app.route(route="shops/{shop_id}/feature3-source-assets/{asset_id}",
           methods=["GET"])
def feature3_registered_source(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] +
                    "/feature3-source-assets/" + req.route_params["asset_id"])


# Feature3 private generated-image history is GET-only; paid GPU submit is
# not publicly registered. Inner HTTPAPI verifies signed JWT + current tenant.
@app.route(route="shops/{shop_id}/feature3-gpu-jobs", methods=["GET"])
def feature3_private_job_history(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] +
                    "/feature3-gpu-jobs")


# No public generated GPU image path; existing Feature3 flag defaults OFF.
@app.route(route="shops/{shop_id}/feature3-gpu-jobs/{job_id}/download",
           methods=["GET"])
def feature3_gpu_private_download(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] +
                    "/feature3-gpu-jobs/" + req.route_params["job_id"] + "/download")


# Source-only future endpoints, explicitly disabled in existing DEV/PROD.
@app.route(route="shops/{shop_id}/feature3-models", methods=["GET"])
def list_feature3_models(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] + "/feature3-models")


# Signed retailer-only registration for an ALREADY UPLOADED private PNG.
# No public upload, image approval, service role or GPU generation.
@app.route(route="shops/{shop_id}/feature3-model-originals/register",
           methods=["POST"])
def register_feature3_model_original(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] +
                    "/feature3-model-originals/register")


# Source importer route was handled in HTTPAPI but not previously mounted
# in the Azure Functions route table. Keep review flags OFF by default.
@app.route(route="shops/{shop_id}/feature3-models/import", methods=["POST"])
def import_feature3_pending_model(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] +
                    "/feature3-models/import")


# Source-only human review routes. Both the general Feature3 and the
# *separate* model-review activation flags default OFF. Signed user JWT and
# current role are rechecked in HTTPAPI, Feature3V2API and database RPC.
@app.route(route="shops/{shop_id}/feature3-models/{model_id}/review",
           methods=["POST"])
def review_feature3_model(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] +
                    "/feature3-models/" + req.route_params["model_id"] + "/review")


@app.route(route="shops/{shop_id}/feature3-models/{model_id}/revoke",
           methods=["POST"])
def revoke_feature3_model(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/shops/" + req.route_params["shop_id"] +
                    "/feature3-models/" + req.route_params["model_id"] + "/revoke")


@app.route(route="campaigns/{campaign_id}/days/{day_id}/feature3-designs",
           methods=["GET", "POST"])
def feature3_designs(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns/" + req.route_params["campaign_id"]
                    + "/days/" + req.route_params["day_id"] + "/feature3-designs")


@app.route(route="campaigns", methods=["POST"])
def create_campaign(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns")


@app.route(route="campaigns/{campaign_id}", methods=["GET"])
def read_campaign(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns/" + req.route_params["campaign_id"])


@app.route(route="campaigns/{campaign_id}/posters", methods=["POST"])
def create_poster_draft(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns/" + req.route_params["campaign_id"] + "/posters")


@app.route(route="campaigns/{campaign_id}/days/{day_id}/posters", methods=["GET"])
def list_saved_posters(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/campaigns/" + req.route_params["campaign_id"]
                    + "/days/" + req.route_params["day_id"] + "/posters")


@app.route(route="poster-drafts/{draft_id}", methods=["GET"])
def get_poster_draft(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/poster-drafts/" + req.route_params["draft_id"])


@app.route(route="poster-drafts/{draft_id}/select", methods=["POST"])
def select_poster_banner(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/poster-drafts/" + req.route_params["draft_id"] + "/select")


@app.route(route="poster-drafts/{draft_id}/renders", methods=["POST"])
def request_poster_render(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/poster-drafts/" + req.route_params["draft_id"] + "/renders")


@app.route(route="poster-jobs/{job_id}", methods=["GET"])
def read_poster_render(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/poster-jobs/" + req.route_params["job_id"])


@app.route(route="poster-jobs/{job_id}/download", methods=["GET"])
def download_poster_render(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch(req, "/poster-jobs/" + req.route_params["job_id"] + "/download")


def _trusted_worker_span_sink(admin):
    # Only a separately reviewed, released SQL schema and explicit DEV flag
    # may activate service-only worker span persistence. OFF by default.
    return configured_worker_span_sink(
        admin, os.environ.get("RETAIL_FEATURE_WORKER_SPANS_ENABLED"))


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
        span_sink=_trusted_worker_span_sink(admin),
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
    # Import the heavy FFmpeg engine ONLY on real queue invocation. An HTTP cold
    # start should not import media codecs or the offline renderer.
    from render_worker import process_render
    from private_media import PrivateMedia
    # Queue message contains only a validated job UUID. No paths, tokens or URLs.
    origin = os.environ["RETAIL_SUPABASE_URL"]
    key = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    admin = AdminStore(origin, key)
    process_render(
        message.get_body().decode("ascii"),
        admin, PrivateMedia(origin, key),
        span_sink=_trusted_worker_span_sink(admin),
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


@app.timer_trigger(schedule="0 */10 * * * *", arg_name="timer",
                   run_on_startup=False, use_monitor=True)
def dispatch_onboarding_emails(timer: func.TimerRequest):
    # Explicitly OFF by default. No SMTP connection unless the dedicated
    # RetailGrowthAI sender, URL and feature flag have been configured.
    if os.environ.get("RETAIL_NOTIFICATIONS_ENABLED") != "true":
        return
    store = NotificationStore(
        os.environ["RETAIL_SUPABASE_URL"],
        os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"],
    )
    sender = SmtpSender.from_environment()
    dispatch_notifications(store, sender, enabled=True, limit=8)


@app.timer_trigger(schedule="0 */2 * * * *", arg_name="timer",
                   run_on_startup=False, use_monitor=True)
def dispatch_pending_posters(timer: func.TimerRequest):
    # The queue and database migration must be provisioned under separate
    # RetailGrowthAI DEV authorization before enabling this source-only path.
    if os.environ.get("RETAIL_ENABLE_POSTER_RENDERING") != "true":
        return
    admin = PosterAdmin(os.environ["RETAIL_SUPABASE_URL"],
                        os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"])
    queue = AzurePosterQueue(os.environ["RETAIL_STORAGE"])
    # The poster engine imports Pillow and image fonts; a timer never needs it
    # on an HTTP instance and must not load it during function indexing.
    from poster_worker import dispatch_posters
    admin.reconcile_posters()
    dispatch_posters(admin, queue)


@app.queue_trigger(arg_name="message", queue_name="retail-poster-render",
                   connection="RETAIL_STORAGE")
def render_campaign_poster(message: func.QueueMessage):
    if os.environ.get("RETAIL_ENABLE_POSTER_RENDERING") != "true":
        # Never acknowledge/delete a legitimate queued event if disabled.
        raise RuntimeError("poster worker is not enabled")
    # Heavy Pillow/PNG decoding is worker-only; no eager import in HTTP host.
    from poster_worker import process_poster
    from private_poster_media import PrivatePosterMedia
    origin = os.environ["RETAIL_SUPABASE_URL"]
    key = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    process_poster(message.get_body().decode("ascii"),
                   PosterAdmin(origin,key), PrivatePosterMedia(origin,key))



# Feature #2 routes are additive to v1 and OFF by default. Keep handler
# authorization independent of the other campaign API endpoints.
def build_feature2_api():
    if os.environ.get("RETAIL_ENABLE_FEATURE2") != "true":
        return None
    from feature2_adapter import TrendFeatureAdapter
    from feature2_store import TrendSnapshotStore, TenantDraftStore, authorized_profile_reader
    origin = os.environ["RETAIL_SUPABASE_URL"]
    key = os.environ["RETAIL_SUPABASE_PUBLISHABLE_KEY"]
    service_key = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    tenant = TenantStore(origin, key)
    admin = AdminStore(origin, service_key)
    shared = TrendSnapshotStore(admin)
    # Real paid AI is an independent, strictly OFF-by-default server feature.
    # A valid configuration is not cost approval: the database RPC still
    # checks operator-enabled per-shop budgets/roles/subscriptions atomically.
    ai_service = None
    if os.environ.get("RETAIL_FEATURE2_REAL_AI_ENABLED") == "true":
        required = ("RETAIL_FOUNDRY_ENDPOINT", "RETAIL_FOUNDRY_DEPLOYMENT",
                    "RETAIL_FOUNDRY_API_KEY", "RETAIL_FEATURE2_INPUT_USD_PER_MILLION",
                    "RETAIL_FEATURE2_OUTPUT_USD_PER_MILLION",
                    "RETAIL_FEATURE2_MAX_CALL_USD")
        if all(os.environ.get(name) for name in required):
            from feature2_ai_activation import Feature2AiActivation
            try:
                ai_service = Feature2AiActivation(
                    admin,
                    endpoint=os.environ["RETAIL_FOUNDRY_ENDPOINT"],
                    deployment=os.environ["RETAIL_FOUNDRY_DEPLOYMENT"],
                    api_key=os.environ["RETAIL_FOUNDRY_API_KEY"],
                    input_usd_per_million=float(os.environ["RETAIL_FEATURE2_INPUT_USD_PER_MILLION"]),
                    output_usd_per_million=float(os.environ["RETAIL_FEATURE2_OUTPUT_USD_PER_MILLION"]),
                    approved_max_cost_usd=float(os.environ["RETAIL_FEATURE2_MAX_CALL_USD"]),
                )
            except ValueError:
                # A bad optional model configuration cannot disable ordinary
                # deterministic Feature2 endpoints. Paid AI continues OFF.
                ai_service = None
    return TrendFeatureAdapter(
        SupabaseJWTVerifier(origin), tenant,
        profile_reader=authorized_profile_reader(tenant),
        snapshot_store=shared, draft_store=TenantDraftStore(admin, tenant),
        ai_service=ai_service,
    )


def dispatch_feature2(request, shop_id, *, method, resource="trends"):
    path = "/shops/{shop_id}/" + ({
        "trends": "trend-recommendations", "drafts": "content-drafts",
        "prompt": "improve-prompt", "prompt_ai": "improve-prompt-ai",
        "draft_ai": "content-drafts-ai",
    }[resource])
    ai_mode = resource in ("prompt_ai", "draft_ai")
    diagnostics = RequestDiagnostics(method, path)
    try:
        handler = build_feature2_api()
        if handler is None:
            code, body = 503, {"error": "FEATURE2_DISABLED"}
        else:
            try:
                payload = request.get_json() if method == "POST" else None
            except ValueError:
                code, body = 400, {"error": "INVALID_REQUEST"}
            else:
                if resource in ("prompt", "prompt_ai") and method == "POST":
                    code, body = handler.improve(
                        shop_id, request.headers.get("Authorization", ""), payload,
                        ai_mode=ai_mode)
                elif resource == "drafts" and method == "GET":
                    code, body = handler.list_drafts(
                        shop_id, request.headers.get("Authorization", ""))
                else:
                    code, body = handler.handle(
                        method, shop_id, request.headers.get("Authorization", ""), payload,
                        ai_mode=ai_mode)
    except (KeyError, ValueError):
        code, body = 503, {"error": "TREND_STORAGE_NOT_CONFIGURED"}
    except Exception:
        code, body = 500, {"error": "INTERNAL_ERROR"}
    return func.HttpResponse(
        json.dumps(body), status_code=code, mimetype="application/json",
        headers=diagnostics.complete(code, body),
    )


@app.route(route="shops/{shop_id}/trend-recommendations", methods=["GET"])
def get_retailer_trends(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch_feature2(req, req.route_params["shop_id"], method="GET")


@app.route(route="shops/{shop_id}/content-drafts", methods=["GET", "POST"])
def create_retailer_trend_draft(req: func.HttpRequest) -> func.HttpResponse:
    # Same registered route, distinct signed-in READ and verified WRITE methods;
    # avoid duplicate Azure route definitions during Flex Functions indexing.
    return dispatch_feature2(req, req.route_params["shop_id"],
                             method=req.method.upper(), resource="drafts")


@app.route(route="shops/{shop_id}/improve-prompt", methods=["POST"])
def improve_retailer_prompt(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch_feature2(req, req.route_params["shop_id"],
                             method="POST", resource="prompt")


# Both new model endpoints are additive; original template routes remain
# backwards-compatible and free. No model call without JWT/RLS plus DB budget.
@app.route(route="shops/{shop_id}/improve-prompt-ai", methods=["POST"])
def improve_retailer_prompt_with_ai(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch_feature2(req, req.route_params["shop_id"],
                             method="POST", resource="prompt_ai")


@app.route(route="shops/{shop_id}/content-drafts-ai", methods=["POST"])
def create_retailer_trend_draft_with_ai(req: func.HttpRequest) -> func.HttpResponse:
    return dispatch_feature2(req, req.route_params["shop_id"],
                             method="POST", resource="draft_ai")


@app.timer_trigger(schedule="0 15 5 * * *", arg_name="timer",
                   run_on_startup=False, use_monitor=True)
def feature2_collect_india_trends(timer: func.TimerRequest):
    # Once daily, 05:15 UTC (10:45 India). Leased Supabase claim is also
    # mandatory across host restarts and scale-out. Not per-shop, no GPU/LLM.
    if os.environ.get("RETAIL_FEATURE2_COLLECTION_ENABLED") != "true":
        return
    from datetime import datetime, timezone
    from feature2_store import TrendSnapshotStore
    from ai_agents.trend_runtime import run_daily_collection
    store = TrendSnapshotStore(AdminStore(
        os.environ["RETAIL_SUPABASE_URL"],
        os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"],
    ))
    run_daily_collection(datetime.now(timezone.utc), store)
