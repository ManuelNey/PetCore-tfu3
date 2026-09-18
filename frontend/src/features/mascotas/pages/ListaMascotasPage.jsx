import { useEffect, useState } from 'react'
import MascotaCard from '../components/MascotaCard'
import FormularioMascota from '../components/FormularioMascota'
import Boton from '../../../components/common/Boton'
import { useAuth } from '../../../app/AuthContext'
import './ListaMascotasPage.css'

const API_URL = 'http://localhost:8000'

function obtenerMensajeError(
  detalle,
  mensajePredeterminado,
) {
  if (typeof detalle === 'string') {
    return detalle
  }

  if (Array.isArray(detalle)) {
    return detalle
      .map((error) => error.msg)
      .join('. ')
  }

  return mensajePredeterminado
}

function calcularEdad(fechaNacimiento) {
  if (!fechaNacimiento) {
    return '—'
  }

  const nacimiento = new Date(
    `${fechaNacimiento}T00:00:00`,
  )
  const hoy = new Date()

  let edad =
    hoy.getFullYear() - nacimiento.getFullYear()

  const todaviaNoCumplio =
    hoy.getMonth() < nacimiento.getMonth() ||
    (hoy.getMonth() === nacimiento.getMonth() &&
      hoy.getDate() < nacimiento.getDate())

  if (todaviaNoCumplio) {
    edad -= 1
  }

  return `${edad} ${edad === 1 ? 'año' : 'años'}`
}

function adaptarMascota(mascota) {
  return {
    id: mascota.id_mascota,
    nombre: mascota.nombre,
    especie: mascota.especie,
    raza: mascota.raza || 'Sin especificar',
    activa: mascota.estado === 'ACTIVA',
    edad: calcularEdad(mascota.fecha_nacimiento),

    // Todavía no forman parte del GET.
    ultimoPeso: '—',
    proximoTurno: 'Sin turnos',
    consultas: 0,
  }
}

