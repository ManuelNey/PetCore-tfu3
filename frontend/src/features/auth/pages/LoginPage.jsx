import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Boton from '../../../components/common/Boton'
import { useAuth } from '../../../app/AuthContext'
import './Auth.css'

function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function manejarSubmit(evento) {
    evento.preventDefault()
    setError(null)
    setEnviando(true)

    try {
      await login(correo, contrasena)
      navigate('/', { replace: true })
    } catch (error) {
      setError(error.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="auth-pantalla">
      <div className="auth-panel">
        <span className="auth-logo">Pet-Core</span>

        <div className="auth-tarjeta">
          <h1 className="auth-titulo">Iniciar sesión</h1>
          <p className="auth-subtitulo">Clínica Veterinaria · sede única</p>

          <form className="auth-form" onSubmit={manejarSubmit}>
            <div className="auth-campo">
              <label htmlFor="correo">Correo electrónico</label>
              <input
                id="correo"
                type="email"
                placeholder="nombre@correo.com"
                value={correo}
                onChange={(evento) => setCorreo(evento.target.value)}
                required
              />
            </div>
            <div className="auth-campo">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                id="contrasena"
                type="password"
                placeholder="••••••••"
                value={contrasena}
                onChange={(evento) => setContrasena(evento.target.value)}
                required
              />
            </div>

            {error && <p className="auth-error">{error}</p>}

            <Boton type="submit" className="auth-boton" disabled={enviando}>
              {enviando ? 'Ingresando…' : 'Ingresar'}
            </Boton>
            <div className="auth-enlaces">
              <a href="#">Olvidé mi contraseña</a>
              <Link to="/registro">Crear cuenta</Link>
            </div>
          </form>
        </div>

        <p className="auth-nota">
          Estado inicial. Sin segundo factor para ningún rol. El rol se determina del lado del
          servidor tras validar credenciales.
        </p>
      </div>
    </div>
  )
}

export default LoginPage
