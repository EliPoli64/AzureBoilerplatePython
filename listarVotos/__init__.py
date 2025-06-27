from datetime import datetime
from typing import List
from pydantic import BaseModel, SecretStr
from pydantic import ValidationError
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, text
from sqlalchemy.orm import selectinload, joinedload
from shared.database import get_session
from shared.dtos import ListaVotosInputDTO
import json
import logging
import hashlib
import azure.functions as func
from shared.models import (
    Usuario, 
    LlaveUsuario,
    PropuestaVotacion,
    Propuesta,
    Votacion,
    UsuarioVotacionPublica,
    Respuesta,
    RespuestaParticipante,
    Pregunta,
    VotacionPregunta,
    Log,
    Documento
)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Iniciando procesamiento de listaVotos")
    ahora = datetime.now()
    try:
        auth_data = ListaVotosInputDTO(**req.get_json())
        logging.info(f"Solicitud recibida para cédula: {auth_data.cedula[:3]}******")
        async with get_session() as session:
            usuario = await obtenerUsuario(session, auth_data.cedula) 
            if not usuario:
                await insertarLog(
                    session=session,
                    descripcion="Usuario no encontrado en autenticación",
                    computador="listarVotos/endpoint",
                    usuario=auth_data.cedula,
                    tipologid=1,
                    origenlogid=2,
                    logseveridadid=2
                )
                logging.warning(f"Usuario no encontrado: {auth_data.cedula[:3]}******")
                return func.HttpResponse(
                    json.dumps({"error": "Credenciales inválidas"}),
                    status_code=401,
                    mimetype="application/json"
                )
                logging.info(f"Usuario encontrado: ID {usuario.userid}")
            logging.info(f"Usuario encontrado: ID {usuario.userid}")
            llaveActiva = await obtenerLlave(session, usuario.userid)
            documento = Documento(
                    nombre=f"{usuario.userid}-PruebaVida",
                    fechaCreacion=ahora,
                    tipoDocumentoID=10,
                    estadoDocumentoID=4,
                    ultimaModificacion=ahora,
                    esActual=True,
                    idLegal=f"{usuario.userid}_PV",
                    checksum=generarChecksum(auth_data.prueba_vida),
                )
            session.add(documento)
            await session.commit()
            await insertarLog(
                    session=session,
                    descripcion="Insercion Prueba de Vida",
                    computador="listarVotos/endpoint",
                    usuario=str(usuario.userid),
                    tipologid=1,
                    origenlogid=2,
                    logseveridadid=2
                )
            try:
                resultado = await session.execute(
                    text("""
                        SELECT DECRYPTBYPASSPHRASE(:pass, :llave) AS llave_desencriptada
                        WHERE :llave IS NOT NULL
                    """),
                    {
                        "pass": auth_data.contrasenna.get_secret_value(),
                        "llave": llaveActiva.llaveCifrada
                    }
                )
                llave_desencriptada = resultado.scalar_one_or_none()
                if llave_desencriptada is None:
                    await insertarLog(
                        session=session,
                        descripcion="Fallo de descifrado de llave",
                        computador="listarVotos/endpoint",
                        usuario=str(usuario.userid),
                        refId1=usuario.userid,
                        tipologid=2,
                        origenlogid=2,
                        logseveridadid=3
                    )
                    logging.warning(f"Fallo de descifrado para usuario ID: {usuario.userid}")
                    return func.HttpResponse(
                        json.dumps({
                            "error": "Credenciales inválidas",
                            "codigo": "AUTH_FAILED"
                        }),
                        status_code=401,
                        mimetype="application/json"
                    )
                llave_desencriptada = llave_desencriptada.decode('utf-8')
                logging.info(f"Autenticación exitosa para usuario ID: {usuario.userid}")
            except Exception as e:
                await insertarLog(
                    session=session,
                    descripcion="Error técnico en verificación de contraseña",
                    computador="listarVotos/endpoint",
                    usuario=str(usuario.userid),
                    refId1=usuario.userid,
                    trace=str(e),
                    tipologid=2,
                    origenlogid=2,
                    logseveridadid=5
                )
                logging.error(f"Error técnico al verificar contraseña: {str(e)}", exc_info=True)
                return func.HttpResponse(
                    json.dumps({
                        "error": "Error interno en verificación",
                        "codigo": "INTERNAL_ERROR"
                    }),
                    status_code=500,
                    mimetype="application/json"
                )        
            respuestas = await obtenerRespuestasParticipantes(session, llave_desencriptada, usuario.userid)
            response_data = {
                "user_id": usuario.userid,
                "nombre" : usuario.nombre,
                "primerApellido": usuario.primerApellido,
                "segundoApellido": usuario.segundoApellido,
                "respuestas": respuestas
            }
            await insertarLog(
                session=session,
                descripcion="Respuestas obtenidas exitosamente",
                computador="listarVotos/endpoint",
                usuario=str(usuario.userid),
                refId1=usuario.userid,
                tipologid=3,
                origenlogid=2,
                logseveridadid=1,
            )
            return func.HttpResponse(
                json.dumps(response_data, default=str),
                status_code=200,
                mimetype="application/json"
            )
    except ValidationError as e:
        logging.error(f"Error de validación: {str(e)}")
        return func.HttpResponse(
            e.json(),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Error interno del servidor"}),
            status_code=500,
            mimetype="application/json"
        )

