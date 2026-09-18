import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../../../app/AuthContext'
import { obtenerHistorial, obtenerMascota } from '../../../api/historial'
import { listarTiposAtencion } from '../../../api/catalogos'
import Boton from '../../../components/common/Boton'
import Badge from '../../../components/common/Badge'
import { calcularEdad, formatearFechaCorta } from '../../../utils/fechas'
import './HistorialMascotaPage.css'

const LIMITE_INICIAL = 10
const INCREMENTO_PAGINACION = 10

function Campo({ etiqueta, valor }) {
  if (!valor) {
    return null
  }

  return (
    <div className="historial-campo">
      <span className="historial-campo-etiqueta">{etiqueta}</span>
      <p className="historial-campo-valor">{valor}</p>
    </div>
  )
}

function EncabezadoConsulta({ tipo, fecha, hora, veterinario }) {
  return (
    <div className="historial-consulta-encabezado">
      <h3>{tipo}</h3>
      <span className="historial-consulta-meta">
        {formatearFechaCorta(fecha)} · {hora} · {veterinario}
      </span>
    </div>
  )
}

function EstadoBadges({ modificadaEl, edicionVencida }) {
  if (!modificadaEl && !edicionVencida) {
    return null
  }

  return (
    <div className="historial-badges">
      {modificadaEl && (
        <Badge variant="neutral">
          Modificada el {formatearFechaCorta(modificadaEl.slice(0, 10))}
        </Badge>
      )}
      {edicionVencida && <Badge variant="inactiva">Cerrada · edición vencida</Badge>}
    </div>
  )
}

// --- Vista del cliente: solo lectura ---

function ConsultaCliente({ consulta }) {
  return (
    <article className="historial-tarjeta">
      <EncabezadoConsulta
        tipo={consulta.tipo}
        fecha={consulta.fecha}
        hora={consulta.hora}
        veterinario={consulta.veterinario}
      />

      <EstadoBadges
        modificadaEl={consulta.modificada_el}
        edicionVencida={consulta.edicion_vencida}
      />

      {consulta.corregida && (
        <p className="historial-nota-correccion">
          Corregida el {formatearFechaCorta(consulta.corregida_el)}.
        </p>
      )}

      <div className="historial-campos">
        <Campo etiqueta="Motivo" valor={consulta.motivo} />
        <Campo etiqueta="Diagnóstico" valor={consulta.diagnostico} />
        <Campo etiqueta="Tratamiento" valor={consulta.tratamiento} />
        <Campo etiqueta="Recomendaciones" valor={consulta.recomendaciones} />
      </div>
    </article>
  )
}

function VistaCliente({ idMascota, token }) {
  const [mascota, setMascota] = useState(null)
  const [historial, setHistorial] = useState(null)
  const [limite, setLimite] = useState(LIMITE_INICIAL)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controlador = new AbortController()

    setCargando(true)
    setError('')

    Promise.all([
      obtenerMascota(token, idMascota, controlador.signal),
      obtenerHistorial(token, idMascota, { limite, offset: 0 }, controlador.signal),
    ])
      .then(([mascotaInfo, historialInfo]) => {
        setMascota(mascotaInfo)
        setHistorial(historialInfo)
      })
      .catch((errorPeticion) => {
        if (errorPeticion.name !== 'AbortError') {
          setError(errorPeticion.message || 'No se pudo cargar el historial.')
        }
      })
      .finally(() => {
        if (!controlador.signal.aborted) {
          setCargando(false)
        }
      })

    return () => controlador.abort()
  }, [idMascota, token, limite])

  if (cargando) {
    return <div className="historial-mensaje">Cargando historial...</div>
  }

  if (error) {
    return <div className="historial-mensaje historial-mensaje-error">{error}</div>
  }

  const consultas = historial?.consultas ?? []
  const total = historial?.total ?? 0
  const quedanMasConsultas = consultas.length < total

  return (
    <section className="historial-page">
      <p className="historial-breadcrumb">
        <Link to="/mascotas">Mis mascotas</Link> · {mascota.nombre} · Historial clínico
      </p>

      <div className="historial-encabezado">
        <div className="historial-encabezado-titulo">
          <div className="historial-foto">foto</div>

          <div>
            <h1>Historial de {mascota.nombre}</h1>
            <p className="historial-subtitulo">
              {mascota.especie} · {mascota.raza ?? 'Sin especificar'} ·{' '}
              {calcularEdad(mascota.fecha_nacimiento) ?? '—'} · {total}{' '}
              {total === 1 ? 'consulta registrada' : 'consultas registradas'}
            </p>
          </div>
        </div>

        <Badge variant="neutral">Solo lectura</Badge>
      </div>

      <div className="historial-aviso">
        <span className="historial-aviso-punto" />
        <p>
          Registro elaborado por los veterinarios de la clínica. No se puede modificar desde tu
          cuenta. Ante dudas sobre un diagnóstico o tratamiento, consultá en la próxima visita.
        </p>
      </div>

      {consultas.length === 0 && (
        <div className="historial-mensaje">Todavía no hay consultas registradas.</div>
      )}

      <div className="historial-lista">
        {consultas.map((consulta) => (
          <ConsultaCliente key={consulta.id_consulta} consulta={consulta} />
        ))}
      </div>

      {quedanMasConsultas && (
        <button
          type="button"
          className="historial-ver-mas"
          onClick={() => setLimite((actual) => actual + INCREMENTO_PAGINACION)}
        >
          Ver {total - consultas.length} consultas anteriores
        </button>
      )}
    </section>
  )
}

