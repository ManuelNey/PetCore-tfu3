from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.turnos.dto import ConsultaCreate, TurnoCreate
from app.turnos.excepciones import TurnoEnPasadoError
from app.turnos.repository import TurnoRepository

# La hora que elige el cliente es hora local de la clínica (igual que en
# AgendaService y DisponibilidadService).
ZONA_CLINICA = ZoneInfo("America/Montevideo")


class TurnoService:
    def __init__(self, repository: TurnoRepository) -> None:
        self.repository: TurnoRepository = repository

    def _a_dict(self, fila) -> dict:
        from datetime import datetime, timezone

        puede_cancelar = (
            fila["estado"] == "CONFIRMADO"
            and fila["fecha_hora_inicio"] > datetime.now(timezone.utc)
        )

        return {
            "id_turno": fila["id_turno"],
            "fecha_hora_inicio": fila["fecha_hora_inicio"],
            "duracion_minutos": fila["duracion_minutos"],
            "tipo": fila["tipo"],
            "estado": fila["estado"],
            "canal_origen": fila["canal_origen"],
            "veterinario": fila["veterinario"],
            "puede_cancelar": puede_cancelar,
            "mascota": {
                "id_mascota": fila["id_mascota"],
                "nombre": fila["mascota_nombre"],
                "especie": fila["especie"],
                "estado": fila["mascota_estado"],
            },
        }

    def listar_por_cliente(self, id_cliente: int, periodo: str) -> list[dict]:
        filas = self.repository.listar_por_cliente(id_cliente, periodo)
        return [self._a_dict(f) for f in filas]

    def obtener_por_id(self, id_turno: int, id_cliente: int) -> dict:
        fila = self.repository.obtener_por_id(id_turno, id_cliente)
        if not fila:
            raise LookupError("Turno no encontrado.")
        return self._a_dict(fila)

    def cancelar(self, id_turno: int, id_cliente: int) -> None:
        resultado = self.repository.cancelar(id_turno, id_cliente)
        if not resultado:
            raise ValueError(
                "No se pudo cancelar: el turno no existe, ya fue "
                "cancelado, o falta menos de 1 hora para su inicio."
            )

    def crear(self, id_cliente: int, datos: TurnoCreate) -> dict:
        """
        Reserva un turno para el cliente autenticado.

        Valida que la mascota sea del cliente, que el tipo de atención esté
        activo y sea reservable por un cliente, y que el veterinario esté
        activo. La superposición de horarios la valida la base de datos
        (restricción `no_superposicion`); si otro turno ya tomó ese horario,
        `TurnoRepository.crear_turno` levanta HorarioNoDisponibleError.
        """
        if datos.hora_inicio.minute % 15 != 0 or datos.hora_inicio.second != 0:
            raise ValueError("El horario debe ser un múltiplo de 15 minutos.")

        mascota = self.repository.obtener_mascota_cliente(datos.id_mascota, id_cliente)
        if mascota is None:
            raise LookupError("Mascota no encontrada.")

        tipo_atencion = self.repository.obtener_tipo_atencion_reservable(datos.id_tipo_atencion)
        if tipo_atencion is None:
            raise LookupError("Tipo de atención no encontrado.")

        veterinario = self.repository.obtener_veterinario_activo(datos.id_veterinario)
        if veterinario is None:
            raise LookupError("Veterinario no encontrado.")

        duracion = tipo_atencion["duracion_minutos"]
        fecha_hora_inicio = datetime.combine(
            datos.fecha, datos.hora_inicio, tzinfo=ZONA_CLINICA
        )
        fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=duracion)

        ahora = datetime.now(timezone.utc)
        if fecha_hora_inicio <= ahora:
            raise TurnoEnPasadoError("No se puede reservar un turno en un horario que ya pasó.")

        id_turno = self.repository.crear_turno(
            id_mascota=datos.id_mascota,
            id_veterinario=datos.id_veterinario,
            id_tipo_atencion=datos.id_tipo_atencion,
            id_usuario_creador=id_cliente,
            fecha_hora_inicio=fecha_hora_inicio,
            fecha_hora_fin=fecha_hora_fin,
            duracion_minutos=duracion,
        )

        return self._a_dict(self.repository.obtener_por_id(id_turno, id_cliente))

    def registrar_consulta(self, id_turno: int, id_veterinario: int, datos: ConsultaCreate) -> dict:
        """
        Registra la atención de un turno CONFIRMADO del veterinario autenticado.

        Guarda la consulta clínica y pasa el turno a ATENDIDO en la misma
        transacción (ver TurnoRepository.registrar_consulta).
        """
        motivo = datos.motivo.strip()
        diagnostico = datos.diagnostico.strip()

        if motivo == "":
            raise ValueError("El motivo de la consulta no puede estar vacío.")

        if diagnostico == "":
            raise ValueError("El diagnóstico de la consulta no puede estar vacío.")

        consulta = self.repository.registrar_consulta(
            id_turno=id_turno,
            id_veterinario=id_veterinario,
            datos={
                "motivo": motivo,
                "diagnostico": diagnostico,
                "observaciones": datos.observaciones,
                "tratamiento": datos.tratamiento,
                "recomendaciones": datos.recomendaciones,
            },
        )

        if consulta is None:
            raise LookupError(
                "El turno no existe, no es tuyo, o no está confirmado para registrar la consulta."
            )

        return {
            "id_consulta": consulta["id_consulta"],
            "fecha_registro": consulta["fecha_registro"],
            "edicion_vence_el": consulta["fecha_registro"] + timedelta(hours=24),
            "turno_estado": "ATENDIDO",
        }