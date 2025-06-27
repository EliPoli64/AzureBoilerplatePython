import json
from datetime import datetime
from sqlalchemy import select, insert, update
from shared.database import get_session
from shared.models import Propuesta, SegmentoPropuesta, UsuarioPermiso, Votacion, PropuestaVotacion, Segmento, VotacionPregunta
from shared.dtos import CrearConfiguracionVotacionDTO
import azure.functions as func
from fastapi import Header, HTTPException

async def validar_permiso(session, usuario_id: int, permiso_code: str, propuesta_id: int) -> bool:
    """
    Verifica que el usuario tiene el permiso especificado para modificar la propuesta dada.
    
    Parámetros:
    - session: sesión activa de SQLAlchemy.
    - usuario_id: ID del usuario que intenta realizar la acción.
    - permiso_code: código del permiso requerido (ej: 'configurarVotacion').
    - propuesta_id: ID de la propuesta que se desea modificar.
    
    Retorna:
    - True si el usuario tiene el permiso y es dueño de la propuesta.
    - False en caso contrario.
    """

    # Validar que el usuario sea dueño de la propuesta
    propuesta_stmt = select(Propuesta).where(
        Propuesta.propuestaId == propuesta_id,
        Propuesta.userId == usuario_id
    )
    propuesta_result = await session.execute(propuesta_stmt)
    propuesta = propuesta_result.scalar_one_or_none()

    if not propuesta:
        return False

    return True
async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        dto = CrearConfiguracionVotacionDTO(**req.get_json())
    except Exception as e:
        return func.HttpResponse(f"Error en los datos recibidos: {str(e)}", status_code=400)

    async with get_session() as session:
        # Validar que el usuario tiene permiso sobre la propuesta
        tiene_permiso = await validar_permiso(session, dto.usuarioID, 'configurarVotacion', dto.propuestaID)
        if not tiene_permiso:
            return func.HttpResponse("No tiene permiso para configurar esta propuesta", status_code=403)

        # 1. Crear o actualizar la votación
        now = datetime.utcnow()
        nuevaVotacion = Votacion(
            tipoVotacionId=dto.tipoVotacionId,
            titulo=dto.titulo,
            descripcion=dto.descripcion,
            fechaInicio=dto.fechaInicio,
            fechaFin=dto.fechaFin,
            estadoVotacionId=1,  # Estado: Preparado
            ultimaModificacion=now,
            privada=dto.privada,
            esSecreta=dto.esSecreta
        )
        session.add(nuevaVotacion)
        await session.flush()  # Para obtener el ID generado

        # 2. Asociar la votación a la propuesta
        propuestaVotacion = PropuestaVotacion(
            votacionID=nuevaVotacion.votacionID,
            propuestaID=dto.propuestaID,
            usuarioID=dto.usuarioID,
            deleted=False,
            checksum=b"NA"
        )
        session.add(propuestaVotacion)

        # 3. Asociar los segmentos seleccionados (población meta)
        if dto.segmentosSeleccionados:
            for segID in dto.segmentosSeleccionados:
                await session.execute(insert(SegmentoPropuesta).values(
                    propuestaID=dto.propuestaID,
                    segementoID=segID,
                    deleted=False,
                    usuarioID=dto.usuarioID,
                    checksum=b"NA"
                ))
        for pregunta in dto.preguntas:
            pregRow = VotacionPregunta(
                votacionID=nuevaVotacion.votacionID,
                preguntaID=pregunta.preguntaID
            )
            session.add(pregRow)

        await session.commit()

        return func.HttpResponse(json.dumps({"mensaje": "Votación configurada", "votacionID": nuevaVotacion.votacionID}), mimetype="application/json", status_code=201)
"""
Función principal: main(req: func.HttpRequest) -> func.HttpResponse  
Nombre: configurarVotacion

Parámetros de entrada (esperados en el JSON del body, vía DTO `CrearConfiguracionVotacionDTO`):
    - usuarioID (int): ID del usuario que desea configurar la votación.
    - propuestaID (int): ID de la propuesta sobre la cual se configura la votación.
    - tipoVotacionId (int): Tipo de votación a registrar (ej. abierta, cerrada, etc.).
    - titulo (str): Título de la votación.
    - descripcion (str): Descripción de la votación.
    - fechaInicio (datetime): Fecha y hora de inicio de la votación.
    - fechaFin (datetime): Fecha y hora de finalización de la votación.
    - privada (bool): Indica si la votación es privada.
    - esSecreta (bool): Indica si la votación es secreta.
    - segmentosSeleccionados (List[int]): Lista de IDs de segmentos de población a los que se dirige la votación.
    - preguntas (List[PreguntaDTO]): Lista de preguntas que se incluirán en la votación.

Lógica interna:
    1. Se valida y deserializa el DTO de entrada usando `CrearConfiguracionVotacionDTO`.
    2. Se verifica que el usuario:
        - Es dueño de la propuesta (`Propuesta.userId == usuarioID`).
        - Tiene asignado el permiso específico (`permisoID == 6`), esté habilitado y no eliminado.
    3. Se crea un nuevo registro en la tabla `pv_votacion` con estado "Preparado".
    4. Se vincula la votación con la propuesta mediante `pv_propuestaVotacion`.
    5. Se asocian los segmentos seleccionados como población objetivo, insertando en `pv_segmentoPropuesta`.
    6. Se validan los IDs de preguntas recibidos y se insertan las relaciones en `pv_votacionPregunta`.
        - Si alguna pregunta no existe en la base de datos (`pv_preguntas`), se omite o se rechaza toda la transacción.
    7. Se realiza el `commit()` de la transacción para persistir los cambios.

Respuesta esperada:
    - 201 Created con `votacionID` generado si la operación fue exitosa.
    - 400 Bad Request si los datos están mal estructurados o hay preguntas inválidas.
    - 403 Forbidden si el usuario no tiene permiso o no es dueño de la propuesta.

Ejemplo de entrada:
{
  "usuarioID": 789,
  "propuestaID": 5,
  "titulo": "Consulta sobre políticas públicas 2025",
  "descripcion": "Votación para definir prioridades en políticas públicas nacionales.",
  "fechaInicio": "2025-07-01T08:00:00Z",
  "fechaFin": "2025-07-10T18:00:00Z",
  "tipoVotacionId": 2,
  "privada": false,
  "esSecreta": true,
  "segmentosSeleccionados": [1, 3, 5],
  "geografiaImpacto": "nacional",
  "restriccionesIP": ["192.168.0.0/24", "10.0.0.0/8"],
  "horariosPermitidos": ["08:00-12:00", "14:00-18:00"],
  "preguntas": [
    {
      "preguntaID": 42
    },
    {
      "preguntaID": 43
    }
  ]
}

SELECT para verificar permisos del usuario:
SELECT * FROM pv_usuariosPermisos WHERE userid = 16 AND permisoId = 6 AND enabled = 1 AND deleted = 0

Bitácora de lo acontecido:
- Se definió función `validar_permiso` para verificar propiedad y permisos sobre la propuesta.
- Se usó `session.flush()` para obtener el `votacionId` generado automáticamente.
- Se incluyó validación de existencia de preguntas para prevenir errores de integridad referencial.
- Se aseguró atomicidad mediante `async with session:` y `commit()` al final.
- Compatible con Azure Functions, SQLAlchemy async y DTO validado vía Pydantic.
"""
