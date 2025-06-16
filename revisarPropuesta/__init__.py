import logging, json, os, pyodbc, azure.functions as func

CONN = os.getenv("SqlConnectionString")
SQL  = "EXEC dbo.sp_RevisarPropuesta @Id=?"

def main(req: func.HttpRequest) -> func.HttpResponse:
    pid = req.route_params.get("id")
    if not pid or not pid.isdigit():
        return func.HttpResponse("id inválido", status_code=400)

    try:
        with pyodbc.connect(CONN) as cnn, cnn.cursor() as cur:
            cur.execute(SQL, int(pid))
            cnn.commit()
    except Exception as exc:
        logging.exception("DB error")
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=500)

    return func.HttpResponse(json.dumps({"msg": "Propuesta en revisión"}), mimetype="application/json")
