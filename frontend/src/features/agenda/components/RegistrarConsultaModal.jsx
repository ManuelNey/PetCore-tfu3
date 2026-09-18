import { useState } from 'react'
import Boton from '../../../components/common/Boton'
import './RegistrarConsultaModal.css'

const CONSULTA_VACIA = {
  motivo: '',
  diagnostico: '',
  observaciones: '',
  tratamiento: '',
  recomendaciones: '',
}

function RegistrarConsultaModal({ turno, onGuardar, onCancelar }) {
  const [consulta, setConsulta] = useState(CONSULTA_VACIA)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')

  function manejarCambio(evento) {
    const { name, value } = evento.target

    setConsulta((actual) => ({ ...actual, [name]: value }))

    if (error) {
      setError('')
    }
  }

  async function manejarSubmit(evento) {
    evento.preventDefault()
    setError('')

    const motivo = consulta.motivo.trim()
    const diagnostico = consulta.diagnostico.trim()

    if (!motivo) {
      setError('El motivo no puede estar vacío.')
      return
    }

    if (!diagnostico) {
      setError('El diagnóstico no puede estar vacío.')
      return
    }

    setGuardando(true)

    try {
      await onGuardar({
        motivo,
        diagnostico,
        observaciones: consulta.observaciones.trim() || null,
        tratamiento: consulta.tratamiento.trim() || null,
        recomendaciones: consulta.recomendaciones.trim() || null,
      })
    } catch (errorRegistro) {
      setError(errorRegistro.message || 'No se pudo registrar la consulta.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="consulta-modal-fondo" onClick={onCancelar}>
      <div className="consulta-modal-panel" onClick={(evento) => evento.stopPropagation()}>
        <h2 className="consulta-modal-titulo">Registrar consulta</h2>
        <p className="consulta-modal-subtitulo">
          {turno.mascota.nombre} · {turno.mascota.especie} · {turno.hora_inicio} · {turno.tipo}
        </p>

        <form className="consulta-form" onSubmit={manejarSubmit}>
          <div className="consulta-form-campo">
            <label htmlFor="motivo">Motivo</label>
            <textarea
              id="motivo"
              name="motivo"
              rows={2}
              value={consulta.motivo}
              onChange={manejarCambio}
              autoFocus
              required
            />
          </div>

          <div className="consulta-form-campo">
            <label htmlFor="diagnostico">Diagnóstico</label>
            <textarea
              id="diagnostico"
              name="diagnostico"
              rows={2}
              value={consulta.diagnostico}
              onChange={manejarCambio}
              required
            />
          </div>

          <div className="consulta-form-campo">
            <label htmlFor="observaciones">Observaciones (opcional)</label>
            <textarea
              id="observaciones"
              name="observaciones"
              rows={2}
              value={consulta.observaciones}
              onChange={manejarCambio}
            />
          </div>

          <div className="consulta-form-campo">
            <label htmlFor="tratamiento">Tratamiento (opcional)</label>
            <textarea
              id="tratamiento"
              name="tratamiento"
              rows={2}
              value={consulta.tratamiento}
              onChange={manejarCambio}
            />
          </div>

          <div className="consulta-form-campo">
            <label htmlFor="recomendaciones">Recomendaciones (opcional)</label>
            <textarea
              id="recomendaciones"
              name="recomendaciones"
              rows={2}
              value={consulta.recomendaciones}
              onChange={manejarCambio}
            />
          </div>

          {error && (
            <p className="consulta-form-error" role="alert">
              {error}
            </p>
          )}

          <div className="consulta-form-acciones">
            <Boton type="button" variant="secundario" onClick={onCancelar} disabled={guardando}>
              Cancelar
            </Boton>
            <Boton type="submit" disabled={guardando}>
              {guardando ? 'Guardando...' : 'Guardar consulta'}
            </Boton>
          </div>
        </form>
      </div>
    </div>
  )
}

export default RegistrarConsultaModal
