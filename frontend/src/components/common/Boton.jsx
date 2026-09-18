// Botón reutilizable: mismo estilo primario/secundario en toda la app.
// `as` permite renderizarlo como <button> (default) o como Link de router.
function Boton({ variant = 'primario', as: Componente = 'button', className = '', ...props }) {
  return <Componente className={`boton boton-${variant} ${className}`.trim()} {...props} />
}

export default Boton
