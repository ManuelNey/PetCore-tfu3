"""
Valet Key: un enlace temporal para descargar un PDF concreto.

El token dice para qué PDF sirve y cuándo vence. Quien lo recibe puede descargar
ese PDF sin iniciar sesión, pero el token no sirve para nada más.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.config import settings

ALGORITMO_JWT = "HS256"
TIPO = "valet_key"
RECURSO = "historial_pdf"


class ValetKeyInvalida(Exception):
    """El token está modificado, es inválido o ya venció"""


class ValetKeyNoCorresponde(Exception):
    """El token es válido, pero es de otro PDF"""


def generar_valet_key(id_tarea: UUID) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "tipo": TIPO,
        "recurso": RECURSO,
        "id_tarea": str(id_tarea),
        "iat": ahora,
        "exp": ahora + timedelta(seconds=settings.VALET_KEY_SEGUNDOS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITMO_JWT)


def validar_valet_key(token: str, id_tarea: UUID) -> None:
    """Revisa que el token no esté modificado, que no haya vencido y que sea de esta tarea."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITMO_JWT],
            options={"require": ["tipo", "recurso", "id_tarea", "exp"]},
        )
    except jwt.ExpiredSignatureError as error:
        raise ValetKeyInvalida("El enlace de descarga venció.") from error
    except jwt.InvalidTokenError as error:
        raise ValetKeyInvalida("El token de descarga no es válido.") from error

    if payload["tipo"] != TIPO or payload["recurso"] != RECURSO:
        raise ValetKeyNoCorresponde("El token no sirve para este recurso.")

    if payload["id_tarea"] != str(id_tarea):
        raise ValetKeyNoCorresponde("El token no corresponde a esta exportación.")
