import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Tarjeta from '../../../components/common/Tarjeta'
import Badge from '../../../components/common/Badge'
import Boton from '../../../components/common/Boton'
import { useAuth } from '../../../app/AuthContext'
import { cancelarTurno, obtenerTurno } from '../../../api/turnos'
import './DetalleTurnoPage.css'

const VARIANTE_ESTADO = {
  CONFIRMADO: 'activa',
  CANCELADO: 'inactiva',
  COMPLETADO: 'neutral',
}

function formatearFechaHora(fechaIso) {
  return new Date(fechaIso).toLocaleString('es-UY', {
    dateStyle: 'full',
    timeStyle: 'short',
  })
}

function DetalleTurnoPage() {
  const { id } = useParams()
  const { token } = useAuth()
  const navigate = useNavigate()

  const [turno, setTurno] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [cancelando, setCancelando] = useState(false)

  useEffect(() => {
    setCargando(true)
    setError('')

    obtenerTurno(token, id)
      .then(setTurno)
      .catch((error) => setError(error.message))
      .finally(() => setCargando(false))
  }, [token, id])

  async function manejarCancelar() {
    setCancelando(true)

    try {
      await cancelarTurno(token, id)
      setTurno((actual) => ({ ...actual, estado: 'CANCELADO', puede_cancelar: false }))
    } catch (error) {
      setError(error.message)
    } finally {
      setCancelando(false)
    }
  }

  if (cargando) {
    return <section className="detalle-turno-page">Cargando turno...</section>
  }

  if (error) {
    return (
      <section className="detalle-turno-page">
        <p className="detalle-turno-error">{error}</p>
        <Boton variant="secundario" onClick={() => navigate('/turnos')}>
          Volver a mis turnos
        </Boton>
      </section>
    )
  }

  return (
    <section className="detalle-turno-page">
      <Link to="/turnos" className="detalle-turno-volver">
        ← Volver a mis turnos
      </Link>

      <Tarjeta className="detalle-turno-card">
        <div className="detalle-turno-encabezado">
          <h1>{turno.tipo}</h1>
          <Badge variant={VARIANTE_ESTADO[turno.estado] ?? 'neutral'}>{turno.estado}</Badge>
        </div>

        <div className="detalle-turno-filas">
          <div className="detalle-turno-fila">
            <span>Fecha y hora</span>
            <strong>{formatearFechaHora(turno.fecha_hora_inicio)}</strong>
          </div>
          <div className="detalle-turno-fila">
            <span>Duración</span>
            <strong>{turno.duracion_minutos} min</strong>
          </div>
          <div className="detalle-turno-fila">
            <span>Mascota</span>
            <strong>
              {turno.mascota.nombre} · {turno.mascota.especie}
            </strong>
          </div>
          <div className="detalle-turno-fila">
            <span>Veterinario</span>
            <strong>{turno.veterinario}</strong>
          </div>
          <div className="detalle-turno-fila">
            <span>Canal de origen</span>
            <strong>{turno.canal_origen}</strong>
          </div>
        </div>

        {turno.puede_cancelar && (
          <div className="detalle-turno-acciones">
            <Boton variant="secundario" disabled={cancelando} onClick={manejarCancelar}>
              {cancelando ? 'Cancelando...' : 'Cancelar turno'}
            </Boton>
          </div>
        )}
      </Tarjeta>
    </section>
  )
}

export default DetalleTurnoPage
