from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    VARBINARY,
    Integer,
    LargeBinary,
    String,
    DateTime,
    Numeric
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Usuario(Base):
    __tablename__ = "pv_usuarios"
    __table_args__ = {'extend_existing': True}
    userid = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    primerApellido = Column(String(50), nullable=False)
    segundoApellido = Column(String(50), nullable=True)
    fechaNacimiento = Column(DateTime, nullable=False)
    identificacion = Column(String(9), nullable=False, unique=True)
    nacional = Column(Boolean, nullable=False)
    checksum = Column(VARBINARY(260))
    sexo = Column(Boolean, nullable=False)
    
    llaves = relationship("LlaveUsuario", back_populates="usuario")
    votaciones_publicas = relationship("UsuarioVotacionPublica", back_populates="usuario")
    propuestas = relationship("Propuesta", back_populates="usuario")
    
class LlaveUsuario(Base):
    __tablename__ = 'pv_llavesUsuarios'
    __table_args__ = {'extend_existing': True}
    llaveUsuarioID = Column(Integer, primary_key=True, autoincrement=True)
    llaveCifrada = Column(VARBINARY(260), nullable=False)
    usuarioID = Column(Integer, ForeignKey('pv_usuarios.userid'), nullable=False)
    esActiva = Column(Boolean, nullable=False)
    ultimaModificacion = Column(DateTime)
    
    usuario = relationship("Usuario", back_populates="llaves")
"""
class MediaFiles(Base):
    __tablename__ = 'pv_mediaFiles'
    
    mediaFileId = Column(Integer, primary_key=True, autoincrement=True)
    documentURL = Column(String(200), nullable=False)
    lastUpdate = Column(DateTime, nullable=False)
    deleted = Column(Boolean, nullable=False)
    mediaTypeId = Column(Integer, ForeignKey('pv_mediaTypes.mediaTypeId'), nullable=False)
    
    media_type = relationship("MediaTypes")
"""

class Segmento(Base):
    __tablename__ = 'pv_segmento'
    __table_args__ = {'extend_existing': True}

    segmentoID = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(300), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    deleted = Column(Boolean, nullable=False, default=False)
    fechaCreacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    usuarioID = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Segmento(id={self.segmentoID}, nombre={self.nombre})>"

class SegmentoPropuesta(Base):
    __tablename__ = 'pv_propuestaSegmentosDirigidos'
    __table_args__ = {'extend_existing': True}

    propuestaSegmentoDirigoID = Column(Integer, primary_key=True, autoincrement=True)
    propuestaID = Column(Integer, ForeignKey('pv_propuestas.propuestaid'), nullable=False)
    segementoID = Column(Integer, ForeignKey('pv_segmento.segmentoID'), nullable=False)
    usuarioID = Column(Integer, ForeignKey('pv_usuarios.userid'), nullable=False)
    deleted = Column(Boolean, nullable=False, default=False)
    checksum = Column(VARBINARY(256), nullable=False)

    def __repr__(self):
        return f"<SegmentoPropuesta(propuestaID={self.propuestaID}, segmentoID={self.segementoID})>"

class PropuestaVotacion(Base):
    __tablename__ = 'pv_propuestaVotacion'
    __table_args__ = {'extend_existing': True}
    propuestaVotacionID = Column(Integer, primary_key=True)
    votacionID = Column(Integer, ForeignKey('pv_votacion.votacionID'), nullable=False)
    propuestaID = Column(Integer, ForeignKey('pv_propuestas.propuestaid'), nullable=False)
    usuarioID = Column(Integer, ForeignKey('pv_usuarios.userid'), nullable=False)
    deleted = Column(Boolean, nullable=False)
    checksum = Column(VARBINARY(256), nullable=False)
    
    votacion = relationship("Votacion")
    propuesta = relationship("Propuesta")
    usuario = relationship("Usuario")

