export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Wrapper simple sobre fetch: arma la URL, manda JSON y tira un Error con
// el mensaje que devuelve la API cuando la respuesta no es exitosa.
export async function apiFetch(path, { token, ...options } = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const respuesta = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  const datos = await respuesta.json().catch(() => null)

  if (!respuesta.ok) {
    const mensaje = datos?.detail ?? 'Ocurrió un error al comunicarse con el servidor.'
    throw new Error(typeof mensaje === 'string' ? mensaje : 'Datos inválidos.')
  }

  return datos
}
