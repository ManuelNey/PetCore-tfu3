from pydantic import BaseModel, ConfigDict


class PropietarioResumen(BaseModel):
    nombre: str
    telefono: str


class UltimaAtencion(BaseModel):
    fecha: str
    veterinario: str
    fue_propia: bool


class TurnoHoy(BaseModel):
    hora: str
    estado_visual: str


class PacienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    especie: str
    raza: str | None
    edad: str | None
    estado: str
    propietario: PropietarioResumen
    consultas_registradas: int
    ultima_atencion: UltimaAtencion | None
    turno_hoy: TurnoHoy | None