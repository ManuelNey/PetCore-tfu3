from sqlalchemy.exc import IntegrityError

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.Auth.Register.clients.dto import (
    RegisterRequest,
    RegisterResponse,
)
from app.Auth.Register.clients.repository import (
    RegisterRepository,
)


password_context = PasswordHash(
    (
        BcryptHasher(rounds=12),
    )
)


class RegistroInvalidoError(ValueError):
    pass


class RegistroDuplicadoError(ValueError):
    pass


class RegisterService:
    def __init__(
        self,
        repository: RegisterRepository,
    ):
        self.repository = repository

    def registrar_cliente(
        self,
        datos: RegisterRequest,
    ) -> RegisterResponse:
        nombre_limpio = " ".join(
            datos.nombre.split()
        )
        apellido_limpio = " ".join(
            datos.apellido.split()
        )
        documento_limpio = datos.documento.strip()
        correo_limpio = (
            str(datos.correo).strip().lower()
        )
        telefono_limpio = datos.telefono.strip()

        contrasena = (
            datos.contrasena.get_secret_value()
        )
        confirmacion = (
            datos.confirmar_contrasena
            .get_secret_value()
        )

        if nombre_limpio == "":
            raise RegistroInvalidoError(
                "El nombre no puede estar vacío."
            )

        if apellido_limpio == "":
            raise RegistroInvalidoError(
                "El apellido no puede estar vacío."
            )

        if documento_limpio == "":
            raise RegistroInvalidoError(
                "El documento no puede estar vacío."
            )

        if telefono_limpio == "":
            raise RegistroInvalidoError(
                "El teléfono no puede estar vacío."
            )

        if contrasena != confirmacion:
            raise RegistroInvalidoError(
                "Las contraseñas no coinciden."
            )

        if len(contrasena) < 8:
            raise RegistroInvalidoError(
                "La contraseña debe tener "
                "al menos 8 caracteres."
            )

        if len(contrasena) > 72:
            raise RegistroInvalidoError(
                "La contraseña no puede superar "
                "los 72 caracteres."
            )

        if not any(
            caracter.isalpha()
            for caracter in contrasena
        ):
            raise RegistroInvalidoError(
                "La contraseña debe contener "
                "al menos una letra."
            )

        if not any(
            caracter.isdigit()
            for caracter in contrasena
        ):
            raise RegistroInvalidoError(
                "La contraseña debe contener "
                "al menos un número."
            )

        usuario_correo = (
            self.repository.buscar_por_correo(
                correo_limpio
            )
        )

        if usuario_correo is not None:
            raise RegistroDuplicadoError(
                "Ya existe un usuario "
                "con ese correo."
            )

        usuario_documento = (
            self.repository.buscar_por_documento(
                documento_limpio
            )
        )

        if usuario_documento is not None:
            raise RegistroDuplicadoError(
                "Ya existe un usuario "
                "con ese documento."
            )

        contrasena_hash = password_context.hash(
            contrasena
        )

        try:
            usuario = self.repository.crear_cliente(
                nombre=nombre_limpio,
                apellido=apellido_limpio,
                documento=documento_limpio,
                correo=correo_limpio,
                telefono=telefono_limpio,
                contrasena_hash=contrasena_hash,
            )

        except IntegrityError as error:
            raise RegistroDuplicadoError(
                "No se pudo registrar el usuario "
                "porque el correo o documento "
                "ya se encuentra registrado."
            ) from error

        return RegisterResponse(
            id_usuario=usuario["id_usuario"],
            nombre=usuario["nombre"],
            apellido=usuario["apellido"],
            documento=usuario["documento"],
            correo=usuario["correo"],
            telefono=usuario["telefono"],
            rol=usuario["rol"],
        )