import json
import logging
import base64
import azure.functions as func
from shared.dtos import CrearActualizarPropuestaDTO
from shared.database import get_session
from sqlalchemy import text
from pydantic import ValidationError

def bytesAString(b: bytes) -> str:
    return base64.b64encode(b).decode('utf-8')

def json_bytes_serializer(obj):
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode('utf-8')
    raise TypeError(f"Type {type(obj)} not serializable")

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        dto = CrearActualizarPropuestaDTO(**req.get_json())
    except ValidationError as e:
        return func.HttpResponse(e.json(), status_code=400, mimetype="application/json")

    sp_call = text("""
        EXEC dbo.crearActualizarPropuesta
            @PropuestaID = :PropuestaID,
            @CategoriaID = :CategoriaID,
            @Descripcion = :Descripcion,
            @ImgURL = :ImgURL,
            @FechaInicio = :FechaInicio,
            @FechaFin = :FechaFin,
            @Comentarios = :Comentarios,
            @TipoPropuestaID = :TipoPropuestaID,
            @OrganizacionID = :OrganizacionID,
            @SegmentosDirigidosJS = :SegmentosDirigidosJS,
            @SegmentosImpactoJS = :SegmentosImpactoJS,
            @AdjuntosJS = :AdjuntosJS,
            @UsuarioAccion = :UsuarioAccion,
            @EquipoOrigen = :EquipoOrigen
    """)

    try:
        async with get_session() as session:
            params = dto.dict()
            params['Comentarios'] = int(params['Comentarios'])
            result = await session.execute(sp_call, params)
            await session.commit()
            rows = result.fetchall()
            print(f"Rows returned: {len(rows)}")

            resultList = []
            for row in rows:
                rowDict = dict(row._mapping)
                # Convierte checksum si existe
                if 'checksum' in rowDict and isinstance(rowDict['checksum'], bytes): # para debug solamente
                    rowDict['checksum'] = bytesAString(rowDict['checksum'])
                resultList.append(rowDict)
        logging.info(f"Result from SP: {resultList}")
        return func.HttpResponse(
            json.dumps({"result": resultList}, default=json_bytes_serializer),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as ex:
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            mimetype="application/json",
            status_code=500,
        )

"""
Función principal: main(req: func.HttpRequest) -> func.HttpResponse
Nombre: crearActualizarPropuesta

Parámetros de entrada (esperados en el JSON del body):
    - PropuestaID (int | null): ID de la propuesta (null si es nueva).
    - CategoriaID (int): ID de la categoría de la propuesta.
    - Descripcion (str): Texto descriptivo de la propuesta.
    - ImgURL (str): URL de la imagen representativa.
    - FechaInicio (str | null): Fecha de inicio en formato ISO 8601 (opcional).
    - FechaFin (str): Fecha de finalización en formato ISO 8601.
    - Comentarios (bool): Indica si se permiten comentarios en la propuesta.
    - TipoPropuestaID (int): Tipo de propuesta según clasificación.
    - OrganizacionID (int): ID de la organización que crea la propuesta.
    - SegmentosDirigidosJS (str): JSON serializado de IDs de segmentos dirigidos.
    - SegmentosImpactoJS (str): JSON serializado de IDs de segmentos de impacto.
    - AdjuntosJS (str): JSON serializado de documentos adjuntos.
    - UsuarioAccion (int): ID del usuario que realiza la acción.
    - EquipoOrigen (str): Nombre del equipo o servidor de origen.

Lógica interna:
    1. Si la propuesta es nueva (`PropuestaID` es null), se inserta un nuevo registro en `pv_propuestas`.
       - Se calcula el `checksum` con SHA-256.
       - Se asigna estado inicial “En Revisión”.
    2. Si la propuesta existe, se valida que el `UsuarioAccion` sea un proponente principal de la propuesta.
       - Si no lo es, se lanza un error.
       - Se actualiza la propuesta con los campos nuevos y se recalcula el `checksum`.
    3. Se calcula el número de versión siguiente y se inserta en `pv_versionPropuesta`.
    4. Si es una actualización, se marcan como eliminados (`deleted = 1`) los segmentos dirigidos anteriores.
    5. Si se recibe `SegmentosImpactoJS`, se actualizan o insertan los segmentos en `pv_propuestaSegmentosImpacto` con `MERGE`.
    6. Si se reciben `AdjuntosJS`, se insertan los documentos en `pv_documento`, se calcula `checksum`, y se vinculan a la propuesta.
    7. Se crea una entrada en `pv_validacionPropuesta` asociando la nueva versión a un grupo validador.
    8. Se registra en `pv_logs` el evento: creación o actualización de propuesta.
    9. La transacción se confirma; si ocurre error, se revierte todo y se retorna mensaje de error.


Ejemplo de uso (varía con cada llenado de la BD, hay que seleccionar un usuario que tenga permisos de
modificar esa propuesta si no es nula, esto se puede verificar con un simple SELECT en la BD):
{
  "PropuestaID": 1,
  "CategoriaID": 3,
  "Descripcion": "Propuesta para mejorar la infraestructura",
  "ImgURL": "https://example.com/imagen.jpg",
  "FechaInicio": null,
  "FechaFin": "2025-12-31T23:59:59",
  "Comentarios": true,
  "TipoPropuestaID": 2,
  "OrganizacionID": 62,
  "SegmentosDirigidosJS": "[1,2,3]",
  "SegmentosImpactoJS": "[4,5]",
  "AdjuntosJS": "[{\"nombre\": \"documento1.pdf\", \"tipoDocumentoID\": 1, \"idLegal\": \"123456789\"}, {\"nombre\": \"documento2.pdf\", \"tipoDocumentoID\": 2, \"idLegal\": \"987654321\"}]",
  "UsuarioAccion": 672,
  "EquipoOrigen": "ServidorApp01"
}

SELECT para verificar usuarios:
select * from pv_propuestas

Bitácora de lo acontecido:
- Se implementó la ejecución del procedimiento almacenado `crearActualizarPropuesta` usando `sqlalchemy.text`.
- Se incluyó soporte para codificación Base64 en campos tipo `bytes` para compatibilidad con JSON.
- Se validan los campos usando Pydantic (`CrearActualizarPropuestaDTO`), retornando errores de validación detallados.
- Se controla la transacción con `await session.commit()` y se captura cualquier excepción del proceso.
- Se utiliza `get_session` para obtener una sesión `AsyncSession` con contexto seguro.
"""
