import json
import random
import azure.functions as func
from datetime import datetime
from shared.dtos import ComentarioDTO
from shared.database import get_session
from shared.models import (
    DetalleComentarios, ComentarioPropuesta, Propuesta, Documento,
    IaAnalisis, Log, EstadoComentario, Usuario, UsuarioPermiso, Permiso
)
from cryptography.fernet import Fernet
from sqlalchemy import select
import hashlib
import re

# Clave de cifrado simulada (en práctica debe estar segura)
CLAVE_CIFRADO = Fernet.generate_key()


def generarChecksum(valor: str) -> bytes:
    return hashlib.sha256(valor.encode()).digest()


def cifrarContenido(texto: str, clave: bytes) -> str:
    fernet = Fernet(clave)
    return fernet.encrypt(texto.encode()).decode()


def analizarContenido(titulo: str, cuerpo: str) -> dict:
    if not cuerpo or len(cuerpo.strip()) < 10:
        return {"valido": False, "razon": "El cuerpo es demasiado corto"}

    sensible = re.search(r"documento\s+sensibl(e|es)", cuerpo, re.IGNORECASE)
    return {"valido": True, "sensible": bool(sensible)}


async def usuarioEsValido(session, usuarioId: int) -> bool:
    stmt = (
        select(Usuario)
        .join(UsuarioPermiso)
        .where(
            Usuario.userid == usuarioId,
            UsuarioPermiso.enabled == True,
            UsuarioPermiso.deleted == False,
        )
    )

    stmt = stmt.join(Permiso).where(Permiso.permissionId == 9)

    result = await session.execute(stmt)
    return result.scalar() is not None


async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        dto = ComentarioDTO(**req.get_json())
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=400, mimetype="application/json"
        )

    async with get_session() as session:
        async with session.begin():

            if not await usuarioEsValido(session, dto.usuarioId):
                return func.HttpResponse(
                    json.dumps({"error": "Usuario no autorizado"}),
                    mimetype="application/json",
                    status_code=403,
                )

            propuesta = await session.get(Propuesta, dto.propuestaId)
            if not propuesta or not bool(propuesta.comentarios):
                return func.HttpResponse(
                    json.dumps({"error": "La propuesta no permite comentarios"}),
                    mimetype="application/json",
                    status_code=403,
                )

            resultado = analizarContenido(dto.titulo, dto.cuerpo)
            estadoNombre = "Pendiente de Revisión" if resultado["valido"] else "Rechazado"

            estadoQuery = await session.execute(
                select(EstadoComentario).where(EstadoComentario.nombre == estadoNombre)
            )
            estado = estadoQuery.scalar_one()
            ahora = datetime.utcnow()

            cuerpoAlmacenar = cifrarContenido(dto.cuerpo, CLAVE_CIFRADO) if resultado.get("sensible") else dto.cuerpo

            detalle = DetalleComentarios(
                titulo=dto.titulo,
                cuerpo=cuerpoAlmacenar,
                fechaPublicacion=ahora,
                usuarioId=dto.usuarioId,
                organizacionId=dto.organizacionId,
            )
            session.add(detalle)
            await session.flush()

            comentario = ComentarioPropuesta(
                detalleComentarioId=detalle.detalleComentarioId,
                estadoComentId=estado.estadoComentId,
                propuestaId=dto.propuestaId,
            )
            session.add(comentario)
            await session.flush()

            documentoId = None
            if resultado.get("sensible"):
                documento = Documento(
                    nombre=f"comentario_{detalle.detalleComentarioId}.txt",
                    fechaCreacion=ahora,
                    tipoDocumentoID=11,
                    estadoDocumentoID=1,
                    ultimaModificacion=ahora,
                    esActual=True,
                    idLegal=f"{dto.usuarioId}_{detalle.detalleComentarioId}",
                    checksum=generarChecksum(cuerpoAlmacenar),
                )
                session.add(documento)
                await session.flush()

                documentoId = documento.documentoID

                analisis = IaAnalisis(
                    fechaSolicitud=ahora,
                    iaEstadoID=1,
                    fechaComienzo=ahora,
                    fechaFinalizacion=ahora,
                    infoid=random.randint(1, 50),
                    contextoID=1,
                    documentoID=documentoId,
                )
                session.add(analisis)

            log = Log(
                descripcion="Comentario registrado" if resultado["valido"] else "Comentario rechazado",
                timestamp=ahora,
                computador="API-Comentarios",
                usuario=str(dto.usuarioId),
                trace=f"ComentarioID={detalle.detalleComentarioId};Estado={estadoNombre}",
                refId1=dto.propuestaId,
                refId2=detalle.detalleComentarioId,
                valor1=dto.titulo,
                valor2="Sensible" if resultado.get("sensible") else "Normal",
                checksum=generarChecksum(f"{dto.usuarioId}|{dto.propuestaId}|{ahora}"),
                tipologid=1,
                origenlogid=1,
                logseveridadid=1,
            )
            session.add(log)

            if not resultado["valido"]:
                return func.HttpResponse(
                    json.dumps({"msg": "Comentario rechazado", "razon": resultado["razon"]}),
                    mimetype="application/json",
                    status_code=400,
                )

    return func.HttpResponse(
        json.dumps({"msg": "Comentario registrado correctamente"}),
        mimetype="application/json",
        status_code=201,
    )

