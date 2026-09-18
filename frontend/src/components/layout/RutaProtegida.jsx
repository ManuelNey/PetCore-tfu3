import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../app/AuthContext'

// Exige sesión iniciada antes de mostrar cualquier ruta de la app.
// Mientras se resuelve el /me inicial no se sabe si hay sesión, así que
// se espera en vez de mandar a /login por las dudas.
function RutaProtegida() {
  const { cargando, estaAutenticado } = useAuth()

  if (cargando) {
    return <p style={{ padding: 24 }}>Cargando…</p>
  }

  if (!estaAutenticado) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export default RutaProtegida
