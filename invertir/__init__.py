import json
import logging
import base64
import azure.functions as func
from shared.dtos import InversionDTO
from shared.database import get_session
from sqlalchemy import text
from pydantic import ValidationError
from typing import Optional

def bytes_to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode('utf-8')

def json_bytes_serializer(obj):
    if isinstance(obj, bytes):
        return bytes_to_base64(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        dto = InversionDTO(**req.get_json())
    except ValidationError as e:
        logging.error(f"Error de validación: {str(e)}")
        return func.HttpResponse(
            e.json(),
            status_code=400,
            mimetype="application/json"
        )
    sp_call = text("""
        EXEC dbo.invertir
            @proyecto = :proyecto,
            @monto = :monto,
            @moneda = :moneda,
            @cedula = :cedula,
            @contrasenna = :contrasenna,
            @organizacion = :organizacion,
            @metodoPago = :metodoPago
    """)

    try:
        async with get_session() as session:
            params = dto.dict()
            if params['organizacion'] is None:
                params['organizacion'] = None  
            result = await session.execute(sp_call, params)
            await session.commit()
            rows = result.fetchall()

            if not rows:
                return func.HttpResponse(
                    json.dumps({"error": "No se recibieron resultados del stored procedure"}),
                    mimetype="application/json",
                    status_code=500
                )
            
            result_list = []
            for row in rows:
                row_dict = dict(row._mapping)
                for key in row_dict:
                    if isinstance(row_dict[key], bytes):
                        row_dict[key] = bytes_to_base64(row_dict[key])
                result_list.append(row_dict)

            sp_result = result_list[0]
            
            if sp_result.get('Resultado') == 0:
                return func.HttpResponse(
                    json.dumps({
                        "mensaje": sp_result.get('Mensaje'),
                        "transaccion_id": sp_result.get('TransaccionID'),
                        "referencia": sp_result.get('Referencia'),
                        "monto_invertido": float(sp_result.get('MontoInvertido')) if sp_result.get('MontoInvertido') else None,
                        "numero_autorizacion": sp_result.get('NumeroAutorizacion')
                    }, default=json_bytes_serializer),
                    mimetype="application/json",
                    status_code=201
                )
            else:
                return func.HttpResponse(
                    json.dumps({"error": sp_result.get('Mensaje')}),
                    mimetype="application/json",
                    status_code=400
                )

    except Exception as ex:
        logging.error(f"Error al ejecutar el stored procedure: {str(ex)}")
        return func.HttpResponse(
            json.dumps({"error": "Error interno al procesar la inversión"}),
            mimetype="application/json",
            status_code=500
        )