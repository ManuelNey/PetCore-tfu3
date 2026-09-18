const DIAS_CORTOS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
const DIAS_LARGOS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

export function inicioDeHoy() {
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  return hoy
}

export function sumarDias(fecha, cantidad) {
  const copia = new Date(fecha)
  copia.setDate(copia.getDate() + cantidad)
  return copia
}

export function esMismoDia(a, b) {
  return aISO(a) === aISO(b)
}

// Formato para mandar al backend: YYYY-MM-DD.
export function aISO(fecha) {
  const anio = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

// "Mar 25 · agosto 2026", para el navegador de fecha.
export function etiquetaFecha(fecha) {
  return `${DIAS_CORTOS[fecha.getDay()]} ${fecha.getDate()} · ${MESES[fecha.getMonth()]} ${fecha.getFullYear()}`
}

// "Martes 25/08/2026", para el resumen de la selección.
export function etiquetaFechaLarga(fecha) {
  const dd = String(fecha.getDate()).padStart(2, '0')
  const mm = String(fecha.getMonth() + 1).padStart(2, '0')
  return `${DIAS_LARGOS[fecha.getDay()]} ${dd}/${mm}/${fecha.getFullYear()}`
}

// Igual que etiquetaFechaLarga pero a partir de un string "YYYY-MM-DD"
// (evita el corrimiento de día de `new Date(iso)`, que interpreta UTC).
export function etiquetaFechaLargaISO(fechaISO) {
  const [anio, mes, dia] = fechaISO.split('-').map(Number)
  return etiquetaFechaLarga(new Date(anio, mes - 1, dia))
}

// Suma minutos a una hora "HH:MM" y devuelve "HH:MM".
export function sumarMinutos(horaHHMM, minutos) {
  const [horas, mins] = horaHHMM.split(':').map(Number)
  const total = horas * 60 + mins + minutos
  const hh = String(Math.floor(total / 60) % 24).padStart(2, '0')
  const mm = String(total % 60).padStart(2, '0')
  return `${hh}:${mm}`
}
