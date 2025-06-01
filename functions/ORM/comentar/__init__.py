import json, azure.functions as func
from shared.dtos import ComentarioDTO
from shared.database import get_session
from shared.models import Comentario
from pydantic import ValidationError
from sqlalchemy import select
import datetime

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        dto = ComentarioDTO(**req.get_json())
    except ValidationError as e:
        return func.HttpResponse(e.json(), status_code=400)

    async for session in get_session():
        async with session.begin():
            # regla simple: permitir 1 comentario duplicado? -> se omite
            comentario = Comentario(
                propuesta_id=dto.propuesta_id,
                usuario_id=dto.usuario_id,
                contenido=dto.contenido,
                estado="pendiente",
            )
            session.add(comentario)
        await session.commit()

    return func.HttpResponse(json.dumps({"msg": "Comentario enviado"}), mimetype="application/json")
