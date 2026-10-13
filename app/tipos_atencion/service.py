from app.cache import Cache
from app.tipos_atencion.dto import TipoAtencionCreate
from app.tipos_atencion.repository import (
    TipoAtencionRepository,
)


CLAVE_TIPOS_ATENCION = "tipos_atencion:listado"


class TipoAtencionService:
    def __init__(
        self,
        repository: TipoAtencionRepository,
        cache: Cache,
    ):
        self.repository = repository
        self.cache = cache

    # GET
    def listar(self):
        tipos_cache = self.cache.obtener(
            CLAVE_TIPOS_ATENCION
        )

        # Si existe en Redis, se devuelve directamente.
        if tipos_cache is not None:
            return tipos_cache

        # Si no existe, se consulta PostgreSQL.
        tipos_atencion = self.repository.listar()

        # Se guarda el resultado en Redis.
        self.cache.guardar(
            clave=CLAVE_TIPOS_ATENCION,
            valor=tipos_atencion,
        )

        return tipos_atencion

    # POST
    def crear(
        self,
        datos: TipoAtencionCreate,
    ):
        nombre_limpio = datos.nombre.strip()

        if nombre_limpio == "":
            raise ValueError(
                "El nombre no puede estar vacío."
            )

        tipo_existente = (
            self.repository.buscar_por_nombre(
                nombre_limpio
            )
        )

        if tipo_existente is not None:
            raise ValueError(
                "Ya existe un tipo de atención "
                "con ese nombre."
            )

        tipo_creado = self.repository.crear(
            nombre=nombre_limpio,
            descripcion=datos.descripcion,
            duracion_minutos=(
                datos.duracion_minutos
            ),
            reservable_cliente=(
                datos.reservable_cliente
            ),
        )

        # El POST modificó PostgreSQL.
        # La lista guardada en Redis quedó desactualizada.
        self.cache.eliminar(
            CLAVE_TIPOS_ATENCION
        )

        return tipo_creado