function ListaMascotasPage() {
  const { token } = useAuth()

  const [mascotas, setMascotas] = useState([])
  const [soloActivas, setSoloActivas] = useState(true)
  const [formularioAbierto, setFormularioAbierto] =
    useState(false)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [errorAccion, setErrorAccion] = useState('')
  const [mensajeExito, setMensajeExito] = useState('')
  const [
    idMascotaCambiandoEstado,
    setIdMascotaCambiandoEstado,
  ] = useState(null)

  useEffect(() => {
    const controlador = new AbortController()

    async function obtenerMascotas() {
      if (!token) {
        setError('No se encontró el token de acceso.')
        setCargando(false)
        return
      }

      try {
        setCargando(true)
        setError('')

        const respuesta = await fetch(
          `${API_URL}/mascotas`,
          {
            method: 'GET',
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controlador.signal,
          },
        )

        const datos = await respuesta
          .json()
          .catch(() => null)

        if (!respuesta.ok) {
          throw new Error(
            obtenerMensajeError(
              datos?.detail,
              'No se pudieron obtener las mascotas.',
            ),
          )
        }

        const mascotasAdaptadas = datos.map(
          adaptarMascota,
        )

        setMascotas(mascotasAdaptadas)
      } catch (errorPeticion) {
        if (errorPeticion.name !== 'AbortError') {
          setError(
            errorPeticion.message ||
              'No se pudo conectar con el servidor.',
          )
        }
      } finally {
        if (!controlador.signal.aborted) {
          setCargando(false)
        }
      }
    }

    obtenerMascotas()

    return () => {
      controlador.abort()
    }
  }, [token])

  const mascotasVisibles = soloActivas
    ? mascotas.filter((mascota) => mascota.activa)
    : mascotas

  function mostrarMensajeExito(mensaje) {
    setMensajeExito(mensaje)

    setTimeout(() => {
      setMensajeExito('')
    }, 4000)
  }

  async function agregarMascota(datos) {
    if (!token) {
      throw new Error(
        'No se encontró el token de acceso.',
      )
    }

    const respuesta = await fetch(
      `${API_URL}/mascotas`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(datos),
      },
    )

    const resultado = await respuesta
      .json()
      .catch(() => null)

    if (!respuesta.ok) {
      throw new Error(
        obtenerMensajeError(
          resultado?.detail,
          'No se pudo registrar la mascota.',
        ),
      )
    }

    const mascotaCreada = adaptarMascota(resultado)

    setMascotas((mascotasActuales) => [
      ...mascotasActuales,
      mascotaCreada,
    ])

    setFormularioAbierto(false)

    mostrarMensajeExito(
      `${mascotaCreada.nombre} se registró correctamente.`,
    )
  }

  async function cambiarEstadoMascota(mascota) {
    if (!token) {
      setErrorAccion(
        'No se encontró el token de acceso.',
      )
      return
    }

    const accion = mascota.activa
      ? 'inactivar'
      : 'activar'

    setIdMascotaCambiandoEstado(mascota.id)
    setErrorAccion('')
    setMensajeExito('')

    try {
      const respuesta = await fetch(
        `${API_URL}/mascotas/${mascota.id}/${accion}`,
        {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      )

      const resultado = await respuesta
        .json()
        .catch(() => null)

      if (!respuesta.ok) {
        throw new Error(
          obtenerMensajeError(
            resultado?.detail,
            `No se pudo ${accion} la mascota.`,
          ),
        )
      }

      const mascotaActualizada =
        adaptarMascota(resultado)

      setMascotas((mascotasActuales) =>
        mascotasActuales.map((mascotaActual) =>
          mascotaActual.id === mascota.id
            ? mascotaActualizada
            : mascotaActual,
        ),
      )

      const mensaje = mascotaActualizada.activa
        ? `${mascotaActualizada.nombre} fue activada correctamente.`
        : `${mascotaActualizada.nombre} fue inactivada correctamente.`

      mostrarMensajeExito(mensaje)
    } catch (errorPeticion) {
      setErrorAccion(
        errorPeticion.message ||
          `No se pudo ${accion} la mascota.`,
      )
    } finally {
      setIdMascotaCambiandoEstado(null)
    }
  }

  return (
    <section className="mascotas-page">
      <div className="mascotas-encabezado">
        <div>
          <h1>Mis mascotas</h1>

          <p className="mascotas-resumen">
            {mascotas.length} mascotas ·{' '}
            {
              mascotas.filter(
                (mascota) => mascota.activa,
              ).length
            }{' '}
            activas
          </p>
        </div>

        <div className="mascotas-acciones-header">
          <div className="mascotas-tabs">
            <button
              type="button"
              className={
                soloActivas ? 'tab tab-activo' : 'tab'
              }
              onClick={() => setSoloActivas(true)}
            >
              Activas
            </button>

            <button
              type="button"
              className={
                !soloActivas ? 'tab tab-activo' : 'tab'
              }
              onClick={() => setSoloActivas(false)}
            >
              Todas
            </button>
          </div>

          <Boton
            type="button"
            onClick={() =>
              setFormularioAbierto(
                (abierto) => !abierto,
              )
            }
          >
            + Registrar mascota
          </Boton>
        </div>
      </div>

      {formularioAbierto && (
        <FormularioMascota
          onGuardar={agregarMascota}
          onCancelar={() =>
            setFormularioAbierto(false)
          }
        />
      )}

      {mensajeExito && (
        <div className="mascotas-mensaje mascotas-mensaje-exito">
          {mensajeExito}
        </div>
      )}

      {errorAccion && (
        <div className="mascotas-mensaje mascotas-mensaje-error">
          {errorAccion}
        </div>
      )}

      {cargando && (
        <div className="mascotas-mensaje">
          Cargando mascotas...
        </div>
      )}

      {!cargando && error && (
        <div className="mascotas-mensaje mascotas-mensaje-error">
          {error}
        </div>
      )}

      {!cargando &&
        !error &&
        mascotasVisibles.length === 0 && (
          <div className="mascotas-mensaje">
            No hay mascotas para mostrar.
          </div>
        )}

      {!cargando &&
        !error &&
        mascotasVisibles.length > 0 && (
          <div className="mascotas-grid">
            {mascotasVisibles.map((mascota) => (
              <MascotaCard
                key={mascota.id}
                mascota={mascota}
                onCambiarEstado={() =>
                  cambiarEstadoMascota(mascota)
                }
                cambiandoEstado={
                  idMascotaCambiandoEstado === mascota.id
                }
              />
            ))}
          </div>
        )}
    </section>
  )
}

export default ListaMascotasPage