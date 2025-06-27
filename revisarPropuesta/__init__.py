# revisarPropuesta/__init__.py
import logging
import json
import azure.functions as func
from shared.dtos import RevisarPropuestaDTO # Importa el nuevo DTO
from shared.database import get_session
from sqlalchemy import text
from pydantic import ValidationError
from typing import Optional # Puede que no sea necesario si ya está en DTO

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger function processed a request to revise a proposal using SQLAlchemy.')

    try:
        dto = RevisarPropuestaDTO(**req.get_json())
    except ValidationError as e:
        logging.error(f"Error de validación del DTO: {str(e)}")
        return func.HttpResponse(
            e.json(),
            status_code=400,
            mimetype="application/json"
        )
    except ValueError: # Captura si el JSON no es válido
        return func.HttpResponse(
            "Por favor, envíe un cuerpo de solicitud JSON válido.",
            status_code=400,
            mimetype="application/json"
        )
    sp_call = text("""
        DECLARE @output_message NVARCHAR(255);
        DECLARE @return_code INT;
        EXEC @return_code = dbo.usp_RevisarPropuesta
            @PropuestaID = :propuesta_id,
            @RevisorID = :revisor_id,
            @ResultadoFinal = :resultado_final,
            @ComentariosRevision = :comentarios_revision,
            @TipoRevision = :tipo_revision,
            @MensajeSalida = @output_message OUTPUT;
        SELECT @return_code AS ReturnCode, @output_message AS MensajeSalida;
    """)

    try:
        async with get_session() as session:
            params = dto.dict()

            logging.info(f"Executing SP usp_RevisarPropuesta with params: {params}")
            result = await session.execute(sp_call, params)
            await session.commit() 
            rows = result.fetchall()

            if not rows:
                return func.HttpResponse(
                    json.dumps({"error": "No se recibieron resultados esperados del stored procedure usp_RevisarPropuesta"}),
                    mimetype="application/json",
                    status_code=500
                )
            sp_result = dict(rows[0]._mapping) 

            sp_return_code = sp_result.get('ReturnCode')
            sp_mensaje_salida = sp_result.get('MensajeSalida')

            logging.info(f"SP Return Code: {sp_return_code}, Message: {sp_mensaje_salida}")

            response_payload = {
                "status": "success",
                "message": sp_mensaje_salida,
                "sp_return_code": sp_return_code
            }
            status_code = 200

            if sp_return_code != 0: 
                response_payload["status"] = "error"
                status_code = 400 
            
            return func.HttpResponse(
                json.dumps(response_payload),
                mimetype="application/json",
                status_code=status_code
            )

    except Exception as ex:
        logging.exception("Error al ejecutar el stored procedure usp_RevisarPropuesta.")
        return func.HttpResponse(
            json.dumps({"error": f"Error interno del servidor al procesar la revisión: {str(ex)}"}),
            mimetype="application/json",
            status_code=500
        )
    

    """
    Ejemplo de uso:
    {
    "propuesta_id": 2,         
    "revisor_id": 2,           
    "resultado_final": "Rechazada", 
    "comentarios_revision": "Contenido duplicado detectado por el análisis de IA.",
    "tipo_revision": "Combinada"
    }
    {
    "propuesta_id": 1,         
    "revisor_id": 1,           
    "resultado_final": "Aprobada", 
    "comentarios_revision": "Contenido duplicado detectado por el análisis de IA.",
    "tipo_revision": "Combinada"
    }
    """