// --- Vista del veterinario: historial completo con correcciones ---

function CorreccionItem({ correccion }) {
  return (
    <div className="historial-correccion-bloque">
      <div className="historial-correccion-encabezado">
        <span>{formatearFechaCorta(correccion.fecha)} {correccion.hora}</span>
        <Badge variant={correccion.vigente ? 'activa' : 'neutral'}>
          {correccion.vigente ? 'Corrección vigente' : 'Corrección anterior'}
        </Badge>
      </div>

      <p className="historial-correccion-motivo">{correccion.motivo_correccion}</p>

      <div className="historial-campos">
        <Campo etiqueta="Diagnóstico" valor={correccion.diagnostico} />
        <Campo etiqueta="Observaciones" valor={correccion.observaciones} />
        <Campo etiqueta="Tratamiento" valor={correccion.tratamiento} />
        <Campo etiqueta="Recomendaciones" valor={correccion.recomendaciones} />
      </div>

      <p className="historial-correccion-autor">Autor: {correccion.veterinario}</p>
    </div>
  )
}

function ConsultaVeterinario({ consulta }) {
  if (!consulta.recuperada) {
    return (
      <article className="historial-tarjeta historial-tarjeta-no-recuperada">
        <p>
          <strong>Consulta no recuperada.</strong>{' '}
          {consulta.mensaje ?? 'Existe en el registro pero no se pudo leer su contenido.'}
        </p>
      </article>
    )
  }

  return (
    <article className="historial-tarjeta">
      <div className="historial-consulta-encabezado">
        <EncabezadoConsulta
          tipo={consulta.tipo}
          fecha={consulta.fecha}
          hora={consulta.hora}
          veterinario={consulta.veterinario}
        />
      </div>

      <EstadoBadges
        modificadaEl={consulta.corregida ? null : consulta.modificada_el}
        edicionVencida={consulta.edicion_vencida}
      />

      <div className="historial-campos historial-campos-dos-columnas">
        <Campo etiqueta="Motivo" valor={consulta.motivo} />
        <Campo etiqueta="Observaciones" valor={consulta.observaciones} />
        <Campo etiqueta="Diagnóstico" valor={consulta.diagnostico} />
        <Campo etiqueta="Tratamiento" valor={consulta.tratamiento} />
        <Campo etiqueta="Recomendaciones" valor={consulta.recomendaciones} />
      </div>

      {consulta.corregida && consulta.correcciones.length > 0 && (
        <div className="historial-correcciones">
          <p className="historial-correcciones-titulo">
            Consulta corregida · la versión original y su corrección se muestran siempre juntas
          </p>

          {consulta.correcciones.map((correccion) => (
            <CorreccionItem key={correccion.id} correccion={correccion} />
          ))}
        </div>
      )}
    </article>
  )
}

