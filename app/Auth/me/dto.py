from pydantic import BaseModel, ConfigDict


class MeResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id_usuario: int
    nombre: str
    apellido: str
    correo: str
    rol: str