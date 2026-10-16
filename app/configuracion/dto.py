from datetime import datetime

from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr


# PUT
# Nuevo valor de un parámetro. Acepta "3" o 3.
class ConfiguracionUpdate(BaseModel):
    valor: StrictInt | StrictStr


# GET / PUT
class ConfiguracionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clave: str
    valor: str
    fecha_modificacion: datetime | None
    id_usuario_modificador: int | None