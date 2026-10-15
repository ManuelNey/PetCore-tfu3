import logging
import time
from pathlib import Path
from uuid import UUID

from app.config import settings
from app.database import abrir_sesion_con_reintentos
from app.historial.exportacion_repository import ExportacionRepository
from app.historial.pdf import generar_pdf_historial
from app.historial.repository import HistorialRepository
from app.historial.service import HistorialService
from app.historial.valet_key import generar_valet_key, validar_valet_key

logger = logging.getLogger(__name__)


class TareaNoLista(Exception):
    """La tarea existe, pero el PDF todavía no está listo"""


def ruta_archivo(nombre_archivo: str) -> Path | None:
    """Devuelve dónde está guardado el PDF, o None si no existe."""
    ruta = Path(settings.EXPORTACIONES_DIR) / nombre_archivo
    return ruta if ruta.is_file() else None


class ExportacionService:
    def __init__(
        self,
        exportaciones: ExportacionRepository,
        historial: HistorialRepository,
    ) -> None:
        self.exportaciones = exportaciones
        self.historial = historial

    def iniciar(self, id_mascota: int, id_veterinario: int) -> UUID:
        """
        Revisa que la mascota exista y crea la tarea como PENDIENTE.

        Todavía no genera el PDF: eso se hace después de responder.
        """
        if not self.historial.obtener_info_mascota(id_mascota):
            raise LookupError("Mascota no encontrada.")

        return self.exportaciones.crear_tarea(id_mascota, id_veterinario)

    def consultar(self, id_tarea: UUID, id_veterinario: int) -> dict:
        tarea = self.exportaciones.obtener_tarea(id_tarea)

        # Si la tarea es de otro veterinario, respondemos como si no existiera.
        if tarea is None or tarea["id_usuario"] != id_veterinario:
            raise LookupError("Tarea de exportación no encontrada.")

        return tarea

    def enlace_descarga(self, tarea: dict) -> str | None:
        """Crea el enlace con el Valet Key, solo si el PDF ya está listo."""
        if tarea["estado"] != "LISTO" or ruta_archivo(tarea["archivo"]) is None:
            return None

        token = generar_valet_key(tarea["id_tarea"])
        return f"/historial/exportar/{tarea['id_tarea']}/descargar?token={token}"

    def archivo_para_descarga(self, id_tarea: UUID, token: str) -> Path:
        """Revisa el Valet Key y devuelve el PDF."""
        validar_valet_key(token, id_tarea)

        tarea = self.exportaciones.obtener_tarea(id_tarea)
        if tarea is None:
            raise LookupError("Tarea de exportación no encontrada.")
        if tarea["estado"] != "LISTO":
            raise TareaNoLista("El PDF todavía no está disponible.")

        ruta = ruta_archivo(tarea["archivo"])
        if ruta is None:
            raise LookupError("El archivo ya no está disponible.")

        return ruta


def generar_en_segundo_plano(id_tarea: UUID, id_mascota: int, id_veterinario: int) -> None:
    """
    Genera el PDF y marca la tarea como LISTO (o ERROR si algo falla).

    Se ejecuta después de responder al veterinario, por eso usa su propia
    conexión a la base de datos.
    """
    session = abrir_sesion_con_reintentos()
    exportaciones = ExportacionRepository(session)

    try:
        # Pausa solo para la demo (en un uso real es 0).
        time.sleep(settings.EXPORTACION_RETARDO_SEGUNDOS)

        historial = HistorialService(HistorialRepository(session)).obtener_historial_veterinario(
            id_mascota, id_veterinario, None
        )

        nombre_archivo = f"{id_tarea}.pdf"
        generar_pdf_historial(historial, Path(settings.EXPORTACIONES_DIR) / nombre_archivo)

        exportaciones.marcar_listo(id_tarea, nombre_archivo)
    except Exception:
        logger.exception("Exportación %s falló.", id_tarea)
        session.rollback()
        exportaciones.marcar_error(id_tarea, "No se pudo generar el PDF.")
    finally:
        session.close()
