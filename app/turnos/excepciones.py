class HorarioNoDisponibleError(Exception):
    """Otro cliente reservó el mismo horario antes; Postgres lo rechazó con 23P01."""


class TurnoEnPasadoError(Exception):
    """El horario pedido (fecha + hora_inicio) ya pasó."""
