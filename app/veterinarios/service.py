from app.veterinarios.repository import VeterinarioRepository


class VeterinarioService:
    def __init__(self, repository: VeterinarioRepository) -> None:
        """
        Inicializa el servicio.
            repository: Repositorio de veterinarios.
        """
        self.repository: VeterinarioRepository = repository

    def listar_veterinarios(self):
        """
        Devuelve la lista de veterinarios activos.
        """
        return [dict(v) for v in self.repository.obtener_veterinarios_activos()]