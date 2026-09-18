// Etiqueta tipo pill reutilizable (estado de mascota, rol, etc.)
function Badge({ variant = 'neutral', children }) {
  return <span className={`badge badge-${variant}`}>{children}</span>
}

export default Badge
