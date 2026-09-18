from sqlalchemy import text


class EspecieRepository:
    def __init__(self, session):
        self.session = session

    def listar_activas(self):
        consulta = text(
            """
            SELECT id_especie, nombre, estado
            FROM especie
            WHERE estado = 'ACTIVO'
            ORDER BY nombre
            """
        )
        filas = self.session.execute(consulta).mappings().all()

        especies = []

        for fila in filas:
            especies.append(dict(fila))

        return especies
