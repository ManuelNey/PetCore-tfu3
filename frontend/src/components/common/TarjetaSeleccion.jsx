import Badge from './Badge'
import './TarjetaSeleccion.css'

// Fila seleccionable reutilizada en los pasos de reserva (mascota, tipo de
// atención, veterinario) y en cualquier otro listado de elección única.
function TarjetaSeleccion({
  titulo,
  subtitulo,
  seleccionada = false,
  deshabilitada = false,
  etiquetaDerecha,
  icono = 'foto',
  onClick,
}) {
  const clases = ['tarjeta-seleccion']
  if (seleccionada) clases.push('tarjeta-seleccion-activa')
  if (deshabilitada) clases.push('tarjeta-seleccion-deshabilitada')

  return (
    <button
      type="button"
      className={clases.join(' ')}
      onClick={onClick}
      disabled={deshabilitada}
    >
      {icono && <div className="tarjeta-seleccion-icono">{icono}</div>}
      <div className="tarjeta-seleccion-texto">
        <div className="tarjeta-seleccion-titulo">{titulo}</div>
        {subtitulo && <div className="tarjeta-seleccion-subtitulo">{subtitulo}</div>}
      </div>
      {etiquetaDerecha && <Badge variant="inactiva">{etiquetaDerecha}</Badge>}
      {seleccionada && <span className="tarjeta-seleccion-check">✓</span>}
    </button>
  )
}

export default TarjetaSeleccion
