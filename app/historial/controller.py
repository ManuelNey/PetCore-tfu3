from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.historial.dto import HistorialClienteResponse, HistorialVeterinarioResponse
from app.historial.repository import HistorialRepository
from app.historial.service import HistorialService
from app.Middleware.middleware import obtener_usuario_actual

router = APIRouter(tags=["Historial"])


def crear_service(session: Session) -> HistorialService:
    return HistorialService(HistorialRepository(session))


@router.get(
    "/mascotas/{id_mascota}/historial",
    response_model=HistorialClienteResponse | HistorialVeterinarioResponse,
)
def ver_historial(
    id_mascota: int,
    limite: int = 10,
    offset: int = 0,
    tipo: str | None = None,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    session: Session = Depends(get_session),
):
    service = crear_service(session)

    try:
        if usuario["rol"] == "VETERINARIO":
            return service.obtener_historial_veterinario(id_mascota, usuario["id_usuario"], tipo)

        if usuario["rol"] == "CLIENTE":
            return service.obtener_historial_cliente(
                id_mascota, usuario["id_usuario"], limite, offset
            )

        # ADMINISTRADOR u otro rol: sin acceso al contenido clínico.
        HistorialRepository(session).registrar_acceso(
            usuario["id_usuario"], id_mascota, usuario["rol"], "RECHAZADO",
            "Rol sin acceso al historial clinico.",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol sin acceso a este recurso.",
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error