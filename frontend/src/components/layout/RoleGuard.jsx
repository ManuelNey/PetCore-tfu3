import { Navigate } from 'react-router-dom'
import { useAuth } from '../../app/AuthContext'

// Redirige si el rol del usuario autenticado no coincide con el permitido
// para esta sección. Se usa dentro de RutaProtegida, así que ya hay usuario.
function RoleGuard({ rolPermitido, children }) {
  const { usuario } = useAuth()

  if (usuario.rol.toLowerCase() !== rolPermitido) {
    return <Navigate to="/" replace />
  }

  return children
}

export default RoleGuard
