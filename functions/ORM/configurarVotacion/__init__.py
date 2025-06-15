import json, azure.functions as func
from shared.database import get_session
from shared.models import Propuesta
from sqlalchemy import update

async def main(req: func.HttpRequest) -> func.HttpResponse:
    pid = req.route_params.get("id")
    if not pid or not pid.isdigit():
        return func.HttpResponse("id inválido", status_code=400)

    body = await req.get_json()
    async for session in get_session():
        async with session.begin():
            await session.execute(
                update(Propuesta)
                .where(Propuesta.id == int(pid))
                .values(estado="configurada")
            )
        await session.commit()

    return func.HttpResponse(json.dumps({"msg": "Votación configurada"}), mimetype="application/json")
