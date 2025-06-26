from sqlalchemy import (
    VARBINARY,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    DateTime,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Votacion(Base):
    __tablename__ = "pv_votacion"

    votacionId = Column(Integer, primary_key=True, autoincrement=True)
    tipoVotacionId = Column(Integer, nullable=False)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(String, nullable=True)  # nvarchar(max)
    fechaInicio = Column(DateTime, nullable=False)
    fechaFin = Column(DateTime, nullable=False)
    estadoVotacionId = Column(Integer, nullable=False)
    ultimaModificacion = Column(DateTime, nullable=False)
    encuestaId = Column(Integer, nullable=False)
    privada = Column(Boolean, nullable=False)
    esSecreta = Column(Boolean, nullable=False)

class Voto(Base):
    __tablename__ = "pv_respuestaParticipante"

    respuestaParticipanteID = Column(Integer, primary_key=True, autoincrement=True)
    preguntaID = Column(Integer, nullable=False)
    respuestaID = Column(Integer, nullable=False)
    checksum = Column(LargeBinary(500), nullable=False)
    valor = Column(String(500), nullable=False)
    fechaRespuesta = Column(DateTime, nullable=True)
    ncRespuesta = Column(LargeBinary(256), nullable=False)
    tokenGUID =  Column(String(36), nullable=False, unique=True) #Manera de emular el Unique Identifier
    pesoRespuesta = Column(Integer, nullable=False)
    
class Inversion(Base):
    __tablename__ = "pv_inversion"

    inversionId = Column(Integer, primary_key=True, autoincrement=True)
    proyectoId = Column(Integer, nullable=False)
    usuarioId = Column(Integer, nullable=False)
    transaccionId = Column(Integer, nullable=False)
    organizacionId = Column(Integer, nullable=True)

class Propuesta(Base):
    __tablename__ = 'pv_propuestas'
    propuestaid = Column(Integer, primary_key=True)
    comentarios = Column(Boolean)

class DetalleComentarios(Base):
    __tablename__ = 'pv_detalleComentarios'
    detalleComentarioId = Column(Integer, primary_key=True)
    titulo = Column(String)
    cuerpo = Column(String)
    fechaPublicacion = Column(DateTime)
    usuarioId = Column(Integer)
    organizacionId = Column(Integer)

class ComentarioPropuesta(Base):
    __tablename__ = 'pv_comentariosPropuesta'
    comentarioid = Column(Integer, primary_key=True)
    detalleComentarioId = Column(Integer)
    estadoComentId = Column(Integer)
    propuestaId = Column(Integer)

class EstadoComentario(Base):
    __tablename__ = 'pv_estadoComentarios'
    estadoComentId = Column(Integer, primary_key=True)
    nombre = Column(String)

class Documento(Base):
    __tablename__ = 'pv_documento'
    documentoID = Column(Integer, primary_key=True)
    nombre = Column(String)
    fechaCreacion = Column(DateTime)
    tipoDocumentoID = Column(Integer)
    estadoDocumentoID = Column(Integer)
    ultimaModificacion = Column(DateTime)
    esActual = Column(Boolean)
    idLegal = Column(String)
    checksum = Column(VARBINARY)

class IaAnalisis(Base):
    __tablename__ = 'pv_iaAnalisis'
    analisisId = Column(Integer, primary_key=True)
    fechaSolicitud = Column(DateTime)
    iaEstadoID = Column(Integer)
    fechaComienzo = Column(DateTime)
    fechaFinalizacion = Column(DateTime)
    infoid = Column(Integer)
    contextoID = Column(Integer)
    documentoID = Column(Integer)

class Log(Base):
    __tablename__ = 'pv_logs'
    logid = Column(Integer, primary_key=True)
    descripcion = Column(String)
    timestamp = Column(DateTime)
    computador = Column(String)
    usuario = Column(String)
    trace = Column(String)
    refId1 = Column(Integer)
    refId2 = Column(Integer)
    valor1 = Column(String)
    valor2 = Column(String)
    checksum = Column(VARBINARY)
    tipologid = Column(Integer)
    origenlogid = Column(Integer)
    logseveridadid = Column(Integer)

class Usuario(Base):
    __tablename__ = 'pv_usuarios'
    userid = Column(Integer, primary_key=True)

class Permiso(Base):
    __tablename__ = 'pv_permissions'
    permissionId = Column(Integer, primary_key=True)
    code = Column(String)

class UsuarioPermiso(Base):
    __tablename__ = 'pv_usuariosPermisos'
    permisoUsuarioId = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey('pv_usuarios.userid'))
    permisoId = Column(Integer, ForeignKey('pv_permissions.permissionId'))
    enabled = Column(Boolean)
    deleted = Column(Boolean)

class TipoVotacion(Base):
    _tablename_ = 'pv_tipoVotacion'
    tipoVotacionId = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    descripcion = Column(String(500))

class Pregunta(Base):
    _tablename_ = 'pv_preguntas'
    preguntaId = Column(Integer, primary_key=True)
    enunciado = Column(String(500))
    tipoPreguntaId = Column(Integer)
    maxSelecciones = Column(Integer)
    fechaPublicacion = Column(DateTime)
    deleted = Column(Boolean)
    order = Column(Integer)

class Respuesta(Base):
    _tablename_ = 'pv_respuestas'
    respuestaId = Column(Integer, primary_key=True)
    preguntaId = Column(Integer, ForeignKey('pv_preguntas.preguntaId'))
    respuesta = Column(String(50))
    value = Column(String(100))
    order = Column(Integer)
    deleted = Column(Boolean)

class VotacionPregunta(Base):
    _tablename_ = 'pv_votacionPregunta'
    votacionPreguntaId = Column(Integer, primary_key=True)
    votacionId = Column(Integer, ForeignKey('pv_votacion.votacionId'))
    preguntaId = Column(Integer, ForeignKey('pv_preguntas.preguntaId'))