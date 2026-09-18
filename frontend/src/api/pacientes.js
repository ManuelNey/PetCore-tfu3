import { apiFetch } from './client'

export function listarPacientes(token, { q, alcance = 'clinica', especie } = {}, signal = undefined) {
  const parametros = new URLSearchParams({ alcance })

  if (q) parametros.set('q', q)
  if (especie) parametros.set('especie', especie)

  return apiFetch(`/pacientes?${parametros.toString()}`, { token, signal })
}