async def obtenerUsuario(session, cedula) -> Usuario | None:
    try:
        result = await session.execute(
            select(Usuario)
            .where(Usuario.identificacion == cedula)
            .options(selectinload(Usuario.llaves))
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logging.error(f"Error en consulta de usuario: {str(e)}", exc_info=True)
        raise ValueError("Error al consultar usuario en la base de datos")

async def obtenerRespuestasParticipantes(session, llaveCifrada, usuario) -> List[dict]:
    try:
        query = (
            select(
                RespuestaParticipante.respuestaParticipanteID,
                RespuestaParticipante.preguntaID,
                RespuestaParticipante.respuestaID,
                RespuestaParticipante.valor,
                RespuestaParticipante.fechaRespuesta,
                RespuestaParticipante.ncRespuesta,
                RespuestaParticipante.tokenGUID,
                RespuestaParticipante.pesoRespuesta,
                Pregunta.enunciado,
                Respuesta.respuesta,
                Respuesta.value,
                Votacion.titulo.label("titulo_votacion")
            )
            .select_from(RespuestaParticipante)
            .join(Pregunta, RespuestaParticipante.preguntaID == Pregunta.preguntaID)
            .join(Respuesta, RespuestaParticipante.respuestaID == Respuesta.respuestaID)
            .join(VotacionPregunta, VotacionPregunta.preguntaID == Pregunta.preguntaID)
            .join(Votacion, Votacion.votacionId == VotacionPregunta.votacionID)
        )
        result = await session.execute(query)
        respuestas = []
        for row in result:
            respuesta = {
                "respuesta_participante_id": row.respuestaParticipanteID,
                "pregunta_id": row.preguntaID,
                "respuesta_id": row.respuestaID,
                "fecha_respuesta": row.fechaRespuesta,
                "nc_respuesta": row.ncRespuesta, 
                "titulo_votacion": row.titulo_votacion,
                "enunciado_pregunta": row.enunciado,
                "texto_respuesta": row.respuesta
            }
            if await verificarRespuesta(session, respuesta['nc_respuesta'], llaveCifrada, usuario):
                respuestas.append(respuesta)
        respuestas_recientes = sorted(
            respuestas,
            key=lambda x: x['fecha_respuesta'],
            reverse=True
        )[:5]
        for respuesta in respuestas_recientes:
            respuesta['fecha_respuesta'] = respuesta['fecha_respuesta'].isoformat()
            del respuesta['nc_respuesta']
        return respuestas_recientes
    except Exception as e:
        logging.error(f"Error al consultar respuestas de participantes: {str(e)}", exc_info=True)
        raise ValueError("Error al obtener respuestas de participantes")

async def verificarRespuesta(session, ncRespuesta, llaveCifrada, usuario) -> bool:
    try:
        if not ncRespuesta:
            return False
        result = await session.execute(
            text("""
                SELECT DECRYPTBYPASSPHRASE(:llaveCifrada, :nc_respuesta) AS nc_desencriptado
            """),
            {
                "llaveCifrada": llaveCifrada,
                "nc_respuesta": ncRespuesta
            }
        )
        nc_desencriptado = result.scalar_one_or_none()
        if nc_desencriptado != None:
            logging.info(nc_desencriptado)
            logging.info(usuario)
            return nc_desencriptado.decode('utf-8') == str(usuario)
        return False
    except Exception as e:
        logging.error(f"Error desencriptando ncRespuesta: {str(e)}")
        return False

async def obtenerLlave(session, usuario_id: int) -> LlaveUsuario:
    try:
        result = await session.execute(
            select(LlaveUsuario)
            .where(
                LlaveUsuario.usuarioID == usuario_id,
                LlaveUsuario.esActiva == True 
            )
            .order_by(desc(LlaveUsuario.ultimaModificacion))
        )
        
        llave = result.scalar_one_or_none()
        if not llave:
            logging.warning(f"No hay llave activa para usuario ID: {usuario_id}")
            raise ValueError("No se encontró llave criptográfica activa")
        logging.info(f"Llave encontrada para usuario ID: {usuario_id}")
        return llave
    except Exception as e:
        logging.error(f"Error al consultar llave: {str(e)}", exc_info=True)
        raise ValueError("Error al verificar credenciales")


def generarChecksum(valor: str) -> bytes:
    return hashlib.sha256(valor.encode()).digest()

async def insertarLog(
    session: Session,
    descripcion: str,
    computador: str,
    usuario: str,
    trace: str = "API/ENDPOINT/listarVotos",  
    refId1: int = None,
    refId2: int = None,
    valor1: str = None,
    valor2: str = None,
    checksum: str = "2025API/20END25OINT06/listarVotos26",  
    tipologid: int = 1,     
    origenlogid: int = 1,   
    logseveridadid: int = 1 ):
    log_entry = Log(
        descripcion=descripcion,
        timestamp=datetime.utcnow(),
        computador=computador,
        usuario=usuario,
        trace=trace,
        refId1=refId1,
        refId2=refId2,
        valor1=valor1,
        valor2=valor2,
        checksum=generarChecksum(checksum),
        tipologid=tipologid,
        origenlogid=origenlogid,
        logseveridadid=logseveridadid
    )
    session.add(log_entry)
    await session.commit()


"""
Función principal: main(req: func.HttpRequest) -> func.HttpResponse
Nombre: listarVotos

Parámetros de entrada (JSON en el body):
    - cedula (str): Cédula de identidad del usuario
    - contrasenna (SecretStr): Contraseña del usuario
    - prueba_vida (str): Texto de prueba de vida para verificación

Lógica interna:
    1. Autenticación:
       - Valida credenciales usando ListaVotosInputDTO
       - Verifica usuario en pv_usuarios
       - Obtiene llave criptográfica activa del usuario
       - Registra prueba de vida en pv_documento (tipoDocumentoID=10)
    
    2. Verificación:
       - Desencripta llave usando DECRYPTBYPASSPHRASE
       - Valida coincidencia de credenciales
    
    3. Consulta:
       - Obtiene respuestas de votaciones públicas del usuario
       - Filtra las 5 más recientes por fecha
       - Verifica pertenencia mediante desencriptación de ncRespuesta
    
    4. Respuesta:
       - Devuelve datos básicos del usuario
       - Lista de respuestas válidas (sin campo nc_respuesta)
       - Registra logs en cada etapa crítica

Flujo de respuesta:
    - 200 OK: Datos de usuario y respuestas válidas
    - 401 Unauthorized: Credenciales inválidas
    - 400 Bad Request: Error en validación de datos
    - 500 Internal Server Error: Error inesperado

Estructura de respuesta exitosa (200):
{
    "user_id": int,
    "nombre": str,
    "primerApellido": str,
    "segundoApellido": str,
    "respuestas": [
        {
            "respuesta_participante_id": int,
            "pregunta_id": int,
            "respuesta_id": int,
            "fecha_respuesta": str (ISO format),
            "titulo_votacion": str,
            "enunciado_pregunta": str,
            "texto_respuesta": str
        },
        (máximo 5)
    ]
}

Ejemplo de uso:
POST /api/listarVotos
{
    "cedula": "100000000",
    "contrasenna": "JUGAHE0000",
    "prueba_vida": "video_123.mp3"
}

Tablas relacionadas:
    - pv_usuarios
    - pv_llaveUsuario
    - pv_respuestaParticipante
    - pv_preguntas
    - pv_respuestas
    - pv_votacionPregunta
    - pv_votacion
    - pv_documento
    - pv_logs

Seguridad:
    - Todos los accesos quedan registrados en logs
    - Las contraseñas se manejan como SecretStr
    - Los datos sensibles (ncRespuesta) no se exponen
    - Se verifica pertenencia de cada respuesta
    - Se genera checksum SHA-256 para prueba de vida

Consideraciones:
    - Requiere llave criptográfica activa
    - Las fechas se devuelven en formato ISO 8601
    - Máximo 5 respuestas recientes
"""