from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.Middleware.middleware import requerir_rol
from app.disponibilidad.dto import DisponibilidadResponse
from app.disponibilidad.repository import DisponibilidadRepository
from app.disponibilidad.service import DisponibilidadService

router = APIRouter(prefix="/disponibilidad", tags=["Disponibilidad"])


def crear_service(session: Session) -> DisponibilidadService:
    """Arma el servicio de disponibilidad con su repositorio."""
    repository: DisponibilidadRepository = DisponibilidadRepository(session)
    return DisponibilidadService(repository)


@router.get("", response_model=DisponibilidadResponse, response_model_exclude_none=True)
def obtener_disponibilidad(
    veterinario: int = Query(...),
    fecha: date = Query(...),
    tipo_atencion: int = Query(...),
    _usuario: dict[str, Any] = Depends(requerir_rol("CLIENTE", "ADMINISTRADOR")),
    session: Session = Depends(get_session),
) -> dict:
    """
    Grilla de horarios de un veterinario para una fecha y un tipo de atención.

    Usada en el paso 4 de "Reservar turno" (cliente) y en el panel de
    turnos por teléfono (administrador). `response_model_exclude_none`
    hace que el campo `motivo` no aparezca en los slots disponibles.
    """
    try:
        return crear_service(session).calcular(veterinario, fecha, tipo_atencion)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