function VistaVeterinario({ idMascota, token }) {
  const [historial, setHistorial] = useState(null)
  const [tipo, setTipo] = useState('')
  const [tiposAtencion, setTiposAtencion] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    listarTiposAtencion(token)
      .then(setTiposAtencion)
      .catch(() => {})
  }, [token])

  useEffect(() => {
    const controlador = new AbortController()

    setCargando(true)
    setError('')

    obtenerHistorial(token, idMascota, { tipo: tipo || undefined }, controlador.signal)
      .then(setHistorial)
      .catch((errorPeticion) => {
        if (errorPeticion.name !== 'AbortError') {
          setError(errorPeticion.message || 'No se pudo cargar el historial.')
        }
      })
      .finally(() => {
        if (!controlador.signal.aborted) {
          setCargando(false)
        }
      })

    return () => controlador.abort()
  }, [idMascota, token, tipo, intento])

  if (cargando) {
    return <div className="historial-mensaje">Cargando historial...</div>
  }

  if (error) {
    return <div className="historial-mensaje historial-mensaje-error">{error}</div>
  }

  const mascota = historial.mascota
  const consultas = historial.consultas ?? []

  return (
    <section className="historial-page">
      {!historial.consistente && (
        <div className="historial-alerta-inconsistente">
          <div className="historial-alerta-inconsistente-encabezado">
            <div>
              <strong>⚠ Historial incompleto — no lo tomes como válido</strong>
              <p>
                {historial.advertencias.join(' ') ||
                  'No se pudieron recuperar todas las consultas de esta mascota.'}{' '}
                Lo que ves abajo es un fragmento parcial: no sirve para decidir un diagnóstico ni
                un tratamiento.
              </p>
            </div>

            <Boton type="button" onClick={() => setIntento((actual) => actual + 1)}>
              Reintentar carga
            </Boton>
          </div>

          <p className="historial-alerta-resumen">
            Vista parcial · {historial.recuperadas} de {historial.esperadas} consultas · último
            intento{' '}
            {new Date(historial.ultimo_intento).toLocaleTimeString('es-UY', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>
      )}

      <p className="historial-breadcrumb">
        <Link to="/pacientes">Pacientes</Link> · {mascota.nombre} · Historial clínico
      </p>

      <div className="historial-encabezado">
        <div className="historial-encabezado-titulo">
          <div className="historial-foto">foto</div>

          <div>
            <h1>{mascota.nombre} · Historial clínico</h1>
            <p className="historial-subtitulo">
              {mascota.especie} · {mascota.raza ?? 'Sin especificar'} ·{' '}
              {calcularEdad(mascota.fecha_nacimiento) ?? '—'}
              {mascota.peso_actual != null && ` · ${mascota.peso_actual} kg`} · Propietaria:{' '}
              {mascota.propietario} · {mascota.telefono}
            </p>
          </div>
        </div>

        <div className="historial-acciones">
          <select
            className="historial-filtro-tipo"
            value={tipo}
            onChange={(evento) => setTipo(evento.target.value)}
          >
            <option value="">Filtrar por tipo</option>
            {tiposAtencion.map((tipoAtencion) => (
              <option key={tipoAtencion.id_tipo_atencion} value={tipoAtencion.nombre}>
                {tipoAtencion.nombre}
              </option>
            ))}
          </select>

          <Boton type="button" disabled title="Se registra desde el turno en Mi agenda">
            + Registrar consulta
          </Boton>
        </div>
      </div>

      {consultas.length === 0 && (
        <div className="historial-mensaje">No hay consultas registradas para este filtro.</div>
      )}

      <div className="historial-lista">
        {consultas.map((consulta, indice) => (
          <ConsultaVeterinario key={consulta.id ?? `faltante-${indice}`} consulta={consulta} />
        ))}
      </div>
    </section>
  )
}

function HistorialMascotaPage() {
  const { idMascota } = useParams()
  const { token, usuario } = useAuth()
  const esVeterinario = usuario.rol.toLowerCase() === 'veterinario'

  return esVeterinario ? (
    <VistaVeterinario idMascota={idMascota} token={token} />
  ) : (
    <VistaCliente idMascota={idMascota} token={token} />
  )
}

export default HistorialMascotaPage
