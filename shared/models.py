from sqlalchemy import (
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


class Propuesta(Base):
    __tablename__ = "pv_propuestas"

    propuestaId = Column(Integer, primary_key=True, autoincrement=True)
    categoriaId = Column(Integer, nullable=False)
    descripcion = Column(String(200), nullable=True)
    imgURL = Column(String(300), nullable=True)
    fechaInicio = Column(DateTime, nullable=False, default=datetime.utcnow)
    userId = Column(Integer, nullable=False)
    fechaFin = Column(DateTime, nullable=True)
    checksum = Column(LargeBinary(300), nullable=False)
    comentarios = Column(Boolean, nullable=False)
    tipoPropuestaId = Column(Integer, nullable=False)
    estadoId = Column(Integer, nullable=False)
    organizacionId = Column(Integer, nullable=True)

class DetalleComentarios(Base):
    __tablename__ = "pv_detalleComentarios"

    detalleComentarioId = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(100), nullable=False)
    cuerpo = Column(String, nullable=False)
    fechaPublicacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    usuarioId = Column(Integer, nullable=False)
    organizacionId = Column(Integer, nullable=True)

    comentariosPropuesta = relationship("ComentarioPropuesta", back_populates="detalleComentario", cascade="all, delete-orphan")

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

class ComentarioPropuesta(Base):
    __tablename__ = "pv_comentariosPropuesta"

    comentarioId = Column(Integer, primary_key=True, autoincrement=True)
    detalleComentarioId = Column(Integer, ForeignKey("pv_detalleComentarios.detalleComentarioId"), nullable=False)
    estadoComentId = Column(Integer, nullable=False)
    propuestaId = Column(Integer, ForeignKey("pv_propuestas.propuestaId"), nullable=False)

    # Relación inversa
    detalleComentario = relationship("DetalleComentarios", back_populates="comentariosPropuesta")


class Inversion(Base):
    __tablename__ = "pv_inversion"

    inversionId = Column(Integer, primary_key=True, autoincrement=True)
    proyectoId = Column(Integer, nullable=False)
    usuarioId = Column(Integer, nullable=False)
    transaccionId = Column(Integer, nullable=False)
    organizacionId = Column(Integer, nullable=True)
