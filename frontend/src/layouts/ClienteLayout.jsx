import { Outlet } from 'react-router-dom'

// Contenedor de las rutas del rol cliente. La navegación general vive en
// el Header; este layout queda como punto de extensión propio del rol.
function ClienteLayout() {
  return <Outlet />
}

export default ClienteLayout
