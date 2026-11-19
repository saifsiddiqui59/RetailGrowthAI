"""Legacy Python v1 metadata canary to isolate Azure Functions indexing (#249)."""
import json
import uuid
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return func.HttpResponse(
        json.dumps({"status": "ok", "canary": "classic-y1-v1-p0249"}),
        status_code=200,
        mimetype="application/json",
        headers={"X-Request-ID": str(uuid.uuid4()), "Cache-Control": "no-store"},
    )
