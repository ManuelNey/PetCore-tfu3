from app.cache import Cache
from app.especies.repository import EspecieRepository


CLAVE_ESPECIES_ACTIVAS = "especies:activas"


class EspecieService:
    def __init__(self, repository: EspecieRepository, cache: Cache,):
        self.repository = repository
        self.cache = cache

    def listar_activas(self):
        especies_cache = self.cache.obtener(
            CLAVE_ESPECIES_ACTIVAS
        )

        # Si existe en Redis, se devuelve directamente.
        if especies_cache is not None:
            return especies_cache

        # Si no existe, se consulta PostgreSQL.
        especies = self.repository.listar_activas()

        # Se guarda en Redis para las proximas consultas.
        self.cache.guardar(
            clave=CLAVE_ESPECIES_ACTIVAS,
            valor=especies,
        )

        return especies