import Boton from '../../../components/common/Boton'
import Tarjeta from '../../../components/common/Tarjeta'
import { etiquetaFechaLargaISO } from '../utils/fecha'

function PasoConfirmar({ mascota, tipoAtencion, veterinario, horario, confirmando, error, onVolver, onConfirmar }) {
  return (
    <Tarjeta>
      <div className="paso-etiqueta">Confirmación</div>
      <h2 className="paso-titulo">Revisá los datos del turno</h2>

      <div className="resumen-turno">
        <div className="resumen-fila">
          <span>Mascota</span>
          <strong>{mascota.nombre}</strong>
        </div>
        <div className="resumen-fila">
          <span>Tipo de atención</span>
          <strong>{tipoAtencion.nombre}</strong>
        </div>
        <div className="resumen-fila">
          <span>Veterinario</span>
          <strong>{`${veterinario.nombre} ${veterinario.apellido}`}</strong>
        </div>
        <div className="resumen-fila">
          <span>Horario</span>
          <strong>
            {etiquetaFechaLargaISO(horario.fecha)}, {horario.inicio} a {horario.fin}
          </strong>
        </div>
      </div>

      {error && <p className="paso-error">{error}</p>}

      <div className="paso-acciones">
        <Boton variant="secundario" onClick={onVolver} disabled={confirmando}>
          Volver
        </Boton>
        <Boton onClick={onConfirmar} disabled={confirmando}>
          {confirmando ? 'Confirmando...' : 'Confirmar turno'}
        </Boton>
      </div>
    </Tarjeta>
  )
}

export default PasoConfirmar
