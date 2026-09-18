from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.agenda.repository import AgendaRepository


ZONA_CLINICA = ZoneInfo("America/Montevideo")


class AgendaService:
    """Contiene las reglas necesarias para construir la agenda."""

    def __init__(self, repository: AgendaRepository) -> None:
        """
        Inicializa el servicio

        Args:
            repository: Repositorio utilizado para consultar los turnos
        """
        self.repository: AgendaRepository = repository

    def obtener_agenda(
        self,
        id_veterinario: int,
        fecha_solicitada: date | None,
        desde: datetime | None,
    ) -> dict:
        """
        Construye la agenda diaria del veterinario autenticado

        Args:
            id_veterinario: Identificador del veterinario
            fecha_solicitada: Día solicitado o None para utilizar hoy
            desde: Momento de la consulta anterior

        Returns:
            Agenda con resumen, turnos y detección de cambios
        """
        ahora = datetime.now(timezone.utc)

        if fecha_solicitada is None:
            fecha_agenda = datetime.now(
                ZONA_CLINICA
            ).date()
        else:
            fecha_agenda = fecha_solicitada

        inicio_dia = datetime.combine(
            fecha_agenda,
            time.min,
            tzinfo=ZONA_CLINICA,
        )
        fin_dia = inicio_dia + timedelta(days=1)

        filas = self.repository.listar_turnos_del_dia(
            id_veterinario=id_veterinario,
            inicio=inicio_dia,
            fin=fin_dia,
        )

        turnos = []

        for fila in filas:
            estado_visual = self._calcular_estado_visual(
                estado=fila["estado"],
                inicio=fila["fecha_hora_inicio"],
                fin=fila["fecha_hora_fin"],
                ahora=ahora,
            )

            propietario = self._formatear_propietario(
                nombre=fila["propietario_nombre"],
                apellido=fila["propietario_apellido"],
            )

            turno = {
                "id": fila["id"],
                "hora_inicio": fila[
                    "fecha_hora_inicio"
                ].astimezone(
                    ZONA_CLINICA
                ).strftime("%H:%M"),
                "duracion_minutos": fila[
                    "duracion_minutos"
                ],
                "tipo": fila["tipo"],
                "mascota": {
                    "id": fila["mascota_id"],
                    "nombre": fila["mascota_nombre"],
                    "especie": fila["mascota_especie"],
                },
                "propietario": propietario,
                "estado": fila["estado"],
                "estado_visual": estado_visual,
                "agendado_por_administracion": fila[
                    "agendado_por_administracion"
                ],
            }

            turnos.append(turno)

        total = len(turnos)

        atendidos = sum(
            turno["estado_visual"] == "ATENDIDO"
            for turno in turnos
        )

        en_curso = sum(
            turno["estado_visual"] == "EN_CURSO"
            for turno in turnos
        )

        pendientes = total - atendidos - en_curso

        hay_cambios = False

        if desde is not None:
            if desde.tzinfo is None:
                desde = desde.replace(
                    tzinfo=ZONA_CLINICA
                )

            hay_cambios = (
                self.repository.hubo_cambios_desde(
                    id_veterinario=id_veterinario,
                    inicio=inicio_dia,
                    fin=fin_dia,
                    desde=desde,
                )
            )

        return {
            "fecha": fecha_agenda,
            "consultado_el": ahora,
            "resumen": {
                "total": total,
                "atendidos": atendidos,
                "en_curso": en_curso,
                "pendientes": pendientes,
            },
            "hay_cambios": hay_cambios,
            "turnos": turnos,
        }

    def _calcular_estado_visual(
        self,
        estado: str,
        inicio: datetime,
        fin: datetime,
        ahora: datetime,
    ) -> str:
        """
        Calcula el estado que debe mostrar la agenda

        Args:
            estado: Estado guardado en PostgreSQL
            inicio: Inicio del turno
            fin: Final del turno
            ahora: Momento actual del servidor

        Returns:
            EN_CURSO si el turno confirmado está transcurriendo;
            de lo contrario, devuelve el estado guardado
        """
        if (
            estado == "CONFIRMADO"
            and inicio <= ahora < fin
        ):
            return "EN_CURSO"

        return estado

    def _formatear_propietario(
        self,
        nombre: str,
        apellido: str,
    ) -> str:
        """
        Construye el nombre abreviado del propietario

        Args:
            nombre: Nombre del propietario
            apellido: Apellido del propietario

        Returns:
            Nombre abreviado, por ejemplo: A. Gimenez.
        """
        inicial = nombre[0]

        return f"{inicial}. {apellido}"