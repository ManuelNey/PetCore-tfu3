import { useEffect, useState } from 'react'
import Boton from '../../../components/common/Boton'
import Tarjeta from '../../../components/common/Tarjeta'
import { useAuth } from '../../../app/AuthContext'
import { obtenerDisponibilidad } from '../../../api/turnos'
import { aISO, esMismoDia, etiquetaFecha, etiquetaFechaLarga, inicioDeHoy, sumarMinutos } from '../utils/fecha'

const MOTIVO_ESTADO = {
  OCUPADO: 'ocupado',
  HUECO_INSUFICIENTE: 'hueco',
  FUERA_DE_AGENDA: 'fuera-agenda',
}

const MOTIVO_TITULO = {
  OCUPADO: 'Ocupado',
  HUECO_INSUFICIENTE: 'Hueco insuficiente para la duración elegida',
  FUERA_DE_AGENDA: 'Fuera del horario del veterinario',
}

function estadoSlot(slot, seleccionado) {
  if (seleccionado && slot.inicio === seleccionado.inicio) return 'seleccionado'
  if (slot.disponible) return 'disponible'
  return MOTIVO_ESTADO[slot.motivo] ?? 'fuera-agenda'
}

function GrupoHorarios({ titulo, rango, slots, seleccionado, onElegir }) {
  if (slots.length === 0) return null

  return (
    <div>
      <div className="horario-franja-titulo">
        {titulo} · {rango}
      </div>
      <div className="horario-grid">
        {slots.map((slot) => {
          const estado = estadoSlot(slot, seleccionado)
          const habilitado = estado === 'disponible' || estado === 'seleccionado'

          return (
            <button
              type="button"
              key={slot.inicio}
              className={`horario-slot horario-slot-${estado}`}
              disabled={!habilitado}
              title={MOTIVO_TITULO[slot.motivo]}
              onClick={() => onElegir(slot.inicio)}
            >
              {slot.inicio}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function PasoHorario({
  mascota,
  tipoAtencion,
  veterinario,
  fecha,
  onCambiarFecha,
  seleccionado,
  onSeleccionar,
  onContinuar,
  onVolver,
  error: errorExterno,
}) {
  const { token } = useAuth()
  const [slots, setSlots] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!veterinario || !tipoAtencion) return

    setCargando(true)
    setError(null)

    obtenerDisponibilidad(token, {
      veterinario: veterinario.id_usuario,
      fecha: aISO(fecha),
      tipoAtencion: tipoAtencion.id_tipo_atencion,
    })
      .then((datos) => setSlots(datos.slots))
      .catch((error) => setError(error.message))
      .finally(() => setCargando(false))
  }, [token, veterinario, tipoAtencion, fecha])

  function cambiarDia(cantidadDias) {
    onSeleccionar(null)
    onCambiarFecha(cantidadDias)
  }

  function elegirHorario(inicio) {
    onSeleccionar({
      fecha: aISO(fecha),
      inicio,
      fin: sumarMinutos(inicio, tipoAtencion.duracion_minutos),
    })
  }

  const manana = slots.filter((slot) => slot.inicio < '12:00')
  const tarde = slots.filter((slot) => slot.inicio >= '12:00')
  const puedeRetroceder = !esMismoDia(fecha, inicioDeHoy())

  return (
    <Tarjeta>
      <div className="paso-etiqueta">Paso 4 de 4</div>
      <h2 className="paso-titulo">Elegí un horario</h2>
      <p className="paso-ayuda">
        Se ofrecen solo los huecos libres de {tipoAtencion?.duracion_minutos} minutos o más, en múltiplos de 15.
      </p>

      <div className="horario-navegador">
        <button
          type="button"
          className="horario-nav-flecha"
          onClick={() => cambiarDia(-1)}
          disabled={!puedeRetroceder}
          aria-label="Día anterior"
        >
          ‹
        </button>
        <div className="horario-fecha-actual">{etiquetaFecha(fecha)}</div>
        <button
          type="button"
          className="horario-nav-flecha"
          onClick={() => cambiarDia(1)}
          aria-label="Día siguiente"
        >
          ›
        </button>
      </div>

      <div className="horario-leyenda">
        <span className="horario-leyenda-item">
          <span className="horario-leyenda-muestra horario-slot-disponible" /> Disponible
        </span>
        <span className="horario-leyenda-item">
          <span className="horario-leyenda-muestra horario-slot-seleccionado" /> Seleccionado
        </span>
        <span className="horario-leyenda-item">
          <span className="horario-leyenda-muestra horario-slot-ocupado" /> Ocupado
        </span>
        <span className="horario-leyenda-item">
          <span className="horario-leyenda-muestra horario-slot-hueco" /> Hueco insuficiente
        </span>
      </div>

      {cargando && <p className="paso-ayuda">Buscando horarios disponibles...</p>}
      {error && <p className="paso-ayuda">{error}</p>}

      {!cargando && !error && (
        <div className="horario-franjas">
          <GrupoHorarios
            titulo="Mañana"
            rango="8:00 a 12:00"
            slots={manana}
            seleccionado={seleccionado}
            onElegir={elegirHorario}
          />
          <GrupoHorarios
            titulo="Tarde"
            rango="12:00 a 18:00"
            slots={tarde}
            seleccionado={seleccionado}
            onElegir={elegirHorario}
          />
          {slots.length === 0 && <p className="paso-ayuda">No hay horarios para este día.</p>}
        </div>
      )}

      {errorExterno && <p className="paso-error">{errorExterno}</p>}

      {seleccionado && (
        <div className="horario-resumen">
          <div className="horario-resumen-etiqueta">Resumen</div>
          <div className="horario-resumen-texto">
            {mascota?.nombre} · {tipoAtencion?.nombre} ({tipoAtencion?.duracion_minutos} min) ·{' '}
            {veterinario?.nombre} {veterinario?.apellido}
            <br />
            {etiquetaFechaLarga(fecha)}, {seleccionado.inicio} a {seleccionado.fin}
          </div>
        </div>
      )}

      <div className="paso-acciones">
        <Boton variant="secundario" onClick={onVolver}>
          Volver
        </Boton>
        <Boton disabled={!seleccionado} onClick={onContinuar}>
          Continuar
        </Boton>
      </div>
    </Tarjeta>
  )
}

export default PasoHorario
