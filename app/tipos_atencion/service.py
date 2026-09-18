from app.tipos_atencion.dto import TipoAtencionCreate
from app.tipos_atencion.repository import TipoAtencionRepository


class TipoAtencionService:
    def __init__(self, repository: TipoAtencionRepository):
        self.repository = repository

    # GET
    def listar(self):
        return self.repository.listar()

    # POST
    def crear(self, datos: TipoAtencionCreate):
        nombre_limpio = datos.nombre.strip()

        if nombre_limpio == "":
            raise ValueError(
                "El nombre no puede estar vacío."
            )

        tipo_existente = self.repository.buscar_por_nombre(
            nombre_limpio
        )

        if tipo_existente is not None:
            raise ValueError(
                "Ya existe un tipo de atención con ese nombre."
            )

        return self.repository.crear(
            nombre=nombre_limpio,
            descripcion=datos.descripcion,
            duracion_minutos=datos.duracion_minutos,
            reservable_cliente=datos.reservable_cliente,
        )
