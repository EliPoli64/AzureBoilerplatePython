import json
import azure.functions as func
from shared.dtos import ComentarioDTO
from shared.database import get_session
from shared.models import DetalleComentarios, ComentarioPropuesta
from pydantic import ValidationError
from datetime import datetime


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Crea un comentario:
    1. Inserta el detalle (titulo + cuerpo) en pv_detalleComentarios.
    2. Enlaza ese detalle a la propuesta en pv_comentariosPropuesta.
    """
    try:
        dto = ComentarioDTO(**req.get_json())
    except ValidationError as e:
        return func.HttpResponse(e.json(), status_code=400, mimetype="application/json")

    try:
        async with get_session() as session:
            async with session.begin():
                detalle = DetalleComentarios(
                    titulo=dto.titulo,
                    cuerpo=dto.cuerpo,
                    fechaPublicacion=datetime.utcnow(),
                    usuarioId=dto.usuarioId,
                    organizacionId=dto.organizacionId,
                )
                session.add(detalle)
                await session.flush()

                comentario = ComentarioPropuesta(
                    detalleComentarioId=detalle.detalleComentarioId,
                    estadoComentId=1,
                    propuestaId=dto.propuestaId,
                )
                session.add(comentario)

        return func.HttpResponse(
            json.dumps({"msg": "Comentario registrado correctamente"}),
            mimetype="application/json",
            status_code=201,
        )

    except Exception as ex:
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            mimetype="application/json",
            status_code=500,
        )
