"""HTTP-only Azure Functions Linux Consumption Y1 canary for issue #249.

No retailer credentials, queue/timer triggers, model costs, or access to real API.
"""
import json
from uuid import uuid4
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="p0249/health", methods=["GET"])
def p0249_health(request: func.HttpRequest) -> func.HttpResponse:
    del request
    return func.HttpResponse(
        body=json.dumps({"status": "ok", "canary": "classic-y1-p0249"}),
        mimetype="application/json",
        status_code=200,
        headers={
            "X-Request-ID": str(uuid4()),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
