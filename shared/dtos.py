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

class CrearActualizarPropuestaDTO(BaseModel):
    PropuestaID: Optional[int] = None
    CategoriaID: int
    Descripcion: str
    ImgURL: Optional[str] = None
    FechaInicio: Optional[str] = None  # ISO string o None
    FechaFin: Optional[str] = None
    Comentarios: int
    TipoPropuestaID: int
    OrganizacionID: int
    SegmentosDirigidosJS: str  # JSON string
    SegmentosImpactoJS: str    # JSON string
    AdjuntosJS: str            # JSON string
    UsuarioAccion: int
    EquipoOrigen: str