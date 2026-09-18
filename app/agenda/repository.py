from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


class AgendaRepository:
    """Realiza las consultas SQL necesarias para la agenda"""

    def __init__(self, session: Session) -> None:
        """
        Inicializa el repositorio

        Args:
            session: Sesion de base de datos proporcionada por FastAPI
        """
        self.session: Session = session

    def listar_turnos_del_dia(
        self,
        id_veterinario: int,
        inicio: datetime,
        fin: datetime,
    ) -> list:
        """
        Busca los turnos no cancelados de un veterinario

        Args:
            id_veterinario: Identificador del veterinario autenticado
            inicio: Comienzo del dia consultado
            fin: Comienzo del dia siguiente

        Returns:
            Lista de turnos ordenados por su hora de inicio
        """
        consulta = text(
            """
            SELECT
                t.id_turno AS id,
                t.fecha_hora_inicio,
                t.fecha_hora_fin,
                t.duracion_minutos,
                t.estado,
                ta.nombre AS tipo,
                m.id_mascota AS mascota_id,
                m.nombre AS mascota_nombre,
                m.especie AS mascota_especie,
                u.nombre AS propietario_nombre,
                u.apellido AS propietario_apellido,
                (a.id_usuario IS NOT NULL)
                    AS agendado_por_administracion
            FROM turno t
            JOIN tipo_atencion ta
                ON ta.id_tipo_atencion = t.id_tipo_atencion
            JOIN mascota m
                ON m.id_mascota = t.id_mascota
            JOIN usuario u
                ON u.id_usuario = m.id_cliente
            LEFT JOIN administrador a
                ON a.id_usuario = t.id_usuario_creador
            WHERE t.id_veterinario = :id_veterinario
              AND t.fecha_hora_inicio >= :inicio
              AND t.fecha_hora_inicio < :fin
              AND t.estado <> 'CANCELADO'
            ORDER BY t.fecha_hora_inicio
            """
        )

        parametros = {
            "id_veterinario": id_veterinario,
            "inicio": inicio,
            "fin": fin,
        }

        return self.session.execute(
            consulta,
            parametros,
        ).mappings().all()

    def hubo_cambios_desde(
        self,
        id_veterinario: int,
        inicio: datetime,
        fin: datetime,
        desde: datetime,
    ) -> bool:
        """
        Comprueba si la agenda cambió desde un momento determinado

        Args:
            id_veterinario: Identificador del veterinario autenticado
            inicio: Comienzo del dia consultado
            fin: Comienzo del dia siguiente
            desde: Momento de la consulta anterior

        Returns:
            True si se creó o modificó algún turno; de lo contrario, False
        """
        consulta = text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM turno
                WHERE id_veterinario = :id_veterinario
                  AND fecha_hora_inicio >= :inicio
                  AND fecha_hora_inicio < :fin
                  AND (
                      fecha_creacion > :desde
                      OR fecha_modificacion > :desde
                  )
            )
            """
        )

        parametros = {
            "id_veterinario": id_veterinario,
            "inicio": inicio,
            "fin": fin,
            "desde": desde,
        }

        resultado = self.session.execute(
            consulta,
            parametros,
        ).scalar()

        return bool(resultado)