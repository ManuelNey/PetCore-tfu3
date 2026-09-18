from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.bcrypt import BcryptHasher

from app.config import settings
from app.Auth.login.dto import (
    LoginRequest,
    LoginResponse,
    UsuarioLoginResponse,
)
from app.Auth.login.repository import LoginRepository


password_context = PasswordHash(
    (
        BcryptHasher(rounds=12),
    )
)

ALGORITMO_JWT = "HS256"


class LoginService:
    def __init__(self, repository: LoginRepository):
        self.repository = repository

    def iniciar_sesion(
        self,
        datos: LoginRequest,
    ) -> LoginResponse:
        correo_limpio = str(datos.correo).strip().lower()

        usuario = self.repository.buscar_por_correo(
            correo_limpio
        )

        # Verificar que el usuario exista.
        if usuario is None:
            self.repository.registrar_evento(
                correo=correo_limpio,
                resultado="FALLIDO",
                detalle="No existe un usuario con ese correo.",
            )

            raise ValueError(
                "Correo o contraseña incorrectos."
            )

        ahora = datetime.now(timezone.utc)

        # Verificar si la cuenta está bloqueada.
        if (
            usuario["bloqueado_hasta"] is not None
            and usuario["bloqueado_hasta"] > ahora
        ):
            self.repository.registrar_evento(
                id_usuario=usuario["id_usuario"],
                correo=correo_limpio,
                resultado="BLOQUEADO",
                detalle=(
                    "Intento de inicio de sesión durante "
                    "el bloqueo temporal."
                ),
            )

            raise ValueError(
                "La cuenta está temporalmente bloqueada."
            )

        # Verificar que el usuario esté activo.
        if usuario["estado"] != "ACTIVO":
            self.repository.registrar_evento(
                id_usuario=usuario["id_usuario"],
                correo=correo_limpio,
                resultado="RECHAZADO",
                detalle="El usuario se encuentra inactivo.",
            )

            raise ValueError(
                "El usuario se encuentra inactivo."
            )

        contrasena_ingresada = (
            datos.contrasena.get_secret_value()
        )

        try:
            contrasena_correcta = password_context.verify(
                contrasena_ingresada,
                usuario["contrasena_hash"],
            )
        except (UnknownHashError, TypeError, ValueError):
            contrasena_correcta = False

        # Procesar contraseña incorrecta.
        if not contrasena_correcta:
            nuevos_intentos = (
                usuario["intentos_inicio"] + 1
            )

            bloqueado_hasta = None
            resultado = "FALLIDO"

            if nuevos_intentos >= settings.LOGIN_MAX_INTENTOS:
                bloqueado_hasta = ahora + timedelta(
                    minutes=settings.LOGIN_BLOQUEO_MINUTOS
                )

                nuevos_intentos = 0
                resultado = "BLOQUEADO"

            self.repository.registrar_intento_fallido(
                id_usuario=usuario["id_usuario"],
                correo=correo_limpio,
                intentos_inicio=nuevos_intentos,
                bloqueado_hasta=bloqueado_hasta,
                resultado=resultado,
            )

            raise ValueError(
                "Correo o contraseña incorrectos."
            )

        rol = usuario["rol"]

        token, expires_in = self._crear_token(
            id_usuario=usuario["id_usuario"],
            rol=rol,
        )

        # Reiniciar los intentos después del acceso correcto.
        self.repository.registrar_login_exitoso(
            id_usuario=usuario["id_usuario"],
            correo=correo_limpio,
        )

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            usuario=UsuarioLoginResponse(
                id_usuario=usuario["id_usuario"],
                nombre=usuario["nombre"],
                apellido=usuario["apellido"],
                correo=usuario["correo"],
                rol=rol,
            ),
        )

    def _crear_token(
        self,
        id_usuario: int,
        rol: str,
    ) -> tuple[str, int]:
        ahora = datetime.now(timezone.utc)

        duracion = timedelta(
            minutes=(
                settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

        fecha_expiracion = ahora + duracion

        payload = {
            "sub": str(id_usuario),
            "rol": rol,
            "type": "access",
            "iss": "pet-core-api",
            "aud": "pet-core-client",
            "iat": ahora,
            "nbf": ahora,
            "exp": fecha_expiracion,
            "jti": str(uuid4()),
        }

        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=ALGORITMO_JWT,
        )

        return token, int(duracion.total_seconds())