from datetime import datetime

from sqlalchemy import text


class LoginRepository:
    def __init__(self, session):
        self.session = session

    def buscar_por_correo(self, correo: str):
        consulta = text(
            """
            SELECT
                u.id_usuario,
                u.nombre,
                u.apellido,
                u.correo,
                u.contrasena_hash,
                u.estado,
                u.intentos_inicio,
                u.bloqueado_hasta,

                CASE
                    WHEN c.id_usuario IS NOT NULL
                        THEN 'CLIENTE'
                    WHEN v.id_usuario IS NOT NULL
                        THEN 'VETERINARIO'
                    WHEN a.id_usuario IS NOT NULL
                        THEN 'ADMINISTRADOR'
                END AS rol

            FROM usuario AS u

            LEFT JOIN cliente AS c
                ON c.id_usuario = u.id_usuario

            LEFT JOIN veterinario AS v
                ON v.id_usuario = u.id_usuario

            LEFT JOIN administrador AS a
                ON a.id_usuario = u.id_usuario

            WHERE LOWER(TRIM(u.correo)) = :correo

            FOR UPDATE OF u
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

    def registrar_intento_fallido(
        self,
        id_usuario: int,
        correo: str,
        intentos_inicio: int,
        bloqueado_hasta: datetime | None,
        resultado: str,
    ):
        try:
            consulta = text(
                """
                UPDATE usuario
                SET
                    intentos_inicio = :intentos_inicio,
                    bloqueado_hasta = :bloqueado_hasta
                WHERE id_usuario = :id_usuario
                """
            )

            self.session.execute(
                consulta,
                {
                    "id_usuario": id_usuario,
                    "intentos_inicio": intentos_inicio,
                    "bloqueado_hasta": bloqueado_hasta,
                },
            )

            self._registrar_auditoria(
                id_usuario=id_usuario,
                correo=correo,
                resultado=resultado,
                detalle="Intento de inicio de sesión fallido.",
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

    def registrar_login_exitoso(
        self,
        id_usuario: int,
        correo: str,
    ):
        try:
            consulta = text(
                """
                UPDATE usuario
                SET
                    intentos_inicio = 0,
                    bloqueado_hasta = NULL
                WHERE id_usuario = :id_usuario
                """
            )

            self.session.execute(
                consulta,
                {
                    "id_usuario": id_usuario,
                },
            )

            self._registrar_auditoria(
                id_usuario=id_usuario,
                correo=correo,
                resultado="EXITOSO",
                detalle="Inicio de sesión exitoso.",
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

    def registrar_evento(
        self,
        correo: str,
        resultado: str,
        detalle: str,
        id_usuario: int | None = None,
    ):
        try:
            self._registrar_auditoria(
                id_usuario=id_usuario,
                correo=correo,
                resultado=resultado,
                detalle=detalle,
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

    def _registrar_auditoria(
        self,
        correo: str,
        resultado: str,
        detalle: str,
        id_usuario: int | None,
    ):
        consulta = text(
            """
            INSERT INTO auditoria_sistema (
                id_usuario_actor,
                correo_ingresado,
                id_usuario_afectado,
                accion,
                resultado,
                detalle
            )
            VALUES (
                :id_usuario_actor,
                :correo_ingresado,
                :id_usuario_afectado,
                'INICIO_SESION',
                :resultado,
                :detalle
            )
            """
        )

        self.session.execute(
            consulta,
            {
                "id_usuario_actor": id_usuario,
                "correo_ingresado": correo,
                "id_usuario_afectado": id_usuario,
                "resultado": resultado,
                "detalle": detalle,
            },
        )