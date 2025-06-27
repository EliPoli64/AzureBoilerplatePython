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

class ComentarioDTO(BaseModel):
    titulo: str
    cuerpo: str
    usuarioId: int
    organizacionId: int
    propuestaId: int

class CrearActualizarPropuestaDTO(BaseModel):
    PropuestaID: Optional[int] = None
    CategoriaID: int
    Descripcion: str
    ImgURL: Optional[str] = None
    FechaInicio: Optional[str] = None  # ISO string o None
    FechaFin: Optional[str] = None
    Comentarios: bool
    TipoPropuestaID: int
    OrganizacionID: int
    SegmentosDirigidosJS: str  # JSON string
    SegmentosImpactoJS: str    # JSON string
    AdjuntosJS: str            # JSON string
    UsuarioAccion: int
    EquipoOrigen: str

class VotoDTO(BaseModel):
    preguntaID: int = Field(..., description = "ID de la pregunta a contestar")
    respuestaID: int = Field(..., description = "ID de la respuesta con la que se contestará")
    valor: str = Field(..., max_length=100, description="Contenido de la respuesta")
    pesoRespuesta: int = Field(..., description = "ID del peso de la respuesta")

class RevisarPropuestaDTO(BaseModel):
    propuesta_id: int
    revisor_id: int
    resultado_final: str #'Aprobada', 'Rechazada'
    comentarios_revision: Optional[str] = None
    tipo_revision: str 