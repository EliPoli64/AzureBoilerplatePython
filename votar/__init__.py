import azure.functions as func
from shared.dtos import VotoDTO
from shared.database import get_session
from shared.models import Voto, Usuario, Log, LlaveUsuario, Documento, Pregunta, Respuesta, Votacion, VotacionPregunta, RespuestaParticipante
from sqlalchemy import select, desc, text
from sqlalchemy.orm import selectinload, Session, relationship, contains_eager
from pydantic import ValidationError
import json
import logging
from datetime import datetime, timezone
import base64
import hashlib 
from typing import Optional, List
import uuid 

def validarVotoUsuario(registro_respuesta_participante: dict, json_votacion_completa: dict) -> bool:

    try:
        participante_pregunta_id = registro_respuesta_participante.get("pregunta_id")
        participante_votacion_id = registro_respuesta_participante.get("votacionID")

        if participante_pregunta_id is None or participante_votacion_id is None:
            print("Advertencia: El JSON del participante debe contener 'pregunta_id' y 'votacionID'.")
            return False
        
        votacion_id_completa = json_votacion_completa.get("votacionID")
        preguntas_de_votacion = json_votacion_completa.get("preguntas", []) 

        if votacion_id_completa is None:
            print("Advertencia: El JSON completo de la votación debe contener 'votacionID'.")
            return False
        if participante_votacion_id != votacion_id_completa:
            print(f"Mismatch: La votacionID del participante ({participante_votacion_id}) no coincide con la votacionID de la votación completa ({votacion_id_completa}).")
            return False
        pregunta_encontrada_en_votacion = False
        for pregunta_en_votacion in preguntas_de_votacion:
            if pregunta_en_votacion.get("preguntaID") == participante_pregunta_id:
                pregunta_encontrada_en_votacion = True
                break
        
        if not pregunta_encontrada_en_votacion:
            print(f"Mismatch: La pregunta_id del participante ({participante_pregunta_id}) no se encontró en la lista de preguntas de la votación con ID {votacion_id_completa}.")
            return False
        return True

    except Exception as e:
        print(f"Ocurrió un error inesperado durante la validación: {e}")
        return False


def validarFechas(json_votacion: dict) -> bool:

    try:
        fecha_inicio_str = json_votacion.get("fechaInicio")
        fecha_fin_str = json_votacion.get("fechaFin")

        if not fecha_inicio_str or not fecha_fin_str:
            print("Error: El JSON de la votación debe contener 'fechaInicio' y 'fechaFin'.")
            return False

        fecha_inicio_dt = datetime.fromisoformat(fecha_inicio_str).replace(tzinfo=timezone.utc)
        fecha_fin_dt = datetime.fromisoformat(fecha_fin_str).replace(tzinfo=timezone.utc)
        
        fecha_actual_utc = datetime.now(timezone.utc)

        if fecha_inicio_dt <= fecha_actual_utc <= fecha_fin_dt:
            return True
        else:
            return False

    except ValueError as e:
        print(f"Error al parsear las fechas del JSON. Asegúrate de que estén en formato ISO 8601 (YYYY-MM-DDTHH:MM:SS): {e}")
        return False
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la validación: {e}")
        return False
    


