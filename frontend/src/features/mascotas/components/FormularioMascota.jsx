import { useEffect, useState } from 'react'
import Boton from '../../../components/common/Boton'
import { useAuth } from '../../../app/AuthContext'
import { listarEspecies } from '../../../api/especies'
import './FormularioMascota.css'

const MASCOTA_VACIA = {
  nombre: '',
  especie: '',
  raza: '',
  fecha_nacimiento: '',
}

function hoyComoTexto() {
  return new Date().toISOString().split('T')[0]
}

function FormularioMascota({ onGuardar, onCancelar }) {
  const { token } = useAuth()
  const [especies, setEspecies] = useState([])
  const [errorEspecies, setErrorEspecies] = useState('')
  const [mascota, setMascota] = useState(MASCOTA_VACIA)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listarEspecies(token)
      .then(setEspecies)
      .catch(() => setErrorEspecies('No se pudieron cargar las especies. Recargá la página.'))
  }, [token])

  function manejarCambio(evento) {
    const { name, value } = evento.target

    setMascota((mascotaActual) => ({
      ...mascotaActual,
      [name]: value,
    }))

    if (error) {
      setError('')
    }
  }

  async function manejarSubmit(evento) {
    evento.preventDefault()
    setError('')

    const nombreLimpio = mascota.nombre.trim()

    if (!nombreLimpio) {
      setError('El nombre no puede estar vacío.')
      return
    }

    if (!mascota.especie) {
      setError('Seleccioná una especie.')
      return
    }

    if (mascota.fecha_nacimiento && mascota.fecha_nacimiento > hoyComoTexto()) {
      setError('La fecha de nacimiento no puede ser una fecha futura.')
      return
    }

    setGuardando(true)

    try {
      await onGuardar({
        nombre: nombreLimpio,
        especie: mascota.especie,
        raza: mascota.raza.trim() || null,
        fecha_nacimiento: mascota.fecha_nacimiento || null,
      })
    } catch (errorRegistro) {
      setError(errorRegistro.message || 'No se pudo registrar la mascota.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="mascota-modal-fondo" onClick={onCancelar}>
      <div className="mascota-modal-panel" onClick={(evento) => evento.stopPropagation()}>
        <h2 className="mascota-modal-titulo">Registrar mascota</h2>
        <p className="mascota-modal-subtitulo">Completá los datos de tu mascota.</p>

        <form className="mascota-form" onSubmit={manejarSubmit}>
          <div className="mascota-form-grid">
            <div className="mascota-form-campo">
              <label htmlFor="nombre">Nombre</label>
              <input
                id="nombre"
                name="nombre"
                type="text"
                maxLength="100"
                placeholder="Nube"
                value={mascota.nombre}
                onChange={manejarCambio}
                autoFocus
                required
              />
            </div>

            <div className="mascota-form-campo">
              <label htmlFor="especie">Especie</label>
              <select
                id="especie"
                name="especie"
                value={mascota.especie}
                onChange={manejarCambio}
                required
              >
                <option value="" disabled>
                  Seleccionar...
                </option>
                {especies.map((especie) => (
                  <option key={especie.id_especie} value={especie.nombre}>
                    {especie.nombre}
                  </option>
                ))}
              </select>
              {errorEspecies && <p className="mascota-form-error">{errorEspecies}</p>}
            </div>

            <div className="mascota-form-campo">
              <label htmlFor="raza">Raza</label>
              <input
                id="raza"
                name="raza"
                type="text"
                maxLength="100"
                placeholder="Opcional"
                value={mascota.raza}
                onChange={manejarCambio}
              />
            </div>

            <div className="mascota-form-campo">
              <label htmlFor="fecha_nacimiento">Fecha de nacimiento</label>
              <input
                id="fecha_nacimiento"
                name="fecha_nacimiento"
                type="date"
                max={hoyComoTexto()}
                value={mascota.fecha_nacimiento}
                onChange={manejarCambio}
              />
            </div>
          </div>

          {error && (
            <p className="mascota-form-error" role="alert">
              {error}
            </p>
          )}

          <div className="mascota-form-acciones">
            <Boton type="button" variant="secundario" onClick={onCancelar} disabled={guardando}>
              Cancelar
            </Boton>
            <Boton type="submit" disabled={guardando}>
              {guardando ? 'Guardando...' : 'Guardar mascota'}
            </Boton>
          </div>
        </form>
      </div>
    </div>
  )
}

export default FormularioMascota
