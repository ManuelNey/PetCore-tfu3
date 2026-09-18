from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


class RegisterRepository:
    def __init__(self, session):
        self.session = session

    def buscar_por_correo(
        self,
        correo: str,
    ):
        consulta = text(
            """
            SELECT id_usuario
            FROM usuario
            WHERE LOWER(correo) = :correo
            """
        )

        fila = self.session.execute(
            consulta,
            {
                "correo": correo,
            },
        ).mappings().first()

        if fila is None:
            return None

        return dict(fila)

    def buscar_por_documento(
        self,
        documento: str,
    ):
        consulta = text(
            """
            SELECT id_usuario
            FROM usuario
            WHERE documento = :documento
            """
        )

        fila = self.session.execute(
            consulta,
            {
                "documento": documento,
            },
        ).mappings().first()

        if fila is None:
            return None

        return dict(fila)

    def crear_cliente(
        self,
        nombre: str,
        apellido: str,
        documento: str,
        correo: str,
        telefono: str,
        contrasena_hash: str,
    ):
        try:
            consulta_usuario = text(
                """
                INSERT INTO usuario (
                    nombre,
                    apellido,
                    documento,
                    correo,
                    telefono,
                    contrasena_hash
                )
                VALUES (
                    :nombre,
                    :apellido,
                    :documento,
                    :correo,
                    :telefono,
                    :contrasena_hash
                )
                RETURNING
                    id_usuario,
                    nombre,
                    apellido,
                    documento,
                    correo,
                    telefono
                """
            )

            fila = self.session.execute(
                consulta_usuario,
                {
                    "nombre": nombre,
                    "apellido": apellido,
                    "documento": documento,
                    "correo": correo,
                    "telefono": telefono,
                    "contrasena_hash": contrasena_hash,
                },
            ).mappings().one()

            usuario = dict(fila)

            consulta_cliente = text(
                """
                INSERT INTO cliente (
                    id_usuario
                )
                VALUES (
                    :id_usuario
                )
                """
            )

            self.session.execute(
                consulta_cliente,
                {
                    "id_usuario": (
                        usuario["id_usuario"]
                    ),
                },
            )

            self.session.commit()

            usuario["rol"] = "CLIENTE"

            return usuario

        except IntegrityError:
            self.session.rollback()
            raise