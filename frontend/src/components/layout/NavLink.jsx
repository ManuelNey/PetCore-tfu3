import { NavLink as RouterNavLink } from 'react-router-dom'

// Wrapper fino sobre el NavLink de react-router para aplicar la clase
// "activo" de forma consistente en toda la navegación.
function NavLink({ to, children }) {
  return (
    <RouterNavLink
      to={to}
      end
      className={({ isActive }) => (isActive ? 'nav-link nav-link-activo' : 'nav-link')}
    >
      {children}
    </RouterNavLink>
  )
}

export default NavLink
