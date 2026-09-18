from datetime import date, datetime

from pydantic import BaseModel


class MascotaAgendaResponse(BaseModel):
    """Datos básicos de la mascota asociada al turno"""

    id: int
    nombre: str
    especie: str


class TurnoAgendaResponse(BaseModel):
    """Información de un turno mostrado en la agenda"""

    id: int
    hora_inicio: str
    duracion_minutos: int
    tipo: str
    mascota: MascotaAgendaResponse
    propietario: str
    estado: str
    estado_visual: str
    agendado_por_administracion: bool


class ResumenAgendaResponse(BaseModel):
    """Cantidad de turnos agrupados por su situación"""

    total: int
    atendidos: int
    en_curso: int
    pendientes: int


class AgendaResponse(BaseModel):
    """Respuesta completa de la agenda diaria del veterinario"""

    fecha: date
    consultado_el: datetime
    resumen: ResumenAgendaResponse
    hay_cambios: bool
    turnos: list[TurnoAgendaResponse]