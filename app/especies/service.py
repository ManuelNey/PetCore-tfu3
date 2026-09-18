from app.especies.repository import EspecieRepository


class EspecieService:
    def __init__(self, repository: EspecieRepository):
        self.repository = repository

    def listar_activas(self):
        return self.repository.listar_activas()
