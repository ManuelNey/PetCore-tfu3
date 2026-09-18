import { apiFetch } from './client'

export function obtenerAgenda(token, fecha, desde = null, signal = undefined) {
  const parametros = new URLSearchParams({ fecha })

  if (desde) {
    parametros.set('desde', desde)
  }

  return apiFetch(`/agenda?${parametros.toString()}`, {
    token,
    signal,
  })
}
