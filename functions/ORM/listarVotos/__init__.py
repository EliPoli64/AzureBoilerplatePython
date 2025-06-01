import json, azure.functions as func
from shared.database import get_session
from shared.models import Voto
from sqlalchemy import select

async def main(req: func.HttpRequest) -> func.HttpResponse:
    uid = req.route_params.get("usuarioId")
    if not uid or not uid.isdigit():
        return func.HttpResponse("usuarioId inválido", status_code=400)

    rows = []
    async for session in get_session():
        stmt = (
            select(Voto.propuesta_id, Voto.fecha)
            .where(Voto.usuario_id == int(uid))
            .order_by(Voto.fecha.desc())
            .limit(5)
        )
        rows = (await session.execute(stmt)).all()

    return func.HttpResponse(json.dumps([dict(r) for r in rows]), mimetype="application/json")
