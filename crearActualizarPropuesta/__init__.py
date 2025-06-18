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
            result = await session.execute(sp_call, dto.dict())
            rows = result.fetchall()
            

            resultList = []
            for row in rows:
                rowDict = dict(row._mapping)
                # Convierte checksum si existe y es bytes
                if 'checksum' in rowDict and isinstance(rowDict['checksum'], bytes):
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
ejemplo de uso:
{
  "PropuestaID": null,
  "CategoriaID": 3,
  "Descripcion": "Propuesta para mejorar la infraestructura tecnológica",
  "ImgURL": "https://example.com/imagen.jpg",
  "FechaInicio": null,
  "FechaFin": "2025-12-31T23:59:59",
  "Comentarios": true,
  "TipoPropuestaID": 2,
  "OrganizacionID": 162,
  "SegmentosDirigidosJS": "[1,2,3]",
  "SegmentosImpactoJS": "[4,5]",
  "AdjuntosJS": "[{\"nombre\": \"documento1.pdf\", \"tipoDocumentoID\": 1, \"idLegal\": \"123456789\"}, {\"nombre\": \"documento2.pdf\", \"tipoDocumentoID\": 2, \"idLegal\": \"987654321\"}]",
  "UsuarioAccion": 10,
  "EquipoOrigen": "ServidorApp01"
}

"""