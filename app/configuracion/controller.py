from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.database import get_session
from app.Middleware.middleware import requerir_rol
from app.configuracion.dto import (
    ConfiguracionResponse,
    ConfiguracionUpdate,
)
from app.configuracion.repository import ConfiguracionRepository
from app.configuracion.service import (
    ClaveDesconocidaError,
    ConfiguracionService,
    ValorInvalidoError,
)


# Solo el ADMINISTRADOR puede ver y cambiar la configuración.
router = APIRouter(
    prefix="/admin/configuracion",
    tags=["Configuración"],
)


def crear_service(session):
    repository = ConfiguracionRepository(session)

    return ConfiguracionService(repository)


#GET /admin/configuracion
@router.get(
    "",
    response_model=list[ConfiguracionResponse],
    status_code=status.HTTP_200_OK,
)
def listar_configuracion(
    _usuario: dict = Depends(requerir_rol("ADMINISTRADOR")),
    session=Depends(get_session),
):
    return crear_service(session).listar()


#GET /admin/configuracion/{clave}
@router.get(
    "/{clave}",
    response_model=ConfiguracionResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_configuracion(
    clave: str,
    _usuario: dict = Depends(requerir_rol("ADMINISTRADOR")),
    session=Depends(get_session),
):
    try:
        return crear_service(session).obtener(clave)

    except ClaveDesconocidaError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


#PUT /admin/configuracion/{clave}
@router.put(
    "/{clave}",
    response_model=ConfiguracionResponse,
    status_code=status.HTTP_200_OK,
)
def actualizar_configuracion(
    clave: str,
    datos: ConfiguracionUpdate,
    usuario: dict = Depends(requerir_rol("ADMINISTRADOR")),
    session=Depends(get_session),
):
    try:
        return crear_service(session).actualizar(
            clave=clave,
            valor=datos.valor,
            id_usuario=usuario["id_usuario"],
        )

    except ClaveDesconocidaError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ValorInvalidoError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error