from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

estilos = getSampleStyleSheet()


def _texto(valor) -> str:
    """Convierte un dato en texto ('-' si está vacío)."""
    if valor is None or valor == "":
        return "-"
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    # Evita que símbolos como < o & rompan el PDF
    return escape(str(valor))


def _campo(etiqueta: str, valor, estilo="Normal") -> Paragraph:
    return Paragraph(f"<b>{etiqueta}:</b> {_texto(valor)}", estilos[estilo])


def generar_pdf_historial(historial: dict, destino: Path) -> None:
    """Arma el PDF con el historial de la mascota."""
    mascota = historial["mascota"]

    contenido = [
        Paragraph("Historial clínico", estilos["Title"]),
        _campo("Mascota", mascota["nombre"]),
        _campo("Especie", mascota["especie"]),
        _campo("Raza", mascota["raza"]),
        _campo("Propietario", mascota["propietario"]),
        _campo("Teléfono", mascota["telefono"]),
        Spacer(1, 12),
    ]

    for advertencia in historial["advertencias"]:
        contenido.append(_campo("Advertencia", advertencia))

    for consulta in historial["consultas"]:
        if not consulta["recuperada"]:
            contenido.append(Paragraph("Consulta no recuperada.", estilos["Heading3"]))
            continue

        titulo = f"{_texto(consulta['fecha'])} - {_texto(consulta['tipo'])}"
        if consulta["corregida"]:
            titulo += " (corregida)"
        contenido.append(Paragraph(titulo, estilos["Heading3"]))

        contenido.append(_campo("Veterinario", consulta["veterinario"]))
        contenido.append(_campo("Motivo", consulta["motivo"]))
        contenido.append(_campo("Diagnóstico", consulta["diagnostico"]))
        contenido.append(_campo("Observaciones", consulta["observaciones"]))
        contenido.append(_campo("Tratamiento", consulta["tratamiento"]))
        contenido.append(_campo("Recomendaciones", consulta["recomendaciones"]))

        for correccion in consulta["correcciones"]:
            contenido.append(_campo("Corrección", f"{_texto(correccion['fecha'])} - {correccion['motivo_correccion']}"))
            contenido.append(_campo("Diagnóstico corregido", correccion["diagnostico"]))

    destino.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(destino), pagesize=A4).build(contenido)
