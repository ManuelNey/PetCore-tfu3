import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Stepper from '../../../components/common/Stepper'
import { useAuth } from '../../../app/AuthContext'
import { crearTurno } from '../../../api/turnos'
import { inicioDeHoy, sumarDias } from '../utils/fecha'
import PasoMascota from '../components/PasoMascota'
import PasoTipoAtencion from '../components/PasoTipoAtencion'
import PasoVeterinario from '../components/PasoVeterinario'
import PasoHorario from '../components/PasoHorario'
import PasoConfirmar from '../components/PasoConfirmar'
import './ReservarTurnoPage.css'

const PASOS = ['Mascota', 'Tipo de atención', 'Veterinario', 'Horario']

function ReservarTurnoPage() {
  const navigate = useNavigate()
  const { token } = useAuth()

  const [pasoActual, setPasoActual] = useState(1)
  const [mascota, setMascota] = useState(null)
  const [tipoAtencion, setTipoAtencion] = useState(null)
  const [veterinario, setVeterinario] = useState(null)
  const [horario, setHorario] = useState(null)
  const [fecha, setFecha] = useState(inicioDeHoy)
  const [confirmando, setConfirmando] = useState(false)
  const [errorConfirmacion, setErrorConfirmacion] = useState(null)

  function elegirTipoAtencion(tipo) {
    setTipoAtencion(tipo)
    setHorario(null)
  }

  function elegirVeterinario(vet) {
    setVeterinario(vet)
    setHorario(null)
  }

  function cambiarFecha(cantidadDias) {
    setFecha((actual) => sumarDias(actual, cantidadDias))
  }

  function elegirHorario(nuevoHorario) {
    setHorario(nuevoHorario)
    setErrorConfirmacion(null)
  }

  async function confirmarTurno() {
    setConfirmando(true)
    setErrorConfirmacion(null)

    try {
      await crearTurno(token, {
        idMascota: mascota.id_mascota,
        idTipoAtencion: tipoAtencion.id_tipo_atencion,
        idVeterinario: veterinario.id_usuario,
        fecha: horario.fecha,
        horaInicio: horario.inicio,
      })
      navigate('/turnos')
    } catch (error) {
      if (error.horarioNoDisponible) {
        // Otro cliente se adelantó: volvemos al paso de horario para que
        // elija de nuevo, sin perder mascota/tipo/veterinario ya elegidos.
        setHorario(null)
        setPasoActual(4)
      }
      setErrorConfirmacion(error.message)
    } finally {
      setConfirmando(false)
    }
  }

  return (
    <section className="reservar-page">
      <h1>Reservar un turno</h1>

      <div className="reservar-stepper">
        <Stepper pasos={PASOS} pasoActual={pasoActual} />
      </div>

      {pasoActual === 1 && (
        <PasoMascota seleccionada={mascota} onSeleccionar={setMascota} onContinuar={() => setPasoActual(2)} />
      )}

      {pasoActual === 2 && (
        <PasoTipoAtencion
          seleccionado={tipoAtencion}
          onSeleccionar={elegirTipoAtencion}
          onContinuar={() => setPasoActual(3)}
          onVolver={() => setPasoActual(1)}
        />
      )}

      {pasoActual === 3 && (
        <PasoVeterinario
          seleccionado={veterinario}
          onSeleccionar={elegirVeterinario}
          onContinuar={() => setPasoActual(4)}
          onVolver={() => setPasoActual(2)}
        />
      )}

      {pasoActual === 4 && (
        <PasoHorario
          mascota={mascota}
          tipoAtencion={tipoAtencion}
          veterinario={veterinario}
          fecha={fecha}
          onCambiarFecha={cambiarFecha}
          seleccionado={horario}
          onSeleccionar={elegirHorario}
          onContinuar={() => setPasoActual(5)}
          onVolver={() => setPasoActual(3)}
          error={errorConfirmacion}
        />
      )}

      {pasoActual === 5 && (
        <PasoConfirmar
          mascota={mascota}
          tipoAtencion={tipoAtencion}
          veterinario={veterinario}
          horario={horario}
          confirmando={confirmando}
          error={errorConfirmacion}
          onVolver={() => setPasoActual(4)}
          onConfirmar={confirmarTurno}
        />
      )}
    </section>
  )
}

export default ReservarTurnoPage
