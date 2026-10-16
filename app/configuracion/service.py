import logging
from dataclasses import dataclass

from app.config import settings
from app.configuracion.repository import ConfiguracionRepository

logger = logging.getLogger(__name__)


class ClaveDesconocidaError(LookupError):
    pass


class ValorInvalidoError(ValueError):
    pass


@dataclass(frozen=True)
class ParametroEntero:
    minimo: int
    maximo: int
    # Respaldo: lo que dicen las variables de entorno (app/config.py).
    por_defecto: int


# Únicos parámetros que se pueden consultar y cambiar en caliente. Los
# límites son los mismos que ya valida Settings en app/config.py, así un
# valor guardado en la base nunca puede ser más permisivo que el del arranque.
PARAMETROS: dict[str, ParametroEntero] = {
    "LOGIN_MAX_INTENTOS": ParametroEntero(
        minimo=3,
        maximo=10,
        por_defecto=settings.LOGIN_MAX_INTENTOS,
    ),
    "LOGIN_BLOQUEO_MINUTOS": ParametroEntero(
        minimo=1,
        maximo=1440,
        por_defecto=settings.LOGIN_BLOQUEO_MINUTOS,
    ),
}


class ConfiguracionService:
    def __init__(self, repository: ConfiguracionRepository):
        self.repository = repository

    # GET /admin/configuracion
    def listar(self) -> list[dict]:
        return [self.obtener(clave) for clave in PARAMETROS]

    # GET /admin/configuracion/{clave}
    def obtener(self, clave: str) -> dict:
        parametro = self._parametro(clave)

        fila = self.repository.obtener(clave)

        if fila is None:
            # Falta la fila: se informa el valor de respaldo que está en uso.
            return {
                "clave": clave,
                "valor": str(parametro.por_defecto),
                "fecha_modificacion": None,
                "id_usuario_modificador": None,
            }

        return fila

    # PUT /admin/configuracion/{clave}
    def actualizar(
        self,
        clave: str,
        valor: int | str,
        id_usuario: int,
    ) -> dict:
        parametro = self._parametro(clave)

        numero = self._a_entero(valor)

        if not parametro.minimo <= numero <= parametro.maximo:
            raise ValorInvalidoError(
                f"{clave} debe estar entre "
                f"{parametro.minimo} y {parametro.maximo}."
            )

        return self.repository.guardar(
            clave=clave,
            valor=str(numero),
            id_usuario_modificador=id_usuario,
        )

    # Lo usa el login. Siempre devuelve un número válido: si el almacén no
    # responde o el valor guardado no sirve, usa el respaldo del entorno para
    # que un problema de configuración nunca impida iniciar sesión.
    def obtener_entero(self, clave: str) -> int:
        parametro = self._parametro(clave)

        try:
            valor = self.repository.obtener_valor(clave)
        except Exception:
            logger.warning(
                "No se pudo leer %s de la tabla configuracion; "
                "se usa el valor del entorno (%s).",
                clave,
                parametro.por_defecto,
                exc_info=True,
            )
            return parametro.por_defecto

        if valor is None:
            return parametro.por_defecto

        try:
            numero = int(valor)
        except ValueError:
            numero = None

        if numero is None or not parametro.minimo <= numero <= parametro.maximo:
            logger.warning(
                "Valor inválido para %s (%r); se usa el del entorno (%s).",
                clave,
                valor,
                parametro.por_defecto,
            )
            return parametro.por_defecto

        return numero

    def _parametro(self, clave: str) -> ParametroEntero:
        parametro = PARAMETROS.get(clave)

        if parametro is None:
            raise ClaveDesconocidaError(
                f"El parámetro {clave} no existe."
            )

        return parametro

    def _a_entero(self, valor: int | str) -> int:
        try:
            return int(str(valor).strip())
        except ValueError as error:
            raise ValorInvalidoError(
                "El valor debe ser un número entero."
            ) from error