from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.Mascotas.dto import (
    MascotaCreate,
    MascotaResponse,
    MascotaUpdate,
)
from app.Mascotas.repository import MascotaRepository
from app.Mascotas.service import MascotaService
from app.Middleware.middleware import obtener_usuario_actual, requerir_rol


router = APIRouter(
    prefix="/mascotas",
    tags=["Mascotas"],
)


def crear_service(session: Session) -> MascotaService:
    """
    Crea el servicio necesario para gestionar las mascotas.
        session: Sesion de SQLAlchemy proporcionada por FastAPI.

    Return:
        Servicio de mascotas configurado.
    """
    repository: MascotaRepository = MascotaRepository(session)

    return MascotaService(repository)


@router.get(
    "",
    response_model=list[MascotaResponse],
)
def listar_mascotas(
    usuario: dict[str, Any] = Depends(
        requerir_rol("CLIENTE")
    ),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    """
    Devuelve las mascotas del cliente autenticado.
        usuario: Informacion del usuario obtenida del token JWT.
        session: Sesion de SQLAlchemy proporcionada por FastAPI.

    Return:
        Lista de mascotas pertenecientes al cliente.

    Raises:
        Si el identificador del clienteno es válido.
    """
    id_cliente: int = usuario["id_usuario"]
    service: MascotaService = crear_service(session)

    try:
        return service.listar_por_cliente(
            id_cliente
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "",
    response_model=MascotaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_mascota(
    datos: MascotaCreate,
    usuario: dict[str, Any] = Depends(
        requerir_rol("CLIENTE")
    ),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Registra una mascota para el cliente autenticado.
        datos: Informacion de la mascota que se registrara.
        usuario: Informacion del usuario obtenida del token JWT

    Return:
        Datos de la mascota registrada.

    Raises:
        HTTPException: Si los datos son invalidos
              """
    id_cliente: int = usuario["id_usuario"]
    service: MascotaService = crear_service(session)

    try:
        return service.crear(
            id_cliente=id_cliente,
            datos=datos,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get("/{id_mascota}", response_model=MascotaResponse)
def ver_mascota(
    id_mascota: int,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Devuelve la ficha de una mascota del cliente autenticado.
        id_mascota: Identificador de la mascota.
        usuario: Informacion del usuario obtenida del token JWT.
        session: Sesion de SQLAlchemy proporcionada por FastAPI.

    Return:
        Datos de la mascota.
    """
    id_cliente: int = usuario["id_usuario"]
    service: MascotaService = crear_service(session)

    return service.obtener_mascota_por_id(id_mascota, id_cliente)

@router.patch("/{id_mascota}", response_model=MascotaResponse)
def actualizar_mascota(
    id_mascota: int,
    datos: MascotaUpdate,
    usuario: dict[str, Any] = Depends(requerir_rol("CLIENTE")),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    id_cliente: int = usuario["id_usuario"]
    service: MascotaService = crear_service(session)

    try:
        return service.actualizar(id_mascota, id_cliente, datos)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.patch(
    "/{id_mascota}/inactivar",
    response_model=MascotaResponse,
)
def inactivar_mascota(id_mascota: int,
    usuario: dict[str, Any] = Depends(
        requerir_rol("CLIENTE")
    ),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Inactiva una mascota del cliente autenticado.
        id_mascota: Identificador de la mascota.
        usuario: Informacion obtenida del token JWT.
        session: Sesion de SQLAlchemy proporcionada por FastAPI.

    Return:
        Datos actualizados de la mascota.

    Raises:
        HTTPException: Si la mascota no existe.
    """
    id_cliente: int = usuario["id_usuario"]
    service: MascotaService = crear_service(session)

    try:
        return service.inactivar(
            id_mascota=id_mascota,
            id_cliente=id_cliente,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.patch(
    "/{id_mascota}/activar",
    response_model=MascotaResponse,
)
def activar_mascota(id_mascota: int,
    usuario: dict[str, Any] = Depends(
        requerir_rol("CLIENTE")
    ),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Activa una mascota del cliente autenticado.
        id_mascota: Identificador de la mascota.
        usuario: Informacion obtenida del token JWT.
        session: Sesion de SQLAlchemy proporcionada por FastAPI.

    Return:
        Datos actualizados de la mascota.

    Raises:
        HTTPException: Si la mascota no existe.
    """
    id_cliente: int = usuario["id_usuario"]
    service: MascotaService = crear_service(session)

    try:
        return service.activar(
            id_mascota=id_mascota,
            id_cliente=id_cliente,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error