import { apiFetch } from './client'

export function listarTiposAtencion(token) {
  return apiFetch('/tipos-atencion', { token })
}

export function listarVeterinarios(token) {
  return apiFetch('/veterinarios', { token })
}
