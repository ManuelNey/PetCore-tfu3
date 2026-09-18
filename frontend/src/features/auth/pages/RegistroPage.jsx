import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Boton from '../../../components/common/Boton'
import './Auth.css'

const DATOS_INICIALES = {
  nombre: '',
  apellido: '',
  documento: '',
  correo: '',
  telefono: '',
  contrasena: '',
  confirmar_contrasena: '',
}

function RegistroPage() {
  const navigate = useNavigate()

  const [formulario, setFormulario] = useState(DATOS_INICIALES)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  const manejarCambio = (evento) => {
    const { name, value } = evento.target

    setFormulario((datosActuales) => ({
      ...datosActuales,
      [name]: value,
    }))

    if (error) {
      setError('')
    }
  }

  const obtenerMensajeError = (detalle) => {
    if (typeof detalle === 'string') {
      return detalle
    }

    if (Array.isArray(detalle)) {
      return detalle
        .map((errorValidacion) => errorValidacion.msg)
        .join('. ')
    }

    return 'No fue posible crear la cuenta.'
  }

  const manejarRegistro = async (evento) => {
    evento.preventDefault()
    setError('')

    if (formulario.contrasena !== formulario.confirmar_contrasena) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setCargando(true)

    try {
      const respuesta = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nombre: formulario.nombre.trim(),
          apellido: formulario.apellido.trim(),
          documento: formulario.documento.trim(),
          correo: formulario.correo.trim().toLowerCase(),
          telefono: formulario.telefono.trim(),
          contrasena: formulario.contrasena,
          confirmar_contrasena: formulario.confirmar_contrasena,
        }),
      })

      const datos = await respuesta.json().catch(() => null)

      if (!respuesta.ok) {
        throw new Error(
          obtenerMensajeError(datos?.detail || datos?.message),
        )
      }

      navigate('/login', {
        replace: true,
        state: {
          mensaje: 'Cuenta creada correctamente. Ya podés iniciar sesión.',
        },
      })
    } catch (errorRegistro) {
      setError(
        errorRegistro.message ||
          'No se pudo conectar con el servidor. Intentá nuevamente.',
      )
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="auth-pantalla">
      <div className="auth-panel">
        <span className="auth-logo">Pet-Core</span>

        <div className="auth-tarjeta">
          <h1 className="auth-titulo">Crear cuenta</h1>

          <p className="auth-subtitulo">
            Clínica Veterinaria · sede única
          </p>

          <form className="auth-form" onSubmit={manejarRegistro}>
            <div className="auth-campo">
              <label htmlFor="nombre">Nombre</label>
              <input
                id="nombre"
                name="nombre"
                type="text"
                placeholder="Ana"
                autoComplete="given-name"
                value={formulario.nombre}
                onChange={manejarCambio}
                required
              />
            </div>

            <div className="auth-campo">
              <label htmlFor="apellido">Apellido</label>
              <input
                id="apellido"
                name="apellido"
                type="text"
                placeholder="Pérez"
                autoComplete="family-name"
                value={formulario.apellido}
                onChange={manejarCambio}
                required
              />
            </div>

            <div className="auth-campo">
              <label htmlFor="documento">Documento</label>
              <input
                id="documento"
                name="documento"
                type="text"
                inputMode="numeric"
                placeholder="48945678"
                autoComplete="off"
                value={formulario.documento}
                onChange={manejarCambio}
                required
              />
            </div>

            <div className="auth-campo">
              <label htmlFor="correo">Correo electrónico</label>
              <input
                id="correo"
                name="correo"
                type="email"
                placeholder="ana@prueba.com"
                autoComplete="email"
                value={formulario.correo}
                onChange={manejarCambio}
                required
              />
            </div>

            <div className="auth-campo">
              <label htmlFor="telefono">Teléfono</label>
              <input
                id="telefono"
                name="telefono"
                type="tel"
                inputMode="tel"
                placeholder="099456789"
                autoComplete="tel"
                value={formulario.telefono}
                onChange={manejarCambio}
                required
              />
            </div>

            <div className="auth-campo">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                id="contrasena"
                name="contrasena"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                value={formulario.contrasena}
                onChange={manejarCambio}
                required
              />
            </div>

            <div className="auth-campo">
              <label htmlFor="confirmar-contrasena">
                Confirmar contraseña
              </label>

              <input
                id="confirmar-contrasena"
                name="confirmar_contrasena"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                value={formulario.confirmar_contrasena}
                onChange={manejarCambio}
                required
              />
            </div>

            {error && (
              <p className="auth-error" role="alert">
                {error}
              </p>
            )}

            <Boton
              type="submit"
              className="auth-boton"
              disabled={cargando}
            >
              {cargando ? 'Creando cuenta...' : 'Crear cuenta'}
            </Boton>

            <div className="auth-enlaces">
              <Link to="/login">Ya tengo cuenta</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default RegistroPage