import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Tarjeta from '../../../components/common/Tarjeta'
import Badge from '../../../components/common/Badge'
import Boton from '../../../components/common/Boton'
import { useAuth } from '../../../app/AuthContext'
import { cancelarTurno, listarTurnos } from '../../../api/turnos'
import './MisTurnosPage.css'

const PERIODOS = [
  { valor: 'proximos', etiqueta: 'Próximos' },
  { valor: 'pasados', etiqueta: 'Pasados' },
  { valor: 'todos', etiqueta: 'Todos' },
]

const VARIANTE_ESTADO = {
  CONFIRMADO: 'activa',
  CANCELADO: 'inactiva',
  COMPLETADO: 'neutral',
}

function formatearFechaHora(fechaIso) {
  return new Date(fechaIso).toLocaleString('es-UY', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function MisTurnosPage() {
  const { token } = useAuth()
  const [periodo, setPeriodo] = useState('proximos')
  const [turnos, setTurnos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [cancelandoId, setCancelandoId] = useState(null)

  useEffect(() => {
    const controlador = new AbortController()

    setCargando(true)
    setError('')

    listarTurnos(token, periodo)
      .then(setTurnos)
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setError(error.message)
        }
      })
      .finally(() => setCargando(false))

    return () => controlador.abort()
  }, [token, periodo])

  async function manejarCancelar(idTurno) {
    setCancelandoId(idTurno)

    try {
      await cancelarTurno(token, idTurno)
      setTurnos((actuales) =>
        actuales.map((turno) =>
          turno.id_turno === idTurno
            ? { ...turno, estado: 'CANCELADO', puede_cancelar: false }
            : turno,
        ),
      )
    } catch (error) {
      setError(error.message)
    } finally {
      setCancelandoId(null)
    }
  }

  return (
    <section className="turnos-page">
      <div className="turnos-encabezado">
        <h1>Mis turnos</h1>
        <Boton as={Link} to="/turnos/nuevo">
          + Reservar turno
        </Boton>
      </div>

      <div className="turnos-tabs">
        {PERIODOS.map((item) => (
          <button
            key={item.valor}
            type="button"
            className={periodo === item.valor ? 'tab tab-activo' : 'tab'}
            onClick={() => setPeriodo(item.valor)}
          >
            {item.etiqueta}
          </button>
        ))}
      </div>

      {cargando && <div className="turnos-mensaje">Cargando turnos...</div>}
      {!cargando && error && <div className="turnos-mensaje turnos-mensaje-error">{error}</div>}
      {!cargando && !error && turnos.length === 0 && (
        <div className="turnos-mensaje">No hay turnos para mostrar.</div>
      )}

      {!cargando && !error && turnos.length > 0 && (
        <div className="turnos-lista">
          {turnos.map((turno) => (
            <Tarjeta key={turno.id_turno} className="turno-card">
              <div className="turno-card-encabezado">
                <div>
                  <div className="turno-fecha">{formatearFechaHora(turno.fecha_hora_inicio)}</div>
                  <div className="turno-tipo">
                    {turno.tipo} · {turno.mascota.nombre} · {turno.veterinario}
                  </div>
                </div>
                <Badge variant={VARIANTE_ESTADO[turno.estado] ?? 'neutral'}>{turno.estado}</Badge>
              </div>

              <div className="turno-card-acciones">
                <Boton as={Link} to={`/turnos/${turno.id_turno}`} variant="secundario">
                  Ver detalle
                </Boton>
                {turno.puede_cancelar && (
                  <Boton
                    variant="secundario"
                    disabled={cancelandoId === turno.id_turno}
                    onClick={() => manejarCancelar(turno.id_turno)}
                  >
                    {cancelandoId === turno.id_turno ? 'Cancelando...' : 'Cancelar'}
                  </Boton>
                )}
              </div>
            </Tarjeta>
          ))}
        </div>
      )}
    </section>
  )
}

export default MisTurnosPage
