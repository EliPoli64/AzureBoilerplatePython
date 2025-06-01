import json
import azure.functions as func
from typing import Any, Dict, Tuple

from SharedLayer.DbConnector import DbConnector

_INSERT_SQL = """
INSERT INTO dbo.pv_infoIA (infoId, modeloIA, apiKey, token, maxTokens)
VALUES (?, ?, ?, ?, ?);
"""


def _validateBody(body: Dict[str, Any]) -> Tuple[int, str, str, str, int]:
    requiredKeys = {"infoId", "modeloIA", "apiKey", "token", "maxTokens"}
    if not requiredKeys.issubset(body.keys()):
        raise ValueError("JSON must contain 'infoId', 'modeloIA', 'apiKey', 'token' and 'maxTokens'.")

    return (
        int(body["infoId"]),
        str(body["modeloIA"]),
        str(body["apiKey"]),
        str(body["token"]),
        int(body["maxTokens"]),
    )


def main(req: func.HttpRequest) -> func.HttpResponse:  # noqa: N802
    """POST /records – Inserts a record into dbo.pv_infoIA."""
    try:
        body = req.get_json()
        recordParams = _validateBody(body)

        dbConnector = DbConnector()
        dbConnector.executeQuery(_INSERT_SQL, recordParams)

        responseBody = {"message": "Registro creado en pv_infoIA correctamente."}
        return func.HttpResponse(
            json.dumps(responseBody),
            mimetype="application/json",
            status_code=201,
        )
    except ValueError as error:
        return func.HttpResponse(
            json.dumps({"error": str(error)}),
            mimetype="application/json",
            status_code=400,
        )
    except Exception:  # noqa: BLE001
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            mimetype="application/json",
            status_code=500,
        )