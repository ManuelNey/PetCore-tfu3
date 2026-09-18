import { Outlet } from 'react-router-dom'

// Contenedor de las rutas del rol veterinario. La navegación general vive
// en el Header; este layout queda como punto de extensión propio del rol.
function VeterinarioLayout() {
  return <Outlet />
}

export default VeterinarioLayout
