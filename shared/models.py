from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class Propuesta(Base):
    __tablename__ = "Propuestas"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200))
    descripcion = Column(String)
    usuario_id = Column(Integer)
    estado = Column(String(50), default="pendiente")

class Voto(Base):
    __tablename__ = "Votos"
    id = Column(Integer, primary_key=True)
    propuesta_id = Column(Integer, ForeignKey("Propuestas.id"))
    usuario_id = Column(Integer)
    voto_cifrado = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)

class Comentario(Base):
    __tablename__ = "Comentarios"
    id = Column(Integer, primary_key=True)
    propuesta_id = Column(Integer)
    usuario_id = Column(Integer)
    contenido = Column(String)
    estado = Column(String, default="pendiente")

class Inversion(Base):
    __tablename__ = "Inversiones"
    id = Column(Integer, primary_key=True)
    propuesta_id = Column(Integer)
    usuario_id = Column(Integer)
    monto = Column(Numeric(18, 2))
    fecha = Column(DateTime, default=datetime.utcnow)
