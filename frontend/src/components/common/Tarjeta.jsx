// Panel blanco redondeado reutilizado como base de cards y bloques de contenido.
function Tarjeta({ className = '', children, ...props }) {
  return (
    <div className={`tarjeta ${className}`.trim()} {...props}>
      {children}
    </div>
  )
}

export default Tarjeta
