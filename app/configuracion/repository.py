from sqlalchemy import text


class ConfiguracionRepository:
    def __init__(self, session):
        self.session = session

    def obtener(self, clave: str):
        """Fila completa de un parámetro, o None si no está en la tabla."""
        consulta = text(
            """
            SELECT
                clave,
                valor,
                fecha_modificacion,
                id_usuario_modificador
            FROM configuracion
            WHERE clave = :clave
            """
        )

        fila = self.session.execute(
            consulta,
            {"clave": clave},
        ).mappings().first()

        if fila is None:
            return None

        return dict(fila)

    def obtener_valor(self, clave: str) -> str | None:
        """Solo el valor. Lo usa el login en cada intento fallido."""
        try:
            return self.session.execute(
                text("SELECT valor FROM configuracion WHERE clave = :clave"),
                {"clave": clave},
            ).scalar()

        except Exception:
            self.session.rollback()
            raise

    def guardar(
        self,
        clave: str,
        valor: str,
        id_usuario_modificador: int,
    ):
        """Crea o actualiza el parámetro y deja registrado quién lo cambió."""
        consulta = text(
            """
            INSERT INTO configuracion (
                clave,
                valor,
                fecha_modificacion,
                id_usuario_modificador
            )
            VALUES (
                :clave,
                :valor,
                now(),
                :id_usuario_modificador
            )
            ON CONFLICT (clave) DO UPDATE
            SET
                valor = EXCLUDED.valor,
                fecha_modificacion = EXCLUDED.fecha_modificacion,
                id_usuario_modificador = EXCLUDED.id_usuario_modificador
            RETURNING
                clave,
                valor,
                fecha_modificacion,
                id_usuario_modificador
            """
        )

        try:
            fila = self.session.execute(
                consulta,
                {
                    "clave": clave,
                    "valor": valor,
                    "id_usuario_modificador": id_usuario_modificador,
                },
            ).mappings().one()

            self.session.commit()

            return dict(fila)

        except Exception:
            self.session.rollback()
            raise