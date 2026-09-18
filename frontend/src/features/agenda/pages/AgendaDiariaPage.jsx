import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Boton from '../../../components/common/Boton'
import { useAuth } from '../../../app/AuthContext'
import { obtenerAgenda } from '../../../api/agenda'
import { registrarConsulta } from '../../../api/turnos'
import RegistrarConsultaModal from '../components/RegistrarConsultaModal'
import './AgendaDiariaPage.css'

const HORA_INICIO_PREDETERMINADA = 8
const HORA_FIN_PREDETERMINADA = 18

const ETIQUETAS_ESTADO = {
  ATENDIDO: 'Atendido',
  EN_CURSO: 'En curso',
  CONFIRMADO: 'Confirmado',
  NO_ASISTIO: 'No asistió',
}

function obtenerFechaLocal() {
  const ahora = new Date()
  const diferenciaZonaHoraria = ahora.getTimezoneOffset() * 60_000

  return new Date(ahora.getTime() - diferenciaZonaHoraria)
    .toISOString()
    .slice(0, 10)
}

function obtenerHoraActual() {
  const ahora = new Date()

  return `${String(ahora.getHours()).padStart(2, '0')}:${String(ahora.getMinutes()).padStart(2, '0')}`
}

function desplazarFecha(fecha, cantidadDias) {
  const fechaNueva = new Date(`${fecha}T12:00:00`)
  fechaNueva.setDate(fechaNueva.getDate() + cantidadDias)

  const diferenciaZonaHoraria = fechaNueva.getTimezoneOffset() * 60_000

  return new Date(fechaNueva.getTime() - diferenciaZonaHoraria)
    .toISOString()
    .slice(0, 10)
}