"""
Función principal: main(req: func.HttpRequest) -> func.HttpResponse
Nombre: comentar

Parámetros de entrada (esperados en el JSON del body):
    - titulo (str): Título del comentario a registrar.
    - cuerpo (str): Contenido textual del comentario. Puede incluir términos sensibles.
    - usuarioId (int): ID del usuario que realiza el comentario.
    - organizacionId (int): ID de la organización a la que pertenece el usuario.
    - propuestaId (int): ID de la propuesta sobre la cual se hace el comentario.

Lógica interna:
    1. Se valida y deserializa el DTO de entrada usando ComentarioDTO.
    2. Se verifica si el usuario tiene el permiso `permissionId = 9`, esté habilitado y no eliminado.
    3. Se consulta si la propuesta correspondiente permite comentarios (`propuesta.comentarios == True`).
    4. Se analiza el contenido del comentario para detectar si es sensible mediante expresión regular.
        - Si es sensible, se cifra el contenido usando `Fernet` y se genera un hash con SHA-256.
    5. Se crea un registro en las siguientes tablas:
        - `DetalleComentarios` (comentario en sí)
        - `ComentarioPropuesta` (vinculación con propuesta)
        - `Documento` (solo si el comentario es sensible)
        - `IaAnalisis` (si se creó documento)
        - `Log` (registro general del evento)
    6. Se devuelve una respuesta:
        - 201 Created si el comentario fue aceptado y registrado.
        - 400 Bad Request si el comentario es inválido o fue rechazado por alguna razón.
        - 403 Forbidden si el usuario no está autorizado o la propuesta no acepta comentarios.

Ejemplo de uso (varía con cada llenado de la BD, hay que seleccionar un usuario que tenga permisos de
comentar en propuestas, esto se puede verificar con un simple SELECT en la BD):
{
  "titulo": "Opinión sobre la propuesta X",
  "cuerpo": "Este comentario incluye un documento sensible que debe ser analizado.",
  "usuarioId": 16,
  "organizacionId": 1,
  "propuestaId": 6
}

SELECT para verificar usuarios:
select * from pv_usuariosPermisos

Bitácora de lo acontecido:
- Se definió función de validación `usuarioEsValido` con join a `UsuarioPermiso` y `Permiso`.
- Se añadió análisis de contenido (`analizarContenido`) con criterio de "documento sensible".
- Se implementó cifrado con `Fernet` y generación de `checksum` con `hashlib.sha256`.
- Se asegura persistencia en `pv_documento` y `pv_iaAnalisis` solo si el contenido es sensible.
- Se crea un `Log` detallado de cada evento con trazabilidad de IDs y estado final.
- Compatible con Azure Functions y SQLAlchemy async con manejo transaccional (`session.begin()`).
"""
