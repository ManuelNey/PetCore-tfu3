import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import NavLink from './NavLink'
import { useAuth } from '../../app/AuthContext'
import './Header.css'

const LINKS_POR_ROL = {
  cliente: [
    { to: '/mascotas', label: 'Mis mascotas' },
    { to: '/turnos', label: 'Mis turnos' },
    { to: '/turnos/nuevo', label: 'Reservar turno' },
  ],
  veterinario: [
    { to: '/agenda', label: 'Mi agenda' },
    { to: '/pacientes', label: 'Pacientes' },
  ],
}

function obtenerIniciales(nombre) {
  return nombre
    .split(' ')
    .map((palabra) => palabra[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function Header() {
  const [menuAbierto, setMenuAbierto] = useState(false)
  const { usuario, logout } = useAuth()
  const navigate = useNavigate()

  const rol = usuario.rol.toLowerCase()
  const nombreCompleto = `${usuario.nombre} ${usuario.apellido}`
  const links = LINKS_POR_ROL[rol] ?? []

  function manejarLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="header">
      <div className="header-barra">
        <div className="header-marca">
          <span className="header-logo">Pet-Core</span>

          <nav className={`header-nav ${menuAbierto ? 'header-nav-abierto' : ''}`}>
            {links.map((link) => (
              <NavLink key={link.to} to={link.to}>
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="header-usuario">
          <span className="header-badge-rol">{usuario.rol}</span>
          <span className="header-nombre">{nombreCompleto}</span>
          <span className="header-avatar">{obtenerIniciales(nombreCompleto)}</span>
          <button type="button" className="header-logout" onClick={manejarLogout}>
            Cerrar sesión
          </button>
        </div>

        <button
          type="button"
          className="header-hamburguesa"
          aria-label="Abrir menú"
          aria-expanded={menuAbierto}
          onClick={() => setMenuAbierto((abierto) => !abierto)}
        >
          ☰
        </button>
      </div>
    </header>
  )
}

export default Header
