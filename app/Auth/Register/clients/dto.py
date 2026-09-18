from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
)


class RegisterRequest(BaseModel):
    nombre: str = Field(
        min_length=1,
        max_length=100,
    )
    apellido: str = Field(
        min_length=1,
        max_length=100,
    )
    documento: str = Field(
        min_length=1,
        max_length=30,
    )
    correo: EmailStr
    telefono: str = Field(
        min_length=1,
        max_length=30,
    )
    contrasena: SecretStr
    confirmar_contrasena: SecretStr


class RegisterResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id_usuario: int
    nombre: str
    apellido: str
    documento: str
    correo: str
    telefono: str
    rol: str