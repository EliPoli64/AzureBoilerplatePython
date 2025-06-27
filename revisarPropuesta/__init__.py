import logging
import json
import os
import pyodbc
import azure.functions as func

# Asegúrate de que la cadena de conexión esté configurada en las variables de entorno de tu Azure Function
CONN = os.getenv("SqlConnectionString")

# SQL para llamar al Stored Procedure y obtener su valor de retorno y el parámetro de salida
# Usamos parámetros con '?' para pyodbc y declaramos variables SQL para el retorno y la salida.
SQL_CALL_SP = """
DECLARE @output_message NVARCHAR(255);
DECLARE @return_code INT;
EXEC @return_code = dbo.usp_RevisarPropuesta 
    @PropuestaID = ?, 
    @RevisorID = ?, 
    @ResultadoFinal = ?, 
    @ComentariosRevision = ?, 
    @TipoRevision = ?, 
    @MensajeSalida = @output_message OUTPUT;
SELECT @return_code AS ReturnCode, @output_message AS MensajeSalida;
"""

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger function processed a request to revise a proposal.')
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Por favor, envíe un cuerpo de solicitud JSON válido.",
            status_code=400
        )
    propuesta_id = req_body.get('propuesta_id')
    revisor_id = req_body.get('revisor_id')
    resultado_final = req_body.get('resultado_final')
    comentarios_revision = req_body.get('comentarios_revision')
    tipo_revision = req_body.get('tipo_revision')

    if not all([propuesta_id, revisor_id, resultado_final, tipo_revision]):
        return func.HttpResponse(
            "Faltan parámetros obligatorios. Se requieren: 'propuesta_id', 'revisor_id', 'resultado_final', 'tipo_revision'.",
            status_code=400
        )
    if not isinstance(propuesta_id, int) or not isinstance(revisor_id, int):
        return func.HttpResponse(
            "Los campos 'propuesta_id' y 'revisor_id' deben ser números enteros.",
            status_code=400
        )
    
    if resultado_final not in ['Aprobada', 'Rechazada']:
        return func.HttpResponse(
            "El valor para 'resultado_final' debe ser 'Aprobada' o 'Rechazada'.",
            status_code=400
        )
    
    
    try:
        logging.info(f"Connecting to DB with connection string: {CONN[:30]}...") # Log parcial por seguridad
        with pyodbc.connect(CONN) as cnn:
            with cnn.cursor() as cur:
                logging.info(f"Executing SP with PropuestaID: {propuesta_id}, RevisorID: {revisor_id}, Resultado: {resultado_final}")
                
                cur.execute(
                    SQL_CALL_SP, 
                    propuesta_id, 
                    revisor_id, 
                    resultado_final, 
                    comentarios_revision, 
                    tipo_revision
                )
                
                row = cur.fetchone()
                
                if row:
                    sp_return_code = row.ReturnCode
                    sp_mensaje_salida = row.MensajeSalida
                    logging.info(f"SP Return Code: {sp_return_code}, Message: {sp_mensaje_salida}")
                    
                    response_payload = {
                        "status": "success",
                        "message": sp_mensaje_salida,
                        "sp_return_code": sp_return_code
                    }
                    if sp_return_code != 0: # Si el SP devolvió un código de error
                        response_payload["status"] = "error"
                        status_code = 400 if sp_return_code in [1, 2, 3] else 500 # Códigos específicos del SP
                else:
                    response_payload = {
                        "status": "error",
                        "message": "El Stored Procedure no devolvió resultados inesperadamente.",
                        "sp_return_code": -1
                    }
                    status_code = 500

                return func.HttpResponse(
                    json.dumps(response_payload),
                    mimetype="application/json",
                    status_code=status_code if 'status_code' in locals() else 200
                )

    except pyodbc.Error as db_err:
        sqlstate = db_err.args[0]
        sql_error_message = db_err.args[1]
        logging.exception(f"Database error occurred: {sqlstate} - {sql_error_message}")
        return func.HttpResponse(
            json.dumps({"error": f"Error de base de datos: {sql_error_message}"}), 
            mimetype="application/json",
            status_code=500
        )
    except Exception as exc:
        logging.exception("An unexpected error occurred.")
        return func.HttpResponse(
            json.dumps({"error": f"Error interno del servidor: {str(exc)}"}),
            mimetype="application/json",
            status_code=500
        )