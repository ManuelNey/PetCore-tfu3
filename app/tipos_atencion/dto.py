from pydantic import BaseModel, ConfigDict, Field

#POST
# Define los datos necesarios para crear un tipo de atención
class TipoAtencionCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = None
    duracion_minutos: int = Field(gt=0, multiple_of=15)
    reservable_cliente: bool = True

#GET
# Define los campos que FastAPI devolverá en la respuesta
class TipoAtencionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_tipo_atencion: int
    nombre: str
    descripcion: str | None
    duracion_minutos: int
    reservable_cliente: bool
    estado: str