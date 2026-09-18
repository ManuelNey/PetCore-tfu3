import { useEffect, useState } from 'react'
import TarjetaSeleccion from '../../../components/common/TarjetaSeleccion'
import Boton from '../../../components/common/Boton'
import Tarjeta from '../../../components/common/Tarjeta'
import { useAuth } from '../../../app/AuthContext'
import { listarMascotas } from '../../../api/mascotas'

function PasoMascota({ seleccionada, onSeleccionar, onContinuar }) {
  const { token } = useAuth()
  const [mascotas, setMascotas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    listarMascotas(token)
      .then(setMascotas)
      .catch((error) => setError(error.message))
      .finally(() => setCargando(false))
  }, [token])

  const mascotasActivas = mascotas.filter((mascota) => mascota.estado === 'ACTIVA')

  return (
    <Tarjeta>
      <div className="paso-etiqueta">Paso 1 de 4</div>
      <h2 className="paso-titulo">¿Para qué mascota es el turno?</h2>
      <p className="paso-ayuda">Solo se listan tus mascotas activas.</p>

      {cargando && <p className="paso-ayuda">Cargando mascotas...</p>}
      {error && <p className="paso-ayuda">{error}</p>}

      <div className="paso-lista">
        {mascotasActivas.map((mascota) => (
          <TarjetaSeleccion
            key={mascota.id_mascota}
            titulo={mascota.nombre}
            subtitulo={`${mascota.especie}${mascota.raza ? ` · ${mascota.raza}` : ''}`}
            seleccionada={seleccionada?.id_mascota === mascota.id_mascota}
            onClick={() => onSeleccionar(mascota)}
          />
        ))}
      </div>

      <div className="paso-acciones paso-acciones-fin">
        <Boton disabled={!seleccionada} onClick={onContinuar}>
          Continuar
        </Boton>
      </div>
    </Tarjeta>
  )
}

export default PasoMascota
