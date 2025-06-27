import json
import logging
import base64
import azure.functions as func
from shared.database import get_session
from sqlalchemy import text


def bytes_to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode('utf-8')


def json_bytes_serializer(obj):
    if isinstance(obj, bytes):
        return bytes_to_base64(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Procesando petición para repartir dividendos...")

    sp_call = text("EXEC dbo.sp_RepartirDividendos")

    try:
        async with get_session() as session:
            await session.execute(sp_call)
            await session.commit()

        return func.HttpResponse(
            json.dumps({"mensaje": "Dividendos repartidos exitosamente"}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as ex:
        logging.exception("Error al ejecutar el stored procedure")
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            mimetype="application/json",
            status_code=500
        )
"""
Función principal: main(req: func.HttpRequest) -> func.HttpResponse
Nombre: repartirDividendos

Descripción general:
    Esta función Azure se encarga de ejecutar el procedimiento almacenado dbo.sp_RepartirDividendos,
    el cual reparte las ganancias validadas de un proyecto entre sus inversionistas, según su participación.

Entrada:
    - No requiere parámetros en el body. Es una operación protegida y debe llamarse desde un entorno autorizado.

Lógica interna:
    1. Se establece una conexión asincrónica con la base de datos usando get_session().
    2. Se ejecuta el procedimiento dbo.sp_RepartirDividendos, el cual:
        - Verifica si hay proyectos con fiscalización aprobada.
        - Calcula el monto correspondiente a repartir por usuario según su inversión.
        - Registra las transacciones y la distribución en las tablas correspondientes.
        - Registra logs de operación o errores en SP_InsertarLog.
    3. No se esperan resultados devueltos directamente, pero se captura cualquier error del procedimiento.
    4. Se devuelve un mensaje de éxito o un detalle de error.

Respuesta:
    - 200 OK si el procedimiento se ejecuta sin errores.
        Ejemplo: { "mensaje": "Dividendos repartidos exitosamente" }
    - 500 Internal Server Error si ocurre alguna excepción.
        Ejemplo: { "error": "Detalle del error" }

Dependencias:
    - SQLAlchemy Async para conexión a base de datos.
    - shared.database.get_session() para obtener sesión de conexión.
    - Procedimiento SQL: dbo.sp_RepartirDividendos.

Uso recomendado:
    Este endpoint se puede invocar desde paneles administrativos o tareas programadas
    para ejecutar el reparto de dividendos en base a fiscalizaciones validadas y proyectos activos.
"""