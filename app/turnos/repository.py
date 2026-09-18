from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.turnos.excepciones import HorarioNoDisponibleError

# Código SQLSTATE de Postgres para la violación de la restricción de
# exclusión `no_superposicion` (dos turnos que se pisan en la agenda).
SQLSTATE_EXCLUSION_VIOLATION = "23P01"


class TurnoRepository:
    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def obtener_mascota_cliente(self, id_mascota: int, id_cliente: int):
        """Mascota activa del cliente, para validar que puede reservarle un turno."""
        consulta = text(
            """
            SELECT id_mascota
            FROM mascota
            WHERE id_mascota = :id_mascota
              AND id_cliente = :id_cliente
              AND estado = 'ACTIVA'
            """
        )
        return self.session.execute(
            consulta, {"id_mascota": id_mascota, "id_cliente": id_cliente}
        ).mappings().first()

    def obtener_tipo_atencion_reservable(self, id_tipo_atencion: int):
        """Tipo de atención activo y reservable por el cliente (no por teléfono/presencial)."""
        consulta = text(
            """
            SELECT id_tipo_atencion, duracion_minutos
            FROM tipo_atencion
            WHERE id_tipo_atencion = :id_tipo_atencion
              AND estado = 'ACTIVO'
              AND reservable_cliente = TRUE
            """
        )
        return self.session.execute(
            consulta, {"id_tipo_atencion": id_tipo_atencion}
        ).mappings().first()

    def obtener_veterinario_activo(self, id_veterinario: int):
        consulta = text(
            """
            SELECT u.id_usuario
            FROM veterinario v
            JOIN usuario u ON u.id_usuario = v.id_usuario
            WHERE v.id_usuario = :id_veterinario
              AND u.estado = 'ACTIVO'
            """
        )
        return self.session.execute(
            consulta, {"id_veterinario": id_veterinario}
        ).mappings().first()

    def crear_turno(
        self,
        id_mascota: int,
        id_veterinario: int,
        id_tipo_atencion: int,
        id_usuario_creador: int,
        fecha_hora_inicio: datetime,
        fecha_hora_fin: datetime,
        duracion_minutos: int,
    ) -> int:
        """
        Inserta el turno como CONFIRMADO/AUTOGESTION. Si se pisa con otro turno
        ya reservado, Postgres rechaza el INSERT con 23P01 (exclusion_violation)
        por la restricción `no_superposicion`; acá se traduce a
        HorarioNoDisponibleError para que el controller arme el 409.
        """
        consulta = text(
            """
            INSERT INTO turno (
                id_mascota, id_veterinario, id_tipo_atencion, id_usuario_creador,
                fecha_hora_inicio, fecha_hora_fin, duracion_minutos, canal_origen
            )
            VALUES (
                :id_mascota, :id_veterinario, :id_tipo_atencion, :id_usuario_creador,
                :fecha_hora_inicio, :fecha_hora_fin, :duracion_minutos, 'AUTOGESTION'
            )
            RETURNING id_turno
            """
        )

        valores = {
            "id_mascota": id_mascota,
            "id_veterinario": id_veterinario,
            "id_tipo_atencion": id_tipo_atencion,
            "id_usuario_creador": id_usuario_creador,
            "fecha_hora_inicio": fecha_hora_inicio,
            "fecha_hora_fin": fecha_hora_fin,
            "duracion_minutos": duracion_minutos,
        }

        try:
            fila = self.session.execute(consulta, valores).mappings().one()
            self.session.commit()
            return fila["id_turno"]
        except IntegrityError as error:
            self.session.rollback()
            codigo_error = getattr(getattr(error, "orig", None), "sqlstate", None)
            if codigo_error == SQLSTATE_EXCLUSION_VIOLATION:
                raise HorarioNoDisponibleError() from error
            raise

    def listar_por_cliente(self, id_cliente: int, periodo: str) -> list:
        condicion_periodo = {
            "proximos": "AND t.fecha_hora_inicio >= now()",
            "pasados": "AND t.fecha_hora_inicio < now()",
            "todos": "",
        }[periodo]

        consulta = text(
            f"""
            SELECT
                t.id_turno, t.fecha_hora_inicio, t.duracion_minutos,
                t.estado, t.canal_origen,
                ta.nombre AS tipo,
                m.id_mascota, m.nombre AS mascota_nombre,
                m.especie, m.estado AS mascota_estado,
                u.nombre || ' ' || u.apellido AS veterinario
            FROM turno t
            JOIN mascota m ON m.id_mascota = t.id_mascota
            JOIN tipo_atencion ta ON ta.id_tipo_atencion = t.id_tipo_atencion
            JOIN usuario u ON u.id_usuario = t.id_veterinario
            WHERE m.id_cliente = :id_cliente
            {condicion_periodo}
            ORDER BY t.fecha_hora_inicio DESC
            """
        )
        return self.session.execute(consulta, {"id_cliente": id_cliente}).mappings().all()

    def obtener_por_id(self, id_turno: int, id_cliente: int):
        consulta = text(
            """
            SELECT
                t.id_turno, t.fecha_hora_inicio, t.duracion_minutos,
                t.estado, t.canal_origen,
                ta.nombre AS tipo,
                m.id_mascota, m.nombre AS mascota_nombre,
                m.especie, m.estado AS mascota_estado,
                u.nombre || ' ' || u.apellido AS veterinario
            FROM turno t
            JOIN mascota m ON m.id_mascota = t.id_mascota
            JOIN tipo_atencion ta ON ta.id_tipo_atencion = t.id_tipo_atencion
            JOIN usuario u ON u.id_usuario = t.id_veterinario
            WHERE t.id_turno = :id_turno AND m.id_cliente = :id_cliente
            """
        )
        return self.session.execute(
            consulta, {"id_turno": id_turno, "id_cliente": id_cliente}
        ).mappings().first()

    def cancelar(self, id_turno: int, id_cliente: int):
        consulta = text(
            """
            UPDATE turno t
            SET estado = 'CANCELADO',
                id_usuario_modificador = :id_cliente,
                fecha_modificacion = CURRENT_TIMESTAMP
            FROM mascota m
            WHERE t.id_mascota = m.id_mascota
              AND t.id_turno = :id_turno
              AND m.id_cliente = :id_cliente
              AND t.estado = 'CONFIRMADO'
              AND t.fecha_hora_inicio > now() + interval '1 hour'
            RETURNING t.id_turno
            """
        )
        resultado = self.session.execute(
            consulta, {"id_turno": id_turno, "id_cliente": id_cliente}
        ).mappings().first()
        self.session.commit()
        return resultado

    def registrar_consulta(
        self,
        id_turno: int,
        id_veterinario: int,
        datos: dict,
    ) -> dict | None:
        # Verifica que el turno sea del veterinario y esté CONFIRMADO
        verificacion = text(
            """
            SELECT id_turno, id_mascota FROM turno
            WHERE id_turno = :id_turno
            AND id_veterinario = :id_veterinario
            AND estado = 'CONFIRMADO'
            """
        )
        turno = self.session.execute(
            verificacion,
            {"id_turno": id_turno, "id_veterinario": id_veterinario},
        ).mappings().first()

        if not turno:
            return None

        insertar_consulta = text(
            """
            INSERT INTO consulta_clinica (
                id_turno, id_mascota, id_veterinario,
                motivo, diagnostico, observaciones, tratamiento, recomendaciones
            )
            VALUES (
                :id_turno, :id_mascota, :id_veterinario,
                :motivo, :diagnostico, :observaciones, :tratamiento, :recomendaciones
            )
            RETURNING id_consulta, fecha_registro
            """
        )
        consulta_creada = self.session.execute(
            insertar_consulta,
            {
                "id_turno": id_turno,
                "id_mascota": turno["id_mascota"],
                "id_veterinario": id_veterinario,
                **datos,
            },
        ).mappings().first()

        actualizar_turno = text(
            "UPDATE turno SET estado = 'ATENDIDO' WHERE id_turno = :id_turno"
        )
        self.session.execute(actualizar_turno, {"id_turno": id_turno})

        self.session.commit()
        return dict(consulta_creada)