import logging, json, os, pyodbc, azure.functions as func
from shared.dtos import InversionDTO
from pydantic import ValidationError

CONN = os.getenv("SqlConnectionString")
SQL  = "EXEC dbo.sp_Invertir @PropuestaId=?,@UsuarioId=?,@Monto=?"

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = InversionDTO(**req.get_json())
    except ValidationError as e:
        return func.HttpResponse(e.json(), status_code=400)

    try:
        with pyodbc.connect(CONN) as cnn, cnn.cursor() as cur:
            cur.execute(SQL, data.propuesta_id, data.usuario_id, data.monto)
            cnn.commit()
    except Exception as exc:
        logging.exception("DB error")
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=500)

    return func.HttpResponse(json.dumps({"msg": "Inversión registrada"}), mimetype="application/json")
