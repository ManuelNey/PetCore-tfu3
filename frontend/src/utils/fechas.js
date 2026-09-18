export function calcularEdad(fechaNacimiento) {
  if (!fechaNacimiento) {
    return null
  }

  const nacimiento = new Date(`${fechaNacimiento}T00:00:00`)
  const hoy = new Date()

  let edad = hoy.getFullYear() - nacimiento.getFullYear()

  const todaviaNoCumplio =
    hoy.getMonth() < nacimiento.getMonth() ||
    (hoy.getMonth() === nacimiento.getMonth() && hoy.getDate() < nacimiento.getDate())

  if (todaviaNoCumplio) {
    edad -= 1
  }

  return `${edad} ${edad === 1 ? 'año' : 'años'}`
}

export function formatearFechaCorta(fecha) {
  if (!fecha) {
    return '—'
  }

  const [anio, mes, dia] = fecha.split('-')

  return `${dia}/${mes}/${anio}`
}
