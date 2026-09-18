from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.Middleware.middleware import requerir_rol
from app.database import get_session
from app.Auth.me.dto import MeResponse
from app.Auth.me.repository import MeRepository
from app.Auth.me.service import MeService


router = APIRouter(
    prefix="/auth/me"
)


def crear_service(session):
    repository = MeRepository(session)

    return MeService(repository)


@router.get(
    "",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_mi_usuario(
    usuario_token: dict = Depends(
        requerir_rol(
            "ADMINISTRADOR",
            "CLIENTE",
            "VETERINARIO",
        )
    ),
    session=Depends(get_session),
):
    service = crear_service(session)

    try:
        return service.obtener(
            id_usuario=usuario_token["id_usuario"],
            rol=usuario_token["rol"],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error