async def getVotacionPorPreguntaID(session, pregunta_id: int) -> Optional[dict]:
    query = (
        select(Votacion)
        .join(Votacion.preguntas) 
        .join(VotacionPregunta.pregunta)  
        .outerjoin(Pregunta.respuestas)  
        .where(Pregunta.preguntaID == pregunta_id) 
        .options(
            contains_eager(Votacion.preguntas).contains_eager(VotacionPregunta.pregunta).contains_eager(Pregunta.respuestas)
        )
    )

    result = await session.execute(query)
    votacion_instance = result.scalars().first()

    if not votacion_instance:
        return None 
    votacion_data = {
        "votacionID": votacion_instance.votacionId,
        "titulo": votacion_instance.titulo,
        "descripcion": votacion_instance.descripcion,
        "fechaInicio": votacion_instance.fechaInicio.isoformat(),
        "fechaFin": votacion_instance.fechaFin.isoformat(),
        "estadoVotacionId": votacion_instance.estadoVotacionId,
        "privada": votacion_instance.privada,
        "esSecreta": votacion_instance.esSecreta,
        "preguntas": []
    }
    preguntas_set = set()

    for vp_assoc in votacion_instance.preguntas:
        pregunta = vp_assoc.pregunta
        if pregunta.preguntaID not in preguntas_set:
            preguntas_set.add(pregunta.preguntaID)
            pregunta_data = {
                "preguntaID": pregunta.preguntaID,
                "enunciado": pregunta.enunciado,
                "tipoPreguntaID": pregunta.tipoPreguntaID,
                "maxSelecciones": pregunta.maxSelecciones,
                "fechaPublicacion": pregunta.fechaPublicacion.isoformat(),
                "respuestas": []
            }
            
            # Iterar sobre las respuestas de la pregunta
            for respuesta in pregunta.respuestas: # 'respuestas' cargadas por eager load
                pregunta_data["respuestas"].append({
                    "respuestaID": respuesta.respuestaID,
                    "respuesta": respuesta.respuesta,
                    "value": respuesta.value
                })
            
            votacion_data["preguntas"].append(pregunta_data)
            
    return votacion_data

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
        raise ValueError("Error al verificar credenciales")

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

