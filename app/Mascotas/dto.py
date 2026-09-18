from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MascotaCreate(BaseModel):
    """
    Representa los datos necesarios para registrar una mascota.
    """

    nombre: str = Field(min_length=1, max_length=100)
    especie: str = Field(min_length=1, max_length=100)
    raza: str | None = Field(default=None, max_length=100)
    fecha_nacimiento: date | None = Field(default=None)


class MascotaResponse(BaseModel):
    """
    Representa los datos de una mascota enviados al frontend.
    """

    model_config = ConfigDict(from_attributes=True)

    id_mascota: int
    nombre: str
    especie: str
    raza: str | None
    fecha_nacimiento: date | None
    sexo: str | None
    observaciones: str | None
    estado: str

class MascotaUpdate(BaseModel):
    nombre: str | None = None
    raza: str | None = None
    fecha_nacimiento: date | None = None
    sexo: str | None = None
    observaciones: str | None = None
    estado: str | None = None