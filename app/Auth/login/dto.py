from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
)


# Datos necesarios para iniciar sesión
class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: SecretStr = Field(
        min_length=1,
        max_length=128,
    )


# Datos del usuario autenticado
class UsuarioLoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nombre: str
    apellido: str
    correo: EmailStr
    rol: str


# Respuesta del login
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    usuario: UsuarioLoginResponse