async def obtenerRespuestasParticipantes(session, llaveCifrada, usuario) -> List[dict]:
    try:
        query = (
            select(
                RespuestaParticipante.respuestaParticipanteID,
                RespuestaParticipante.preguntaID,
                RespuestaParticipante.ncRespuesta,
                Votacion.votacionId
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
                "nc_respuesta": row.ncRespuesta, 
                "votacionID": row.votacionId
            }
            if await verificarRespuesta(session, respuesta['nc_respuesta'], llaveCifrada, usuario):
                respuestas.append(respuesta)

        return respuestas
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
    

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        dto = VotoDTO(**req.get_json())
    except ValidationError as e:
        return func.HttpResponse(e.json(), status_code=400)

    try:
        async with get_session() as session:
            usuario = await obtenerUsuario(session, dto.cedulaUsuario)
            if not usuario:  #VALIDAMOS QUE EL USUARIO EXISTA EN EL SISTEMA  
                await insertarLog(
                    session=session,
                    descripcion="Usuario no encontrado",
                    computador="votar/endpoint",
                    usuario=dto.cedulaUsuario,
                    tipologid=1,
                    origenlogid=2,
                    logseveridadid=2
                )
                return func.HttpResponse(
                    json.dumps({"error": "Credenciales inválidas"}),
                    status_code=401,
                    mimetype="application/json"
                )
            
            llaveActiva = await obtenerLlave(session, usuario.userid)
            try:
                resultado = await session.execute(
                    text("""
                        SELECT DECRYPTBYPASSPHRASE(:pass, :llave) AS llave_desencriptada
                        WHERE :llave IS NOT NULL
                    """),
                    {
                        "pass": dto.contrasenia.get_secret_value(),
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
            documento = Documento(
                nombre=f"{usuario.userid}-PruebaVida",
                fechaCreacion=datetime.now(),
                tipoDocumentoID=10,
                estadoDocumentoID=4,
                ultimaModificacion=datetime.now(),
                esActual=True,
                idLegal=f"{usuario.userid}_PV",
                checksum=generarChecksum(dto.prueba_vida),
            )
            session.add(documento)
            await session.commit()

            votacionJSON = await getVotacionPorPreguntaID(session, dto.preguntaID)
            if not validarFechas(votacionJSON): 
                return func.HttpResponse(
                    json.dumps({
                        "error": "Votación invalida, la fecha ya pasó, o la fecha de inicio no ha llegado.",
                        "codigo": "404"
                    }),
                    status_code=500,
                    mimetype="application/json"
                )
            
            if not validarVotoUsuario(obtenerRespuestasParticipantes(session, llave_desencriptada, usuario), votacionJSON):
                return func.HttpResponse(
                    json.dumps({
                        "error": "Este usuario ya votó para esta pregunta.",
                        "codigo": "506"
                    }),
                    status_code=500,
                    mimetype="application/json"
                )
            
            result = await session.execute( 
                 text("""
                        SELECT ENCRYPTBYPASSPHRASE(:pass, :llave) AS llave_desencriptada
                        WHERE :llave IS NOT NULL
                    """),
                    {
                        "pass": llave_desencriptada,
                        "llave": str(usuario.userid)
                    }
                )
            #async with session.begin():
            voto = Voto(
                    preguntaID = dto.preguntaID,
                    respuestaID = dto.respuestaID,
                    checksum = hashlib.sha256("RespuestaParticipante".encode('utf-8')).digest(),
                    valor = dto.valor,
                    fechaRespuesta = datetime.now(),
                    ncRespuesta = result.scalar_one(),
                    tokenGUID = str(uuid.uuid4()),
                    pesoRespuesta = dto.pesoRespuesta
                )
            session.add(voto)
            await session.commit()
        return func.HttpResponse(json.dumps({"msg": "Voto registrado"}),
                              mimetype="application/json")
    
    

    except Exception as ex:
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            mimetype="application/json",
            status_code=500,
        )
    
    
    """
    Ejemplo de uso:
    {
    "preguntaID": 1,        
    "respuestaID": 1,       
    "valor": "Mejorar el transporte público",           
    "pesoRespuesta": 2, 
    "cedulaUsuario": "100000000",
    "contrasenia": "JUGAHE0000",
    "prueba_vida" : "Prueba de Vida"
    }
    """

    """
Documentación de Función de Azure: `votar` (anteriormente `listarVotos`)

Esta documentación describe la funcionalidad de la función `main` (nombre HTTP: `listarVotos`), que está diseñada para permitir a un usuario autenticado registrar su voto en una pregunta de una votación.

### 1. Descripción General

La función `listarVotos` (que en realidad implementa la lógica para **registrar un voto**) es un endpoint de API de Azure Functions que permite a un usuario autenticarse con sus credenciales (cédula y contraseña), verificar una prueba de vida, y luego registrar su respuesta a una pregunta específica de una votación activa. La función realiza una serie de validaciones de seguridad y de lógica de negocio antes de persistir el voto en la base de datos.

**Inconsistencia en el Nombre:**
Aunque la función se nombra `listarVotos`, su implementación actual está claramente orientada a **registrar un voto** (`INSERT` en `pv_respuestaParticipante`). Si la intención es listar los votos, la lógica de base de datos y la estructura de respuesta deberían modificarse.

### 2. Parámetros de Entrada (JSON en el `body` de la solicitud POST)

La función espera un JSON en el cuerpo de la solicitud HTTP POST, que debe coincidir con la estructura del DTO `VotoDTO`.

| Parámetro       | Tipo        | Descripción                                                          | Ejemplo             |
| :-------------- | :---------- | :------------------------------------------------------------------- | :------------------ |
| `cedulaUsuario` | `str`       | Cédula de identidad del usuario que intenta votar.                   | `"100000000"`       |
| `contrasenia`   | `SecretStr` | Contraseña del usuario (manejada de forma segura por Pydantic).      | `"JUGAHE0000"`      |
| `prueba_vida`   | `str`       | Un identificador o referencia para la prueba de vida (ej. `UUID` de un archivo). | `"video_123.mp3"`   |
| `preguntaID`    | `int`       | ID de la pregunta a la que el usuario está votando.                  | `1`                 |
| `respuestaID`   | `int`       | ID de la respuesta seleccionada por el usuario para la `preguntaID`.| `1`                 |
| `valor`         | `str`       | El texto o valor asociado a la `respuestaID` seleccionada.           | `"Mejorar el transporte público"` |
| `pesoRespuesta` | `int`       | Un valor numérico que representa el "peso" o la ponderación de la respuesta. | `2`                 |

### 3. Lógica Interna y Flujo de Procesamiento

1.  **Validación de Entrada (Pydantic):**
    * El cuerpo de la solicitud JSON se valida contra el `VotoDTO`. Si falla, se retorna un `400 Bad Request`.

2.  **Autenticación de Usuario:**
    * Se busca al `Usuario` por `cedulaUsuario` en la tabla `pv_usuarios` (`obtenerUsuario`).
    * Si el usuario no existe, se registra un log y se devuelve un `401 Unauthorized`.
    * Se obtiene la llave criptográfica `llaveActiva` del usuario desde `pv_llaveUsuario` (`obtenerLlave`).
    * Se intenta **desencriptar** `llaveActiva.llaveCifrada` usando `dto.contrasenia` como frase de paso (`DECRYPTBYPASSPHRASE`).
    * Si la desencriptación falla (retorna `None`), se registra un log de fallo de autenticación y se devuelve `401 Unauthorized`.
    * La `llave_desencriptada` resultante (que debería ser el `usuario.userid` original) se decodifica de `bytes` a `utf-8`.

3.  **Registro de Prueba de Vida:**
    * Se crea un registro en `pv_documento` (con `tipoDocumentoID=10`) para la prueba de vida del usuario, incluyendo un `checksum` SHA-256 de `dto.prueba_vida`.

4.  **Validación de Votación y Pregunta:**
    * Se obtiene la información completa de la votación (`votacionJSON`) asociada a la `dto.preguntaID` (`getVotacionPorPreguntaID`).
    * Se valida que la votación esté activa según sus fechas de inicio y fin (`validarFechas`). Si no lo está, se retorna un `500 Internal Server Error` (este código de estado podría ser más apropiado como `400 Bad Request` o `403 Forbidden`).
    * **CRÍTICO: Verificación de voto duplicado (lógica con error):**
        * Se llama a `obtenerRespuestasParticipantes(session, llave_desencriptada, usuario)` que devuelve una `List[dict]` de respuestas ya verificadas del usuario.
        * Esta lista se pasa como el primer argumento a `validarVotoUsuario`. **Esto causará un `TypeError`** porque `validarVotoUsuario` espera un solo `dict` (una única `respuesta_participante`) y no una lista.
        * **Para corregir esto, la lógica de `validarVotoUsuario` debe iterar sobre la lista de respuestas obtenidas para verificar si alguna de ellas coincide con la votación y pregunta actual, o `obtenerRespuestasParticipantes` debería filtrar por la pregunta/votación específica que se intenta registrar.** Si la intención es verificar que el usuario **no haya votado antes en esta pregunta**, la lógica debe ser revisada para:
            1.  Consultar `pv_respuestaParticipante` para ver si ya existe un registro para `usuario.userid` y `dto.preguntaID`.
            2.  Si existe, retornar el error apropiado.
        * Actualmente, si la llamada a `validarVotoUsuario` (una vez corregido el `TypeError`) determina que la respuesta es "inválida" según su lógica interna, se devuelve un `500 Internal Server Error` con el mensaje "Este usuario ya votó para esta pregunta." (el código de estado `500` debería ser `409 Conflict` o `403 Forbidden`).

5.  **Registro del Voto:**
    * Se ejecuta una consulta SQL para **cifrar** el `usuario.userid` (convertido a `str`) usando `llave_desencriptada` (la contraseña del usuario) como frase de paso (`ENCRYPTBYPASSPHRASE`). El resultado es binario.
    * **Corrección aplicada:** La línea `ncRespuesta = result.scalar_one()` ahora extrae correctamente el valor binario del `CursorResult`.
    * **Consideración de Tipo de Columna `ncRespuesta`:** Si la columna `ncRespuesta` en la tabla `pv_respuestaParticipante` es de tipo `INT`, esta asignación de un valor binario (`VARBINARY` desde SQL Server) resultará en un error de conversión de tipo en la base de datos. Para que esto funcione, `ncRespuesta` debe ser una columna de tipo `VARBINARY` en la base de datos (lo cual es lo usual para datos cifrados).
    * Se crea una nueva instancia de `Voto` (que mapea a `pv_respuestaParticipante`) con los datos proporcionados y el `ncRespuesta` cifrado.
    * Se añade el `voto` a la sesión y se realiza un `await session.commit()`.

6.  **Respuesta Final:**
    * Si todo es exitoso, se devuelve un `200 OK` con un mensaje de "Voto registrado".

### 4. Estructura de Respuesta Exitosa (HTTP 200 OK)

En caso de éxito, la función devuelve un JSON con el siguiente formato:

```json
{
    "msg": "Voto registrado"
}
"""