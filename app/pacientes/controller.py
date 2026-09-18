from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.Middleware.middleware import requerir_rol
from app.pacientes.dto import PacienteResponse
from app.pacientes.repository import PacienteRepository
from app.pacientes.service import PacienteService

router = APIRouter(tags=["Pacientes"])


def crear_service(session: Session) -> PacienteService:
    return PacienteService(PacienteRepository(session))


@router.get("/pacientes", response_model=list[PacienteResponse])
def buscar_pacientes(
    q: str | None = None,
    alcance: str = "clinica",
    especie: str | None = None,
    usuario: dict[str, Any] = Depends(requerir_rol("VETERINARIO")),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    service: PacienteService = crear_service(session)

    return service.buscar(
        id_veterinario=usuario["id_usuario"],
        q=q,
        alcance=alcance,
        especie=especie,
    )
