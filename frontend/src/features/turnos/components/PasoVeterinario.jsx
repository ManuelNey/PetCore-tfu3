import { useEffect, useState } from 'react'
import TarjetaSeleccion from '../../../components/common/TarjetaSeleccion'
import Boton from '../../../components/common/Boton'
import Tarjeta from '../../../components/common/Tarjeta'
import { useAuth } from '../../../app/AuthContext'
import { listarVeterinarios } from '../../../api/catalogos'

function PasoVeterinario({ seleccionado, onSeleccionar, onContinuar, onVolver }) {
  const { token } = useAuth()
  const [veterinarios, setVeterinarios] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    listarVeterinarios(token)
      .then(setVeterinarios)
      .catch((error) => setError(error.message))
      .finally(() => setCargando(false))
  }, [token])

  return (
    <Tarjeta>
      <div className="paso-etiqueta">Paso 3 de 4</div>
      <h2 className="paso-titulo">Elegí veterinario</h2>

      {cargando && <p className="paso-ayuda">Cargando veterinarios...</p>}
      {error && <p className="paso-ayuda">{error}</p>}

      <div className="paso-lista">
        {veterinarios.map((veterinario) => (
          <TarjetaSeleccion
            key={veterinario.id_usuario}
            titulo={`${veterinario.nombre} ${veterinario.apellido}`}
            subtitulo={`MP ${veterinario.matricula_profesional}`}
            seleccionada={seleccionado?.id_usuario === veterinario.id_usuario}
            onClick={() => onSeleccionar(veterinario)}
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

export default PasoVeterinario
