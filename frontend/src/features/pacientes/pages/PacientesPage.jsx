import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../../app/AuthContext'
import { listarPacientes } from '../../../api/pacientes'
import Badge from '../../../components/common/Badge'
import Boton from '../../../components/common/Boton'
import './PacientesPage.css'

function TarjetaPaciente({ paciente }) {
  return (
    <article className="paciente-card">
      <div className="paciente-card-encabezado">
        <div className="paciente-foto">foto</div>

        <div className="paciente-card-titulo">
          <div className="paciente-nombre">{paciente.nombre}</div>
          <div className="paciente-especie">
            {paciente.especie} · {paciente.raza ?? 'Sin especificar'}
            {paciente.edad && ` · ${paciente.edad}`}
          </div>
        </div>

        <Badge variant={paciente.estado === 'ACTIVA' ? 'activa' : 'inactiva'}>
          {paciente.estado === 'ACTIVA' ? 'Activa' : 'Inactiva'}
        </Badge>
      </div>

      <p className="paciente-propietario">
        Propietario: {paciente.propietario.nombre} · {paciente.propietario.telefono}
      </p>

      <div className="paciente-datos">
        <div>
          <div className="paciente-dato-valor">{paciente.consultas_registradas}</div>
          Consultas registradas
        </div>

        <div>
          <div className="paciente-dato-valor">
            {paciente.ultima_atencion
              ? `${paciente.ultima_atencion.fecha} · ${
                  paciente.ultima_atencion.fue_propia ? 'por vos' : `por ${paciente.ultima_atencion.veterinario}`
                }`
              : 'Sin consultas'}
          </div>
          Última atención
        </div>

        <div>
          <div className="paciente-dato-valor">
            {paciente.turno_hoy ? `${paciente.turno_hoy.hora} hoy` : 'Sin turno hoy'}
          </div>
          Próximo turno
        </div>
      </div>

      <Boton as={Link} to={`/pacientes/${paciente.id}/historial`} className="paciente-boton">
        Ver historial clínico
      </Boton>
    </article>
  )
}

function PacientesPage() {
  const { token } = useAuth()

  const [pacientes, setPacientes] = useState([])
  const [alcance, setAlcance] = useState('clinica')
  const [busqueda, setBusqueda] = useState('')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controlador = new AbortController()

    setCargando(true)
    setError('')

    const temporizador = setTimeout(() => {
      listarPacientes(token, { q: busqueda, alcance }, controlador.signal)
        .then(setPacientes)
        .catch((errorPeticion) => {
          if (errorPeticion.name !== 'AbortError') {
            setError(errorPeticion.message || 'No se pudieron obtener los pacientes.')
          }
        })
        .finally(() => {
          if (!controlador.signal.aborted) {
            setCargando(false)
          }
        })
    }, 300)

    return () => {
      clearTimeout(temporizador)
      controlador.abort()
    }
  }, [token, alcance, busqueda])

  return (
    <section className="pacientes-page">
      <div className="pacientes-encabezado">
        <h1>Pacientes</h1>

        <div className="pacientes-filtros">
          <input
            type="search"
            className="pacientes-busqueda"
            placeholder="Buscar por nombre..."
            value={busqueda}
            onChange={(evento) => setBusqueda(evento.target.value)}
          />

          <div className="pacientes-tabs">
            <button
              type="button"
              className={alcance === 'mios' ? 'tab tab-activo' : 'tab'}
              onClick={() => setAlcance('mios')}
            >
              Mis pacientes
            </button>

            <button
              type="button"
              className={alcance === 'clinica' ? 'tab tab-activo' : 'tab'}
              onClick={() => setAlcance('clinica')}
            >
              Toda la clínica
            </button>
          </div>
        </div>
      </div>

      {cargando && <div className="pacientes-mensaje">Buscando pacientes...</div>}

      {!cargando && error && <div className="pacientes-mensaje pacientes-mensaje-error">{error}</div>}

      {!cargando && !error && pacientes.length === 0 && (
        <div className="pacientes-mensaje">No se encontraron pacientes.</div>
      )}

      {!cargando && !error && pacientes.length > 0 && (
        <div className="pacientes-grid">
          {pacientes.map((paciente) => (
            <TarjetaPaciente key={paciente.id} paciente={paciente} />
          ))}
        </div>
      )}
    </section>
  )
}

export default PacientesPage
