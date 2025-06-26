import json
import logging
import base64
import azure.functions as func
from shared.database import get_session
from sqlalchemy import text


def bytes_to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode('utf-8')


def json_bytes_serializer(obj):
    if isinstance(obj, bytes):
        return bytes_to_base64(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Procesando petición para repartir dividendos...")

    sp_call = text("EXEC dbo.sp_RepartirDividendos")

    try:
        async with get_session() as session:
            await session.execute(sp_call)
            await session.commit()

        return func.HttpResponse(
            json.dumps({"mensaje": "Dividendos repartidos exitosamente"}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as ex:
        logging.exception("Error al ejecutar el stored procedure")
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            mimetype="application/json",
            status_code=500
        )