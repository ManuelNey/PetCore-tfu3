from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_session
from app.Middleware.middleware import requerir_rol
from app.tipos_atencion.dto import (
    TipoAtencionCreate,
    TipoAtencionResponse,
)
from app.tipos_atencion.repository import TipoAtencionRepository
from app.tipos_atencion.service import TipoAtencionService


router = APIRouter(
    prefix="/tipos-atencion",
    tags=["Tipos de atención"],
)


def crear_service(session):
    repository = TipoAtencionRepository(session)

    return TipoAtencionService(repository)


@router.get("", response_model=list[TipoAtencionResponse])
def listar_tipos_atencion(
    session=Depends(get_session),
    _usuario: dict = Depends(requerir_rol("CLIENTE", "VETERINARIO")),
):
    service = crear_service(session)

    return service.listar()


@router.post(
    "",
    response_model=TipoAtencionResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_tipo_atencion(
    datos: TipoAtencionCreate,
    session=Depends(get_session),
):
    service = crear_service(session)

    try:
        return service.crear(datos)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
