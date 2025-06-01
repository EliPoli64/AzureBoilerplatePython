from pydantic import BaseModel, Field

class PropuestaDTO(BaseModel):
    id: int = Field(default=0)
    titulo: str
    descripcion: str
    usuario_id: int

class InversionDTO(BaseModel):
    propuesta_id: int
    usuario_id: int
    monto: float

class VotoDTO(BaseModel):
    propuesta_id: int
    usuario_id: int
    voto_plano: str

class ComentarioDTO(BaseModel):
    propuesta_id: int
    usuario_id: int
    contenido: str