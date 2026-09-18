from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.disponibilidad.repository import DisponibilidadRepository

INTERVALO_MINUTOS = 15

# Los bloques de disponibilidad y los horarios de turno se definen en hora
# local de la clínica (ver AgendaService, que usa la misma zona para mostrar
# la agenda del veterinario).
ZONA_CLINICA = ZoneInfo("America/Montevideo")

# Ventana de la agenda de la clínica (ver Agenda diaria del veterinario).
HORA_INICIO_CLINICA = time(8, 0)
HORA_FIN_CLINICA = time(18, 0)


class DisponibilidadService:
    def __init__(self, repository: DisponibilidadRepository) -> None:
        self.repository: DisponibilidadRepository = repository

    def calcular(self, id_veterinario: int, fecha: date, id_tipo_atencion: int) -> dict:
        """
        Arma la grilla de horarios de un veterinario para una fecha.

        Junta la disponibilidad recurrente (por día de semana), le resta las
        excepciones puntuales de esa fecha y los turnos ya ocupados, y genera
        slots de 15 min entre HORA_INICIO_CLINICA y HORA_FIN_CLINICA con el
        motivo de no disponibilidad cuando corresponde.
        """
        tipo_atencion = self.repository.obtener_tipo_atencion(id_tipo_atencion)
        if tipo_atencion is None:
            raise LookupError("Tipo de atención no encontrado.")

        duracion = tipo_atencion["duracion_minutos"]

        dia_semana = fecha.isoweekday()
        bloques = [
            (fila["hora_inicio"], fila["hora_fin"])
            for fila in self.repository.obtener_bloques(id_veterinario, dia_semana)
        ]

        excepciones_filas = self.repository.obtener_excepciones(id_veterinario, fecha)

        # Una ausencia de día completo (horas nulas) invalida toda la agenda del día.
        if any(fila["hora_inicio"] is None for fila in excepciones_filas):
            bloques = []

        excepciones = [
            (fila["hora_inicio"], fila["hora_fin"])
            for fila in excepciones_filas
            if fila["hora_inicio"] is not None
        ]

        # fecha_hora_inicio/fin vienen de PostgreSQL en UTC real (timestamptz).
        # Sin el astimezone(), .time() devolvía la hora UTC cruda y comparaba
        # un turno de las 09:30 locales contra el slot de las 12:30.
        ocupados = [
            (
                fila["fecha_hora_inicio"].astimezone(ZONA_CLINICA).time(),
                fila["fecha_hora_fin"].astimezone(ZONA_CLINICA).time(),
            )
            for fila in self.repository.obtener_turnos_ocupados(id_veterinario, fecha)
        ]

        # Los bloques (09:00-13:00, etc.) están en hora local de la clínica.
        # Compararlos contra datetime.now(timezone.utc) corría el reloj 3
        # horas para adelante (Montevideo es UTC-3) y dejaba todo el día
        # marcado como FUERA_DE_AGENDA aunque todavía quedara agenda libre.
        ahora_local = datetime.now(ZONA_CLINICA)
        # Si la fecha consultada es hoy, los slots que ya pasaron no se pueden
        # reservar aunque el resto de la agenda los deje libres.
        hora_limite = ahora_local.time() if fecha == ahora_local.date() else None

        slots = self._generar_slots(bloques, excepciones, ocupados, duracion, hora_limite)

        return {
            "fecha": fecha,
            "duracion_requerida": duracion,
            "calculado_el": datetime.now(timezone.utc),
            "slots": slots,
        }

    def _generar_slots(
        self,
        bloques: list[tuple[time, time]],
        excepciones: list[tuple[time, time]],
        ocupados: list[tuple[time, time]],
        duracion: int,
        hora_limite: time | None,
    ) -> list[dict]:
        """
        Recorre la ventana de la clínica slot por slot (cada 15 min) y decide
        el estado de cada uno:
          - FUERA_DE_AGENDA: el slot no cae dentro de ningún bloque de
            disponibilidad del veterinario, cae en una excepción (ausencia),
            o ya pasó (solo aplica si se está consultando el día de hoy).
          - OCUPADO: el slot se pisa con un turno ya reservado.
          - HUECO_INSUFICIENTE: el slot está libre pero no queda tiempo
            contiguo suficiente para la duración pedida.
          - disponible: el slot y toda la duración requerida están libres.
        """
        slots: list[dict] = []
        actual = HORA_INICIO_CLINICA

        while actual < HORA_FIN_CLINICA:
            fin_slot = self._sumar_minutos(actual, INTERVALO_MINUTOS)

            if hora_limite is not None and actual <= hora_limite:
                slots.append(self._slot(actual, False, "FUERA_DE_AGENDA"))
                actual = fin_slot
                continue

            bloque = next(
                (b for b in bloques if b[0] <= actual and fin_slot <= b[1]),
                None,
            )

            if bloque is None:
                slots.append(self._slot(actual, False, "FUERA_DE_AGENDA"))
                actual = fin_slot
                continue

            if any(self._solapa(actual, fin_slot, *e) for e in excepciones):
                slots.append(self._slot(actual, False, "FUERA_DE_AGENDA"))
                actual = fin_slot
                continue

            if any(self._solapa(actual, fin_slot, *o) for o in ocupados):
                slots.append(self._slot(actual, False, "OCUPADO"))
                actual = fin_slot
                continue

            fin_requerido = self._sumar_minutos(actual, duracion)
            cabe = (
                fin_requerido <= bloque[1]
                and not any(self._solapa(actual, fin_requerido, *e) for e in excepciones)
                and not any(self._solapa(actual, fin_requerido, *o) for o in ocupados)
            )

            if cabe:
                slots.append(self._slot(actual, True))
            else:
                slots.append(self._slot(actual, False, "HUECO_INSUFICIENTE"))

            actual = fin_slot

        return slots

    @staticmethod
    def _slot(inicio: time, disponible: bool, motivo: str | None = None) -> dict:
        return {
            "inicio": inicio.strftime("%H:%M"),
            "disponible": disponible,
            "motivo": motivo,
        }

    @staticmethod
    def _solapa(inicio_a: time, fin_a: time, inicio_b: time, fin_b: time) -> bool:
        return inicio_a < fin_b and inicio_b < fin_a

    @staticmethod
    def _sumar_minutos(hora: time, minutos: int) -> time:
        return (
            datetime.combine(date.min, hora) + timedelta(minutes=minutos)
        ).time()
