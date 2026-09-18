from sqlalchemy import text


class MeRepository:
    def __init__(self, session):
        self.session = session

    def buscar_por_id(
        self,
        id_usuario: int,
    ):
        consulta = text(
            """
            SELECT
                id_usuario,
                nombre,
                apellido,
                correo,
                estado
            FROM usuario
            WHERE id_usuario = :id_usuario
            """
        )

        fila = self.session.execute(
            consulta,
            {
                "id_usuario": id_usuario,
            },
        ).mappings().first()

        if fila is None:
            return None

        return dict(fila)