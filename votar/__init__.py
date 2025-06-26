import azure.functions as func
from shared.dtos import VotoDTO
from shared.database import get_session
from shared.models import Voto
from sqlalchemy import select
from pydantic import ValidationError
import json
from datetime import datetime
import base64
import hashlib 
import uuid 

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        dto = VotoDTO(**req.get_json())
    except ValidationError as e:
        return func.HttpResponse(e.json(), status_code=400)

    try:
        async with get_session() as session:
            async with session.begin():
                voto = Voto(
                    preguntaID = dto.preguntaID,
                    respuestaID = dto.respuestaID,
                    checksum = hashlib.sha256("RespuestaParticipante".encode('utf-8')).digest(),
                    valor = dto.valor,
                    fechaRespuesta = datetime.now(),
                    ncRespuesta = hashlib.sha256("Respuesta".encode('utf-8')).digest(),
                    tokenGUID = str(uuid.uuid4()),
                    pesoRespuesta = dto.pesoRespuesta
                )
                session.add(voto)
                await session.commit()
        return func.HttpResponse(json.dumps({"msg": "Voto registrado"}),
                              mimetype="application/json")

    except Exception as ex:
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            mimetype="application/json",
            status_code=500,
        )