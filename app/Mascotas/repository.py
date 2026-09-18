from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_session


class MascotaRepository:
    """
    Administra las consultas de mascotas en la base de datos.
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa el repositorio.
            session: Sesion de SQLAlchemy utilizada para acceder
                a PostgreSQL.
        """
        self.session: Session = session

    def listar_por_cliente(
        self,
        id_cliente: int,
    ) -> list[dict[str, Any]]:
        """
        Busca las mascotas pertenecientes a un cliente.
            id_cliente: Identificador del cliente autenticado.

        Retorna lista de mascotas del cliente.
        """
        consulta = text(
            """
            SELECT
                m.id_mascota,
                m.nombre,
                m.especie,
                m.raza,
                m.fecha_nacimiento,
                m.sexo,
                m.observaciones,
                m.estado
            FROM mascota AS m
            INNER JOIN cliente AS c
                ON c.id_usuario = m.id_cliente
            WHERE c.id_usuario = :id_cliente
            ORDER BY m.nombre
            """
        )

        filas = self.session.execute(
            consulta,
            {
                "id_cliente": id_cliente,
            },
        ).mappings().all()

        mascotas: list[dict[str, Any]] = []

        for fila in filas:
            mascotas.append(dict(fila))

        return mascotas

    def crear(
        self,
        id_cliente: int,
        nombre: str,
        especie: str,
        raza: str | None,
        fecha_nacimiento=None,
    ) -> dict[str, Any]:
        """
        Registra una mascota para el cliente autenticado.
            id_cliente: Identificador del cliente autenticado.
            nombre: Nombre de la mascota.
            especie: Especie de la mascota.
            raza: Raza de la mascota.
            fecha_nacimiento: Fecha de nacimiento de la mascota.

        Return:
            Datos de la mascota registrada.

        Raises:
            LookupError: Si no existe el cliente.
        """
        consulta = text(
            """
            INSERT INTO mascota (
                id_cliente,
                nombre,
                especie,
                raza,
                fecha_nacimiento
            )
            SELECT
                c.id_usuario,
                :nombre,
                :especie,
                :raza,
                :fecha_nacimiento
            FROM cliente AS c
            WHERE c.id_usuario = :id_cliente
            RETURNING
                id_mascota,
                nombre,
                especie,
                raza,
                fecha_nacimiento,
                sexo,
                observaciones,
                estado
            """
        )

        valores: dict[str, Any] = {
            "id_cliente": id_cliente,
            "nombre": nombre,
            "especie": especie,
            "raza": raza,
            "fecha_nacimiento": fecha_nacimiento,
        }

        fila = self.session.execute(
            consulta,
            valores,
        ).mappings().first()

        if fila is None:
            raise LookupError(
                "No se encontro el cliente autenticado."
            )

        self.session.commit()

        return dict(fila)

    def obtener_mascota_por_id(self, id_mascota: int, id_cliente: int) -> dict[str, Any] | None:
        consulta = text(
            """
            SELECT id_mascota, nombre, especie, raza, fecha_nacimiento, sexo, observaciones, estado
            FROM mascota
            WHERE id_mascota = :id_mascota AND id_cliente = :id_cliente
            """
        )
        fila = self.session.execute(
            consulta,
            {"id_mascota": id_mascota, "id_cliente": id_cliente},
        ).mappings().first()

        return dict(fila) if fila else None

    def actualizar(self, id_mascota: int, id_cliente: int, datos: dict) -> dict[str, Any] | None:
        if not datos:
            return self.obtener_mascota_por_id(id_mascota, id_cliente)

        columnas = ", ".join(f"{campo} = :{campo}" for campo in datos)
        parametros = {**datos, "id_mascota": id_mascota, "id_cliente": id_cliente}

        consulta = text(
            f"""
            UPDATE mascota SET {columnas}
            WHERE id_mascota = :id_mascota AND id_cliente = :id_cliente
            RETURNING id_mascota, nombre, especie, raza, fecha_nacimiento, sexo, observaciones, estado
            """
        )
        fila = self.session.execute(consulta, parametros).mappings().first()
        self.session.commit()

        return dict(fila) if fila else None

    def cambiar_estado(self, id_mascota: int, id_cliente: int, estado: str,) -> dict[str, Any] | None:
        """
        Cambia el estado de una mascota del cliente autenticado.
            id_mascota: Identificador de la mascota.
            id_cliente: Identificador del cliente autenticado.
            estado: Nuevo estado de la mascota.

        Return:
            Datos actualizados de la mascota.
        """
        consulta = text(
            """
            UPDATE mascota
            SET estado = :estado
            WHERE id_mascota = :id_mascota
            AND id_cliente = :id_cliente
            RETURNING
                id_mascota,
                nombre,
                especie,
                raza,
                fecha_nacimiento,
                sexo,
                observaciones,
                estado
            """
        )

        fila = self.session.execute(
            consulta,
            {
                "id_mascota": id_mascota,
                "id_cliente": id_cliente,
                "estado": estado,
            },
        ).mappings().first()

        if fila is None:
            return None

        self.session.commit()

        return dict(fila)