class UsuarioVotacionPublica(Base):
    __tablename__ = 'pv_usuarioVotacionPublica'
    __table_args__ = {'extend_existing': True}
    usuarioVotacionPubID = Column(Integer, primary_key=True, autoincrement=True)
    usuarioID = Column(Integer, ForeignKey('pv_usuarios.userid'), nullable=False)
    respuestaParticipanteID = Column(Integer, ForeignKey('pv_respuestaParticipante.respuestaParticipanteID'), nullable=False)
    checksum = Column(VARBINARY(256), nullable=False)
    ultimaModificacion = Column(DateTime, nullable=False)
    votacionID = Column(Integer, ForeignKey('pv_votacion.votacionID'), nullable=False)
    
    usuario = relationship("Usuario", back_populates="votaciones_publicas")
    respuesta = relationship("Voto")
    votacion = relationship("Votacion")

class Pregunta(Base):
    __tablename__ = "pv_preguntas"
    __table_args__ = {'extend_existing': True}
    preguntaID = Column(Integer, primary_key=True, autoincrement=True)
    enunciado = Column(String(500), nullable=True)
    tipoPreguntaID = Column(Integer, nullable=False)
    maxSelecciones = Column(Integer, nullable=False)
    fechaPublicacion = Column(DateTime, nullable=False)
    deleted = Column(Boolean, nullable=False)
    order = Column(Integer, nullable=False)
    checksum = Column(VARBINARY(256), nullable=False)

    respuestas = relationship("Respuesta", back_populates="pregunta")


class PesoRespuesta(Base):
    __tablename__ = "pv_pesoRespuesta"
    __table_args__ = {'extend_existing': True}

    pesoID = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    multiplicador = Column(Numeric(14, 2), nullable=True)


class Respuesta(Base):
    __tablename__ = "pv_respuestas"
    __table_args__ = {'extend_existing': True}
    respuestaID = Column(Integer, primary_key=True, autoincrement=True)
    preguntaID = Column(Integer, ForeignKey('pv_preguntas.preguntaID'), nullable=False)
    respuesta = Column(String(50), nullable=False)
    url = Column(String(500), nullable=True)
    value = Column(String(100), nullable=False)
    order = Column(Integer, nullable=False)
    deleted = Column(Boolean, nullable=False)
    checksum = Column(VARBINARY(256), nullable=False)

    pregunta = relationship("Pregunta", back_populates="respuestas")

class VotacionPregunta(Base):
    __tablename__ = 'pv_votacionPregunta'
    __table_args__ = {'extend_existing': True}
    votacionPreguntaID = Column(Integer, primary_key=True, autoincrement=True)
    votacionID = Column(Integer, ForeignKey('pv_votacion.votacionID'), nullable=False)
    preguntaID = Column(Integer, ForeignKey('pv_preguntas.preguntaID'), nullable=False)
    
    votacion = relationship("Votacion")
    pregunta = relationship("Pregunta")

class Propuesta(Base):
    __tablename__ = "pv_propuestas"
    __table_args__ = {'extend_existing': True}
    propuestaId = Column('propuestaid', Integer, primary_key=True, autoincrement=True)
    categoriaId = Column(Integer, nullable=False)
    descripcion = Column(String(200), nullable=True)
    imgURL = Column(String(300), nullable=True)
    fechaInicio = Column(DateTime, nullable=False, default=datetime.utcnow)
    userId = Column(Integer, ForeignKey('pv_usuarios.userid'), nullable=False)
    fechaFin = Column(DateTime, nullable=True)
    checksum = Column(LargeBinary(300), nullable=False)
    comentarios = Column(Boolean, nullable=False)
    tipoPropuestaId = Column(Integer, nullable=False)
    estadoId = Column(Integer, nullable=False)
    organizacionId = Column(Integer, nullable=True)
    
    usuario = relationship("Usuario")
    votaciones = relationship("PropuestaVotacion", back_populates="propuesta")

class DetalleComentarios(Base):
    __tablename__ = "pv_detalleComentarios"
    __table_args__ = {'extend_existing': True}
    detalleComentarioId = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(100), nullable=False)
    cuerpo = Column(String, nullable=False)
    fechaPublicacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    usuarioId = Column(Integer, nullable=False)
    organizacionId = Column(Integer, nullable=True)

    comentariosPropuesta = relationship("ComentarioPropuesta", back_populates="detalleComentario", cascade="all, delete-orphan")

