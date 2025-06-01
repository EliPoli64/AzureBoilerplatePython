import logging
import azure.functions as func
import os
import pyodbc
from shared.dtos import PropuestaDTO
from pydantic import ValidationError
import json

_SQL = "EXEC dbo.sp_CrearActualizarPropuesta @Id=?,@Titulo=?,@Descripcion=?,@UsuarioId?;"

CONN_STR = os.getenv("SqlConnectionString")

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = PropuestaDTO(**req.get_json())
    except ValidationError as ve:
        return func.HttpResponse(ve.json(), status_code=400, mimetype="application/json")

    try:
        with pyodbc.connect(CONN_STR) as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL, data.id, data.titulo, data.descripcion, data.usuario_id)
                conn.commit()
    except Exception as e:
        logging.exception("DB error")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)

    return func.HttpResponse(json.dumps({"message": "Propuesta procesada"}), mimetype="application/json")
