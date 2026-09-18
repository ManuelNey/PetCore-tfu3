import { apiFetch, API_URL } from './client'

export function listarTurnos(token, periodo = 'proximos') {
  return apiFetch(`/turnos?periodo=${periodo}`, { token })
}

export function obtenerTurno(token, idTurno) {
  return apiFetch(`/turnos/${idTurno}`, { token })
}

export function cancelarTurno(token, idTurno) {
  return apiFetch(`/turnos/${idTurno}/cancelar`, { token, method: 'POST' })
}

export function registrarConsulta(token, idTurno, datos) {
  return apiFetch(`/turnos/${idTurno}/consulta`, {
    token,
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function obtenerDisponibilidad(token, { veterinario, fecha, tipoAtencion }) {
  const parametros = new URLSearchParams({
    veterinario,
    fecha,
    tipo_atencion: tipoAtencion,
  })
  return apiFetch(`/disponibilidad?${parametros}`, { token })
}

// No usa apiFetch: el 409 de horario tomado trae un `detail` con objeto
// (seleccion_conservada + disponibilidad_actualizada), no un string, y
// apiFetch solo sabe propagar mensajes de error en texto plano.
export async function crearTurno(token, { idMascota, idTipoAtencion, idVeterinario, fecha, horaInicio }) {
  const respuesta = await fetch(`${API_URL}/turnos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      id_mascota: idMascota,
      id_tipo_atencion: idTipoAtencion,
      id_veterinario: idVeterinario,
      fecha,
      hora_inicio: horaInicio,
    }),
  })

  const datos = await respuesta.json().catch(() => null)

  if (respuesta.status === 409 && datos?.detail?.error === 'HORARIO_NO_DISPONIBLE') {
    const error = new Error(datos.detail.mensaje)
    error.horarioNoDisponible = true
    error.disponibilidadActualizada = datos.detail.disponibilidad_actualizada
    throw error
  }

  if (!respuesta.ok) {
    const mensaje = typeof datos?.detail === 'string' ? datos.detail : 'No se pudo confirmar el turno.'
    throw new Error(mensaje)
  }

  return datos
}
