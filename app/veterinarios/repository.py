from sqlalchemy import text
from sqlalchemy.orm import Session


class VeterinarioRepository:
    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def obtener_veterinarios_activos(self):
        consulta = text(
            """
            SELECT u.id_usuario, u.nombre, u.apellido, v.matricula_profesional
            FROM veterinario v
            JOIN usuario u ON u.id_usuario = v.id_usuario
            WHERE u.estado = 'ACTIVO'
            """
        )
        return self.session.execute(consulta).mappings().all()
    