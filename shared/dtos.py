from typing import Optional
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
    propuestaId: int = Field(..., description="ID de la propuesta que recibe el comentario")
    usuarioId: int = Field(..., description="ID del usuario que hace el comentario")
    titulo: str = Field(..., max_length=100, description="Título del comentario")
    cuerpo: str = Field(..., description="Contenido del comentario")
    organizacionId: Optional[int] = Field(None, description="ID de la organización, si aplica")

    class Config:
        orm_mode = True