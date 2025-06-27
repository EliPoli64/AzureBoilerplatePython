from datetime import datetime
from typing import List, Optional
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

class PreguntaRespuestaDTO(BaseModel):
    pregunta: str
    respuestas: List[str]  # Puede adaptarse a objetos si las respuestas son más complejas
class PreguntaDTO(BaseModel):
    preguntaID: int = Field(..., description="ID de la pregunta que se asocia a la votación")


class CrearConfiguracionVotacionDTO(BaseModel):
    usuarioID: int = Field(..., description="ID del usuario que configura la votación")
    propuestaID: int = Field(..., description="ID de la propuesta asociada")
    
    titulo: str = Field(..., description="Título de la votación")
    descripcion: Optional[str] = Field(None, description="Descripción de la votación")
    fechaInicio: datetime = Field(..., description="Fecha de inicio de la votación")
    fechaFin: datetime = Field(..., description="Fecha de fin de la votación")

    tipoVotacionId: int = Field(..., description="Tipo de votación (única, múltiple, calificación, etc.)")
    privada: bool = Field(..., description="Indica si la votación es privada")
    esSecreta: bool = Field(..., description="Indica si la votación es secreta")

    segmentosSeleccionados: List[int] = Field(default_factory=list, description="IDs de los segmentos poblacionales meta")

    # Opcional si luego agregás implementación para estas restricciones
    geografiaImpacto: Optional[str] = Field(None, description="Zona de impacto: nacional, regional, municipal, etc.")
    restriccionesIP: Optional[List[str]] = Field(None, description="Restricciones de IP permitidas")
    horariosPermitidos: Optional[List[str]] = Field(None, description="Horarios permitidos (HH:mm-HH:mm)")

    preguntas: List[PreguntaDTO] = Field(..., description="Lista de preguntas por ID asociadas a la votación")

class VotoDTO(BaseModel):
    preguntaID: int = Field(..., description = "ID de la pregunta a contestar")
    respuestaID: int = Field(..., description = "ID de la respuesta con la que se contestará")
    valor: str = Field(..., max_length=100, description="Contenido de la respuesta")
    pesoRespuesta: int = Field(..., description = "ID del peso de la respuesta")