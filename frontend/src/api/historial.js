import { apiFetch } from './client'

export function obtenerMascota(token, idMascota, signal = undefined) {
  return apiFetch(`/mascotas/${idMascota}`, { token, signal })
}

export function obtenerHistorial(
  token,
  idMascota,
  { limite, offset, tipo } = {},
  signal = undefined,
) {
  const parametros = new URLSearchParams()

  if (limite != null) parametros.set('limite', limite)
  if (offset != null) parametros.set('offset', offset)
  if (tipo) parametros.set('tipo', tipo)

  const query = parametros.toString()

  return apiFetch(`/mascotas/${idMascota}/historial${query ? `?${query}` : ''}`, {
    token,
    signal,
  })
}
