import json
import azure.functions as func
from typing import Any, Dict, Tuple

from SharedLayer.DbConnector import DbConnector

_INSERT_SQL = """
INSERT INTO SampleTable (Name, Value) VALUES (?, ?);
"""


def _validateBody(body: Dict[str, Any]) -> Tuple[str, int]:
    if not {"name", "value"}.issubset(body.keys()):
        raise ValueError("JSON must contain 'name' and 'value'.")
    return str(body["name"]), int(body["value"])


def main(req: func.HttpRequest) -> func.HttpResponse:  # noqa: N802
    """POST /records – Inserts a record into Azure SQL."""
    try:
        body = req.get_json()
        name, value = _validateBody(body)

        dbConnector = DbConnector()
        dbConnector.executeQuery(_INSERT_SQL, (name, value))

        responseBody = {"message": "Record created successfully."}
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
    except Exception as exc:  # noqa: BLE001
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            mimetype="application/json",
            status_code=500,
        )
