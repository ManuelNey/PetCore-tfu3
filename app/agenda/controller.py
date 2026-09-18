from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agenda.dto import AgendaResponse
from app.agenda.repository import AgendaRepository
from app.agenda.service import AgendaService
from app.database import get_session
from app.Middleware.middleware import requerir_rol


router = APIRouter(
    prefix="/agenda",
    tags=["Agenda"],
)


def crear_service(
    session: Session,
) -> AgendaService:
    """
    Crea el servicio necesario para consultar la agenda

    Args:
        session: Sesion de base de datos proporcionada por FastAPI

    Returns:
        Servicio de agenda configurado
    """
    repository = AgendaRepository(session)

    return AgendaService(repository)


@router.get(
    "",
    response_model=AgendaResponse,
)
def obtener_agenda(
    fecha: date | None = None,
    desde: datetime | None = None,
    usuario: dict[str, Any] = Depends(
        requerir_rol("VETERINARIO")
    ),
    session: Session = Depends(get_session),
) -> dict:
    """
    Devuelve la agenda diaria del veterinario autenticado

    - fecha: día que se desea consultar en formato `AAAA-MM-DD`
      Si no se proporciona, se utiliza el día actual
    - desde: fecha y hora de la consulta anterior
      Se utiliza para indicar si la agenda cambió.
    - No incluye turnos cancelados
    - Calcula si un turno se encuentra actualmente en curso
    - Solamente puede utilizarlo un usuario con rol veterinario
    """
    id_veterinario = usuario["id_usuario"]

    service = crear_service(session)

    return service.obtener_agenda(
        id_veterinario=id_veterinario,
        fecha_solicitada=fecha,
        desde=desde,
    )