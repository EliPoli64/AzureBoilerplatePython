import logging, json, os, pyodbc, azure.functions as func

CONN = os.getenv("SqlConnectionString")
SQL  = "EXEC dbo.sp_RepartirDividendos"      # el SP maneja todo internamente

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        with pyodbc.connect(CONN) as cnn, cnn.cursor() as cur:
            cur.execute(SQL)
            cnn.commit()
    except Exception as exc:
        logging.exception("DB error")
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=500)

    return func.HttpResponse(json.dumps({"msg": "Dividendos repartidos"}), mimetype="application/json")