function formatearFecha(fecha) {
  const texto = new Date(`${fecha}T12:00:00`).toLocaleDateString('es-UY', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

function convertirHoraAMinutos(hora) {
  const [horas, minutos] = hora.split(':').map(Number)

  return horas * 60 + minutos
}

function obtenerLimitesHorario(turnos) {
  if (turnos.length === 0) {
    return {
      horaInicio: HORA_INICIO_PREDETERMINADA,
      horaFin: HORA_FIN_PREDETERMINADA,
    }
  }

  const minutosInicio = turnos.map((turno) => convertirHoraAMinutos(turno.hora_inicio))
  const minutosFin = turnos.map(
    (turno) => convertirHoraAMinutos(turno.hora_inicio) + turno.duracion_minutos,
  )

  return {
    horaInicio: Math.min(
      HORA_INICIO_PREDETERMINADA,
      Math.floor(Math.min(...minutosInicio) / 60),
    ),
    horaFin: Math.max(
      HORA_FIN_PREDETERMINADA,
      Math.ceil(Math.max(...minutosFin) / 60),
    ),
  }
}

function crearHoras(horaInicio, horaFin) {
  return Array.from(
    { length: horaFin - horaInicio + 1 },
    (_, indice) => horaInicio + indice,
  )
}

function obtenerClaseEstado(estadoVisual) {
  return estadoVisual.toLowerCase().replaceAll('_', '-')
}

function FilaTurno({ turno, onRegistrarConsulta }) {
  const claseEstado = obtenerClaseEstado(turno.estado_visual)
  const puedeRegistrarConsulta = turno.estado_visual === 'EN_CURSO'

  return (
    <article className={`agenda-fila agenda-fila-${claseEstado}`}>
      <div className="agenda-fila-info">
        <strong>
          {turno.hora_inicio} · {turno.duracion_minutos}'
        </strong>
        <span>
          <b>{turno.mascota.nombre}</b> · {turno.mascota.especie} · {turno.propietario}
        </span>
      </div>

      <span className="agenda-fila-tipo">{turno.tipo}</span>

      <span className={`agenda-estado agenda-estado-${claseEstado}`}>
        {ETIQUETAS_ESTADO[turno.estado_visual] ?? turno.estado_visual}
      </span>

      <div className="agenda-fila-acciones">
        <Link className="agenda-link-historial" to={`/pacientes/${turno.mascota.id}/historial`}>
          Historial
        </Link>

        {puedeRegistrarConsulta && (
          <button
            type="button"
            className="agenda-boton-registrar"
            onClick={() => onRegistrarConsulta(turno)}
          >
            Registrar consulta
          </button>
        )}
      </div>

      {turno.agendado_por_administracion && (
        <span className="agenda-fila-administracion">
          Agendado por administración · tipo no reservable
        </span>
      )}
    </article>
  )
}

function MarcadorAhora({ hora }) {
  return (
    <div className="agenda-ahora">
      <span className="agenda-ahora-etiqueta">{hora}</span>
      <span className="agenda-ahora-linea" />
    </div>
  )
}

function AgendaDiariaPage() {
  const { token } = useAuth()
  const [fecha, setFecha] = useState(obtenerFechaLocal)
  const [agenda, setAgenda] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [actualizando, setActualizando] = useState(false)
  const [error, setError] = useState('')
  const [mostrarAvisoCambios, setMostrarAvisoCambios] = useState(false)
  const [turnoSeleccionado, setTurnoSeleccionado] = useState(null)
  const [mensajeExito, setMensajeExito] = useState('')

  useEffect(() => {
    const controlador = new AbortController()

    setCargando(true)
    setError('')
    setMostrarAvisoCambios(false)

    obtenerAgenda(token, fecha, null, controlador.signal)
      .then(setAgenda)
      .catch((errorPeticion) => {
        if (errorPeticion.name !== 'AbortError') {
          setError(errorPeticion.message)
        }
      })
      .finally(() => {
        if (!controlador.signal.aborted) {
          setCargando(false)
        }
      })

    return () => controlador.abort()
  }, [fecha, token])

  async function actualizarAgenda() {
    if (!agenda) {
      return
    }

    setActualizando(true)
    setError('')

    try {
      const agendaActualizada = await obtenerAgenda(
        token,
        fecha,
        agenda.consultado_el,
      )

      setAgenda(agendaActualizada)
      setMostrarAvisoCambios(agendaActualizada.hay_cambios)
    } catch (errorPeticion) {
      setError(errorPeticion.message)
    } finally {
      setActualizando(false)
    }
  }

  async function manejarGuardarConsulta(datosConsulta) {
    await registrarConsulta(token, turnoSeleccionado.id, datosConsulta)

    setTurnoSeleccionado(null)
    setMensajeExito(`Consulta de ${turnoSeleccionado.mascota.nombre} registrada correctamente.`)
    setTimeout(() => setMensajeExito(''), 4000)

    const agendaActualizada = await obtenerAgenda(token, fecha)
    setAgenda(agendaActualizada)
  }

  const turnos = agenda?.turnos ?? []
  const { horaInicio, horaFin } = obtenerLimitesHorario(turnos)
  const horas = crearHoras(horaInicio, horaFin)
  const esHoy = fecha === obtenerFechaLocal()
  const horaActual = obtenerHoraActual()
  const minutosAhora = esHoy ? convertirHoraAMinutos(horaActual) : null

  return (
    <section className="agenda-page">
      <div className="agenda-encabezado">
        <div>
          <h1>Agenda del día</h1>

          {agenda && (
            <p className="agenda-resumen-texto">
              {formatearFecha(agenda.fecha)} · {agenda.resumen.total}{' '}
              {agenda.resumen.total === 1 ? 'turno' : 'turnos'} ·{' '}
              {agenda.resumen.atendidos} atendidos · {agenda.resumen.en_curso} en curso
            </p>
          )}
        </div>

        <div className="agenda-navegacion">
          <Boton
            type="button"
            variant="secundario"
            onClick={() => setFecha((actual) => desplazarFecha(actual, -1))}
          >
            ◀ Ayer
          </Boton>

          <Boton
            type="button"
            variant="secundario"
            onClick={() => setFecha(obtenerFechaLocal())}
          >
            Hoy
          </Boton>

          <Boton
            type="button"
            variant="secundario"
            onClick={() => setFecha((actual) => desplazarFecha(actual, 1))}
          >
            Mañana ▶
          </Boton>

          <Boton type="button" disabled={actualizando || cargando} onClick={actualizarAgenda}>
            {actualizando ? 'Actualizando...' : '● Actualizar'}
          </Boton>
        </div>
      </div>

      {mensajeExito && (
        <div className="agenda-mensaje-exito" role="status">
          {mensajeExito}
        </div>
      )}

      {mostrarAvisoCambios && (
        <div className="agenda-aviso-cambios" role="status">
          <span>
            <strong>La agenda cambió.</strong> La información mostrada ya está actualizada.
          </span>

          <Boton type="button" onClick={() => setMostrarAvisoCambios(false)}>
            Ver cambios
          </Boton>
        </div>
      )}

      <div className="agenda-leyenda" aria-label="Estados de los turnos">
        <span>
          <i className="agenda-leyenda-marca agenda-leyenda-confirmado" />
          Pendiente de atención
        </span>
        <span>
          <i className="agenda-leyenda-marca agenda-leyenda-atendido" />
          Atendido
        </span>
        <span>
          <i className="agenda-leyenda-marca agenda-leyenda-en-curso" />
          En curso
        </span>
        {esHoy && (
          <span>
            <i className="agenda-leyenda-marca agenda-leyenda-ahora" />
            Hora actual {horaActual}
          </span>
        )}
      </div>

      {cargando && <div className="agenda-mensaje">Cargando agenda...</div>}

      {!cargando && error && (
        <div className="agenda-mensaje agenda-mensaje-error">{error}</div>
      )}

      {!cargando && !error && agenda && (
        <div className="agenda-panel">
          <div className="agenda-lista">
            {horas.slice(0, -1).map((hora) => {
              const turnosHora = turnos
                .filter((turno) => Math.floor(convertirHoraAMinutos(turno.hora_inicio) / 60) === hora)
                .sort((a, b) => convertirHoraAMinutos(a.hora_inicio) - convertirHoraAMinutos(b.hora_inicio))

              const mostrarAhoraAqui =
                minutosAhora != null && Math.floor(minutosAhora / 60) === hora

              const items = turnosHora.map((turno) => ({ tipo: 'turno', turno }))

              if (mostrarAhoraAqui) {
                const indiceInsercion = items.findIndex(
                  (item) => minutosAhora <= convertirHoraAMinutos(item.turno.hora_inicio),
                )

                const posicion = indiceInsercion === -1 ? items.length : indiceInsercion
                items.splice(posicion, 0, { tipo: 'ahora' })
              }

              return (
                <div className="agenda-hora-bloque" key={hora}>
                  <div className="agenda-hora-etiqueta">
                    {String(hora).padStart(2, '0')}:00
                  </div>

                  <div className="agenda-hora-contenido">
                    {items.length === 0 && <div className="agenda-hora-vacia" />}

                    {items.map((item) =>
                      item.tipo === 'ahora' ? (
                        <MarcadorAhora key="ahora" hora={horaActual} />
                      ) : (
                        <FilaTurno
                          key={item.turno.id}
                          turno={item.turno}
                          onRegistrarConsulta={setTurnoSeleccionado}
                        />
                      ),
                    )}
                  </div>
                </div>
              )
            })}

            {turnos.length === 0 && (
              <div className="agenda-vacia">No hay turnos para este día.</div>
            )}
          </div>

          <p className="agenda-nota">
            Los turnos cancelados no aparecen en la agenda.
          </p>
        </div>
      )}

      {turnoSeleccionado && (
        <RegistrarConsultaModal
          turno={turnoSeleccionado}
          onGuardar={manejarGuardarConsulta}
          onCancelar={() => setTurnoSeleccionado(null)}
        />
      )}
    </section>
  )
}

export default AgendaDiariaPage
