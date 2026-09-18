import socket

from fastapi import APIRouter, Depends

from app.Middleware.middleware import obtener_usuario_actual


router = APIRouter(prefix="/demo", tags=["Demo"])


@router.get("/instancia")
def obtener_instancia(
    _usuario: dict = Depends(obtener_usuario_actual),
):
    """
    Devuelve el nombre del contenedor que atendió la solicitud.

    Se utiliza para demostrar que existen varias réplicas de la API
    detrás del balanceador.
    """
    return {
        "instancia": socket.gethostname()
    }
