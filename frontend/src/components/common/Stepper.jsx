import './Stepper.css'

// Indicador de progreso reutilizable para flujos de varios pasos.
function Stepper({ pasos, pasoActual }) {
  return (
    <div className="stepper">
      {pasos.map((paso, indice) => {
        const numero = indice + 1
        const activo = numero === pasoActual
        const completado = numero < pasoActual

        return (
          <div className="stepper-item" key={paso}>
            <div className="stepper-paso">
              <span className={`stepper-numero ${activo || completado ? 'stepper-numero-activo' : ''}`}>
                {numero}
              </span>
              <div>
                <div className={`stepper-etiqueta ${activo ? 'stepper-etiqueta-activa' : ''}`}>{paso}</div>
                {activo && <div className="stepper-estado">En curso</div>}
              </div>
            </div>
            {numero < pasos.length && <div className="stepper-linea" />}
          </div>
        )
      })}
    </div>
  )
}

export default Stepper
