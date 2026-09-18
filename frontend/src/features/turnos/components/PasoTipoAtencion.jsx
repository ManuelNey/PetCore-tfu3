import { useEffect, useState } from 'react'
import TarjetaSeleccion from '../../../components/common/TarjetaSeleccion'
import Boton from '../../../components/common/Boton'
import Tarjeta from '../../../components/common/Tarjeta'
import { useAuth } from '../../../app/AuthContext'
import { listarTiposAtencion } from '../../../api/catalogos'

function PasoTipoAtencion({ seleccionado, onSeleccionar, onContinuar, onVolver }) {
  const { token } = useAuth()
  const [tiposAtencion, setTiposAtencion] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    listarTiposAtencion(token)
      .then((datos) => setTiposAtencion(datos.filter((tipo) => tipo.reservable_cliente)))
      .catch((error) => setError(error.message))
      .finally(() => setCargando(false))
  }, [token])

  return (
    <Tarjeta>
      <div className="paso-etiqueta">Paso 2 de 4</div>
      <h2 className="paso-titulo">¿Qué tipo de atención necesitás?</h2>
      <p className="paso-ayuda">La duración define los horarios que se te van a ofrecer.</p>

      {cargando && <p className="paso-ayuda">Cargando tipos de atención...</p>}
      {error && <p className="paso-ayuda">{error}</p>}

      <div className="paso-lista">
        {tiposAtencion.map((tipo) => (
          <TarjetaSeleccion
            key={tipo.id_tipo_atencion}
            titulo={tipo.nombre}
            subtitulo={tipo.descripcion}
            icono={null}
            seleccionada={seleccionado?.id_tipo_atencion === tipo.id_tipo_atencion}
            onClick={() => onSeleccionar(tipo)}
            etiquetaDerecha={`${tipo.duracion_minutos} min`}
          />
        ))}
      </div>

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

export default PasoTipoAtencion
