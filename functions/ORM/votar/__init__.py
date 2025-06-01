import azure.functions as func
from shared.dtos import VotoDTO
from shared.database import get_session
from shared.models import Voto
from sqlalchemy import select
from pydantic import ValidationError
import json
import base64, datetime

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        dto = VotoDTO(**req.get_json())
    except ValidationError as e:
        return func.HttpResponse(e.json(), status_code=400)

    async for session in get_session():
        async with session.begin():
            exist_stmt = select(Voto).where(
                (Voto.usuario_id == dto.usuario_id) & (Voto.propuesta_id == dto.propuesta_id)
            )
            result = (await session.execute(exist_stmt)).scalar_one_or_none()
            if result:
                return func.HttpResponse(json.dumps({"error": "Ya votaste"}), status_code=409)

            voto = Voto(
                propuesta_id=dto.propuesta_id,
                usuario_id=dto.usuario_id,
                voto_cifrado=base64.b64encode(dto.voto_plano.encode()).decode(),
                fecha=datetime.datetime.utcnow(),
            )
            session.add(voto)
        await session.commit()
    return func.HttpResponse(json.dumps({"msg": "Voto registrado"}), mimetype="application/json")