import { apiFetch } from './client'

export function login(correo, contrasena) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ correo, contrasena }),
  })
}

export function obtenerUsuarioActual(token) {
  return apiFetch('/auth/me', { token })
}