class Votacion(Base):
    __tablename__ = "pv_votacion"
    __table_args__ = {'extend_existing': True}
    votacionID = Column('votacionID', Integer, primary_key=True, autoincrement=True)
    tipoVotacionId = Column(Integer, nullable=False)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(String, nullable=True)  # nvarchar(max)
    fechaInicio = Column(DateTime, nullable=False)
    fechaFin = Column(DateTime, nullable=False)
    estadoVotacionId = Column(Integer, nullable=False)
    ultimaModificacion = Column(DateTime, nullable=False)
    privada = Column(Boolean, nullable=False)
    esSecreta = Column(Boolean, nullable=False)

    preguntas = relationship("VotacionPregunta", back_populates="votacion")
    propuestas = relationship("PropuestaVotacion", back_populates="votacion")
    votaciones_publicas = relationship("UsuarioVotacionPublica", back_populates="votacion")
    
class ComentarioPropuesta(Base):
    __tablename__ = "pv_comentariosPropuesta"
    __table_args__ = {'extend_existing': True}
    comentarioId = Column(Integer, primary_key=True, autoincrement=True)
    detalleComentarioId = Column(Integer, ForeignKey("pv_detalleComentarios.detalleComentarioId"), nullable=False)
    estadoComentId = Column(Integer, nullable=False)
    propuestaId = Column(Integer, ForeignKey("pv_propuestas.propuestaid"), nullable=False)

    # Relación inversa
    detalleComentario = relationship("DetalleComentarios", back_populates="comentariosPropuesta")


class Inversion(Base):
    __tablename__ = "pv_inversion"
    __table_args__ = {'extend_existing': True}
    inversionId = Column(Integer, primary_key=True, autoincrement=True)
    proyectoId = Column(Integer, nullable=False)
    usuarioId = Column(Integer, nullable=False)
    transaccionId = Column(Integer, nullable=False)
    organizacionId = Column(Integer, nullable=True)

class Documento(Base):
    __tablename__ = 'pv_documento'
    __table_args__ = {'extend_existing': True}
    documentoID = Column(Integer, primary_key=True)
    nombre = Column(String)
    fechaCreacion = Column(DateTime)
    tipoDocumentoID = Column(Integer)
    estadoDocumentoID = Column(Integer)
    ultimaModificacion = Column(DateTime)
    esActual = Column(Boolean)
    idLegal = Column(String)
    checksum = Column(VARBINARY)
class Log(Base):
    __tablename__ = 'pv_logs'
    __table_args__ = {'extend_existing': True}
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
class IaAnalisis(Base):
    __tablename__ = 'pv_iaAnalisis'
    __table_args__ = {'extend_existing': True}
    analisisId = Column(Integer, primary_key=True)
    fechaSolicitud = Column(DateTime)
    iaEstadoID = Column(Integer)
    fechaComienzo = Column(DateTime)
    fechaFinalizacion = Column(DateTime)
    infoid = Column(Integer)
    contextoID = Column(Integer)
    documentoID = Column(Integer)



class EstadoComentario(Base):
    __tablename__ = 'pv_estadoComentarios'
    __table_args__ = {'extend_existing': True}
    estadoComentId = Column(Integer, primary_key=True)
    nombre = Column(String)

class Permiso(Base):

    __tablename__ = 'pv_permissions'
    __table_args__ = {'extend_existing': True}
    permissionId = Column(Integer, primary_key=True)

    code = Column(String)



class UsuarioPermiso(Base):
    __tablename__ = 'pv_usuariosPermisos'
    __table_args__ = {'extend_existing': True}
    permisoUsuarioId = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey('pv_usuarios.userid'))
    permisoId = Column(Integer, ForeignKey('pv_permissions.permissionId'))
    enabled = Column(Boolean)
    deleted = Column(Boolean)

class Voto(Base):
    __tablename__ = "pv_respuestaParticipante"
    __table_args__ = {'extend_existing': True}
    respuestaParticipanteID = Column(Integer, primary_key = True)
    preguntaID = Column(Integer, ForeignKey("pv_preguntas.preguntaID"), nullable = False)
    respuestaID = Column(Integer, ForeignKey("pv_respuestas.respuestaID"),nullable = False)
    checksum = Column(VARBINARY, nullable = False)
    valor = Column(String)
    fechaRespuesta = Column(DateTime)
    ncRespuesta = Column(VARBINARY)
    tokenGUID = Column(String, unique=True)
    pesoRespuesta = Column(Integer, ForeignKey("pv_pesoRespuesta.pesoID"),nullable=False)