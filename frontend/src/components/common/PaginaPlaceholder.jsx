import './PaginaPlaceholder.css'

// Placeholder genérico para pantallas todavía sin implementar.
function PaginaPlaceholder({ titulo, descripcion }) {
  return (
    <section className="placeholder">
      <h1 className="placeholder-titulo">{titulo}</h1>
      <p className="placeholder-descripcion">{descripcion}</p>
    </section>
  )
}

export default PaginaPlaceholder
