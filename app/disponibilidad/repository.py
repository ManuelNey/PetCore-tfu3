from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


class DisponibilidadRepository:
    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def obtener_tipo_atencion(self, id_tipo_atencion: int):
        """Trae la duración (en minutos) del tipo de atención, si está activo."""
        consulta = text(
            """
            SELECT id_tipo_atencion, duracion_minutos
            FROM tipo_atencion
            WHERE id_tipo_atencion = :id_tipo_atencion
              AND estado = 'ACTIVO'
            """
        )
        return self.session.execute(
            consulta, {"id_tipo_atencion": id_tipo_atencion}
        ).mappings().first()

    def obtener_bloques(self, id_veterinario: int, dia_semana: int):
        """Franjas recurrentes activas del veterinario para ese día de la semana."""
        consulta = text(
            """
            SELECT hora_inicio, hora_fin
            FROM disponibilidad
            WHERE id_veterinario = :id_veterinario
              AND dia_semana = :dia_semana
              AND estado = 'ACTIVA'
            ORDER BY hora_inicio
            """
        )
        return self.session.execute(
            consulta,
            {"id_veterinario": id_veterinario, "dia_semana": dia_semana},
        ).mappings().all()

    def obtener_excepciones(self, id_veterinario: int, fecha: date):
        """Ausencias puntuales del veterinario en esa fecha (día completo o franja parcial)."""
        consulta = text(
            """
            SELECT hora_inicio, hora_fin
            FROM excepcion_disponibilidad
            WHERE id_veterinario = :id_veterinario
              AND fecha = :fecha
            """
        )
        return self.session.execute(
            consulta, {"id_veterinario": id_veterinario, "fecha": fecha}
        ).mappings().all()

    def obtener_turnos_ocupados(self, id_veterinario: int, fecha: date):
        """Turnos ya reservados (CONFIRMADO/ATENDIDO) del veterinario en esa fecha."""
        consulta = text(
            """
            SELECT fecha_hora_inicio, fecha_hora_fin
            FROM turno
            WHERE id_veterinario = :id_veterinario
              AND estado IN ('CONFIRMADO', 'ATENDIDO')
              AND fecha_hora_inicio::date = :fecha
            """
        )
        return self.session.execute(
            consulta, {"id_veterinario": id_veterinario, "fecha": fecha}
        ).mappings().all()
