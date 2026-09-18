from datetime import date, datetime

from pydantic import BaseModel


class SlotDisponibilidad(BaseModel):
    """Un horario de 15 min: si está libre, y si no, por qué (motivo)."""

    inicio: str
    disponible: bool
    motivo: str | None = None


class DisponibilidadResponse(BaseModel):
    """Respuesta de GET /disponibilidad: grilla completa de un día para un veterinario."""

    fecha: date
    duracion_requerida: int
    calculado_el: datetime
    slots: list[SlotDisponibilidad]
