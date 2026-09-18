from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.database import get_session
from app.Auth.login.dto import (
    LoginRequest,
    LoginResponse,
)
from app.Auth.login.repository import LoginRepository
from app.Auth.login.service import LoginService


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)


def crear_service(session):
    repository = LoginRepository(session)

    return LoginService(repository)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def iniciar_sesion(
    datos: LoginRequest,
    session=Depends(get_session),
):
    service = crear_service(session)

    try:
        return service.iniciar_sesion(datos)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error