import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.config import settings


logger = logging.getLogger(__name__)


class Cache:
    """
    Administra el acceso al cache compartido de Redis.
    """

    def __init__(self) -> None:
        self.client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    def obtener(
        self,
        clave: str,
    ) -> Any | None:
        """
        Busca una clave en Redis.
        """
        try:
            contenido = self.client.get(clave)

            if contenido is None:
                logger.info(
                    "CACHE MISS: %s",
                    clave,
                )

                return None

            logger.info(
                "CACHE HIT: %s",
                clave,
            )

            return json.loads(contenido)

        except json.JSONDecodeError:
            logger.warning(
                "El contenido de %s no es JSON valido.",
                clave,
            )

            self.eliminar(clave)

            return None

        except RedisError as error:
            logger.warning(
                "No se pudo consultar Redis: %s",
                error,
            )

            return None

    def guardar(
        self,
        clave: str,
        valor: Any,
    ) -> None:
        """
        Guarda un valor en Redis utilizando JSON.
        """
        try:
            contenido = json.dumps(
                valor,
                ensure_ascii=False,
            )

            self.client.set(
                name=clave,
                value=contenido,
                ex=settings.CACHE_TTL_SECONDS,
            )

            logger.info(
                "CACHE SET: %s",
                clave,
            )

        except (RedisError, TypeError) as error:
            logger.warning(
                "No se pudo guardar %s en Redis: %s",
                clave,
                error,
            )

    def eliminar(
        self,
        clave: str,
    ) -> None:
        """
        Elimina una clave de Redis.
        """
        try:
            self.client.delete(clave)

            logger.info(
                "CACHE DELETE: %s",
                clave,
            )

        except RedisError as error:
            logger.warning(
                "No se pudo eliminar %s de Redis: %s",
                clave,
                error,
            )


cache = Cache()