import json
import azure.functions as func
from datetime import datetime, timezone

def main(req: func.HttpRequest) -> func.HttpResponse:  # noqa: N802
    """GET /status – Simple health‑check endpoint."""
    utcNow = datetime.now(tz=timezone.utc).isoformat()
    body = {"status": "🟢 OK", "timestamp": utcNow}
    return func.HttpResponse(json.dumps(body), mimetype="application/json", status_code=200)
