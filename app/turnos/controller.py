from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.disponibilidad.dto import DisponibilidadResponse
from app.disponibilidad.repository import DisponibilidadRepository
from app.disponibilidad.service import DisponibilidadService
from app.Middleware.middleware import requerir_rol
from app.turnos.dto import ConsultaCreate, ConsultaCreateResponse, TurnoCreate, TurnoResponse
from app.turnos.excepciones import HorarioNoDisponibleError, TurnoEnPasadoError
from app.turnos.repository import TurnoRepository
from app.turnos.service import TurnoService

router = APIRouter(prefix="/turnos", tags=["Turnos"])


def crear_service(session: Session) -> TurnoService:
    repository: TurnoRepository = TurnoRepository(session)
    return TurnoService(repository)


@router.get("", response_model=list[TurnoResponse])
def listar_turnos(
    periodo: Literal["proximos", "pasados", "todos"] = "proximos",
    usuario: dict[str, Any] = Depends(requerir_rol("CLIENTE")),
    session: Session = Depends(get_session),
) -> list[dict]:
    id_cliente: int = usuario["id_usuario"]
    return crear_service(session).listar_por_cliente(id_cliente, periodo)


@router.get("/{id_turno}", response_model=TurnoResponse)
def ver_turno(
    id_turno: int,
    usuario: dict[str, Any] = Depends(requerir_rol("CLIENTE")),
    session: Session = Depends(get_session),
) -> dict:
    id_cliente: int = usuario["id_usuario"]
    try:
        return crear_service(session).obtener_por_id(id_turno, id_cliente)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("", response_model=TurnoResponse, status_code=status.HTTP_201_CREATED)
def crear_turno(
    datos: TurnoCreate,
    usuario: dict[str, Any] = Depends(requerir_rol("CLIENTE")),
    session: Session = Depends(get_session),
) -> dict:
    id_cliente: int = usuario["id_usuario"]

    try:
        return crear_service(session).crear(id_cliente, datos)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except TurnoEnPasadoError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except HorarioNoDisponibleError as error:
        disponibilidad = DisponibilidadService(DisponibilidadRepository(session)).calcular(
            datos.id_veterinario, datos.fecha, datos.id_tipo_atencion
        )
        detalle = {
            "error": "HORARIO_NO_DISPONIBLE",
            "mensaje": "Otro cliente reservó ese horario segundos antes de tu confirmación.",
            "seleccion_conservada": {
                "id_mascota": datos.id_mascota,
                "id_tipo_atencion": datos.id_tipo_atencion,
                "id_veterinario": datos.id_veterinario,
            },
            "disponibilidad_actualizada": DisponibilidadResponse(**disponibilidad).model_dump(
                mode="json", exclude_none=True
            ),
        }
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detalle) from error


@router.post("/{id_turno}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_turno(
    id_turno: int,
    usuario: dict[str, Any] = Depends(requerir_rol("CLIENTE")),
    session: Session = Depends(get_session),
) -> None:
    id_cliente: int = usuario["id_usuario"]
    try:
        crear_service(session).cancelar(id_turno, id_cliente)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post(
    "/{id_turno}/consulta",
    response_model=ConsultaCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_consulta(
    id_turno: int,
    datos: ConsultaCreate,
    usuario: dict[str, Any] = Depends(requerir_rol("VETERINARIO")),
    session: Session = Depends(get_session),
) -> dict:
    id_veterinario: int = usuario["id_usuario"]

    try:
        return crear_service(session).registrar_consulta(id_turno, id_veterinario, datos)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error