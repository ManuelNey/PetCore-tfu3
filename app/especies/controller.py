from fastapi import APIRouter, Depends

from app.database import get_session
from app.Middleware.middleware import requerir_rol
from app.especies.dto import EspecieResponse
from app.especies.repository import EspecieRepository
from app.especies.service import EspecieService


router = APIRouter(
    prefix="/especies",
    tags=["Especies"],
)


def crear_service(session):
    repository = EspecieRepository(session)

    return EspecieService(repository)


@router.get("", response_model=list[EspecieResponse])
def listar_especies(
    session=Depends(get_session),
    _usuario: dict = Depends(requerir_rol("CLIENTE")),
):
    service = crear_service(session)

    return service.listar_activas()
