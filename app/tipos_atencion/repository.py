from sqlalchemy import text


class TipoAtencionRepository:
    def __init__(self, session):
        self.session = session

    def listar(self):
        consulta = text(
            """
            SELECT
                id_tipo_atencion,
                nombre,
                descripcion,
                duracion_minutos,
                reservable_cliente,
                estado
            FROM tipo_atencion
            ORDER BY nombre
            """
        )
        filas = self.session.execute(consulta).mappings().all()

        tipos_atencion = []

        for fila in filas:
            tipos_atencion.append(dict(fila))

        return tipos_atencion

    # Antes de agregar un tipo de atencion, revisa si ya existe ese nombre
    def buscar_por_nombre(self, nombre: str):
        consulta = text(
            """
            SELECT
                id_tipo_atencion,
                nombre,
                descripcion,
                duracion_minutos,
                reservable_cliente,
                estado
            FROM tipo_atencion
            WHERE nombre = :nombre
            """
        )
        fila = self.session.execute(
            consulta,
            {"nombre": nombre},
        ).mappings().first()

        if fila is None:
            return None

        return dict(fila)

    def crear(
        self,
        nombre: str,
        descripcion: str | None,
        duracion_minutos: int,
        reservable_cliente: bool,
    ):
        consulta = text(
            """
            INSERT INTO tipo_atencion (
                nombre,
                descripcion,
                duracion_minutos,
                reservable_cliente
            )
            VALUES (
                :nombre,
                :descripcion,
                :duracion_minutos,
                :reservable_cliente
            )
            RETURNING
                id_tipo_atencion,
                nombre,
                descripcion,
                duracion_minutos,
                reservable_cliente,
                estado
            """
        )

        valores = {
            "nombre": nombre,
            "descripcion": descripcion,
            "duracion_minutos": duracion_minutos,
            "reservable_cliente": reservable_cliente,
        }

        fila = self.session.execute(
            consulta,
            valores,
        ).mappings().one()

        self.session.commit()

        return dict(fila)
