from app.Auth.me.dto import MeResponse
from app.Auth.me.repository import MeRepository


class MeService:
    def __init__(
        self,
        repository: MeRepository,
    ):
        self.repository = repository

    def obtener(
        self,
        id_usuario: int,
        rol: str,
    ) -> MeResponse:
        usuario = self.repository.buscar_por_id(
            id_usuario
        )

        if usuario is None:
            raise ValueError(
                "El usuario del token no existe."
            )

        if usuario["estado"] != "ACTIVO":
            raise ValueError(
                "El usuario se encuentra inactivo."
            )

        return MeResponse(
            id_usuario=usuario["id_usuario"],
            nombre=usuario["nombre"],
            apellido=usuario["apellido"],
            correo=usuario["correo"],
            rol=rol,
        )