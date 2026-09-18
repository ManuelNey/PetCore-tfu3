import asyncio
import logging

from sqlmodel import Session, text

from app.database import engine

logger = logging.getLogger(__name__)

INTERVALO_SEGUNDOS = 3 * 60 # Cada 3 minutos


def marcar_turnos_no_asistidos() -> int:
    """
    Pasa a NO_ASISTIO los turnos CONFIRMADO cuya hora de fin ya pasó sin
    que el veterinario haya registrado la consulta.

    Return:
        Cantidad de turnos actualizados.
    """
    with Session(engine) as session:
        resultado = session.execute(
            text(
                """
                UPDATE turno
                SET estado = 'NO_ASISTIO'
                WHERE estado = 'CONFIRMADO'
                AND fecha_hora_fin < now()
                RETURNING id_turno
                """
            )
        )
        ids_actualizados = resultado.all()
        session.commit()

        return len(ids_actualizados)


async def ejecutar_tarea_periodica() -> None:
    """
    Corre en segundo plano mientras la API esté activa y reintenta cada
    `INTERVALO_SEGUNDOS`, incluso si una corrida falla.
    """
    while True:
        try:
            cantidad = await asyncio.to_thread(marcar_turnos_no_asistidos)

            if cantidad:
                logger.info(
                    "Se marcaron %s turno(s) como NO_ASISTIO.", cantidad
                )
        except Exception:
            logger.exception(
                "Error al marcar turnos vencidos como NO_ASISTIO."
            )

        await asyncio.sleep(INTERVALO_SEGUNDOS)
