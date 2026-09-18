import { apiFetch } from './client'

export function listarMascotas(token) {
  return apiFetch('/mascotas', { token })
}
