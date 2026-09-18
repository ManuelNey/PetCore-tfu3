import { apiFetch } from './client'

export function listarEspecies(token) {
  return apiFetch('/especies', { token })
}
