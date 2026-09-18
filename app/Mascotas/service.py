from datetime import date
from typing import Any

from app.Mascotas.dto import MascotaCreate, MascotaUpdate
from app.Mascotas.repository import MascotaRepository
from fastapi import HTTPException


class MascotaService:
    """
    Contiene la lógica de negocio relacionada con las mascotas.
    """

    def __init__(
        self,
        repository: MascotaRepository,
    ) -> None:
        """
        Inicializa el servicio de mascotas.
            repository: Repositorio utilizado para gestionar
                las mascotas.
        """
        self.repository: MascotaRepository = repository

    def listar_por_cliente(
        self,
        id_cliente: int,
    ) -> list[dict[str, Any]]:
        """
        Solicita las mascotas del cliente autenticado.
            id_cliente: Identificador obtenido del token JWT.

        Returns:
            Lista de mascotas pertenecientes al cliente.

        Raises:
            ValueError: Si el identificador no es valido.
        """
        if id_cliente <= 0:
            raise ValueError(
                "El identificador del cliente no es valido."
            )

        return self.repository.listar_por_cliente(
            id_cliente
        )

    def crear(
        self,
        id_cliente: int,
        datos: MascotaCreate,
    ) -> dict[str, Any]:
        """
        Valida y registra una mascota.
            id_cliente: Identificador obtenido del token JWT.
            datos: Datos recibidos para registrar la mascota.

        Returns:
            Datos de la mascota registrada.

        Raises:
            ValueError: Si algun dato no es valido.
            LookupError: Si el cliente no existe.
        """
        nombre_limpio: str = datos.nombre.strip()
        especie_limpia: str = datos.especie.strip()

        raza_limpia: str | None = (
            datos.raza.strip()
            if datos.raza and datos.raza.strip()
            else None
        )

        if id_cliente <= 0:
            raise ValueError(
                "El identificador del cliente no es valido."
            )

        if nombre_limpio == "":
            raise ValueError(
                "El nombre de la mascota no puede estar vacio."
            )

        if especie_limpia == "":
            raise ValueError(
                "La especie de la mascota no puede estar vacia."
            )

        if (
            datos.fecha_nacimiento is not None
            and datos.fecha_nacimiento > date.today()
        ):
            raise ValueError(
                "La fecha de nacimiento no puede ser una fecha futura."
            )

        return self.repository.crear(
            id_cliente=id_cliente,
            nombre=nombre_limpio,
            especie=especie_limpia,
            raza=raza_limpia,
            fecha_nacimiento=datos.fecha_nacimiento,
        )

    def obtener_mascota_por_id(
        self,
        id_mascota: int,
        id_cliente: int,
    ) -> dict[str, Any]:
        """
        Obtiene una mascota por su identificador y el del cliente.
            id_mascota: Identificador de la mascota.
            id_cliente: Identificador del cliente autenticado.

        Returns:
            Datos de la mascota.
        Raises:
            HTTPException: Si la mascota no es encontrada.
        """
        mascota = self.repository.obtener_mascota_por_id(id_mascota, id_cliente)
        if not mascota:
            raise HTTPException(
                status_code=404,
                detail="Mascota no encontrada."
            )
        return dict(mascota)

    def actualizar(self, id_mascota: int, id_cliente: int, datos: MascotaUpdate) -> dict:
        campos = datos.model_dump(exclude_unset=True)  # solo lo que el cliente mandó
        mascota = self.repository.actualizar(id_mascota, id_cliente, campos)
        if not mascota:
            raise LookupError("Mascota no encontrada.")
        return dict(mascota)

    def inactivar(self, id_mascota: int, id_cliente: int, ) -> dict[str, Any]:
        """
        Inactiva una mascota del cliente autenticado.
            id_mascota: Identificador de la mascota.
            id_cliente: Identificador del cliente autenticado.

        Returns:
            Datos actualizados de la mascota.

        Raises:
            LookupError: Si la mascota no existe.
        """
        mascota = self.repository.cambiar_estado(
            id_mascota=id_mascota,
            id_cliente=id_cliente,
            estado="INACTIVA",
        )

        if mascota is None:
            raise LookupError(
                "Mascota no encontrada."
            )

        return mascota


    def activar(self, id_mascota: int, id_cliente: int,) -> dict[str, Any]:
        """
        Activa una mascota del cliente autenticado.
            id_mascota: Identificador de la mascota.
            id_cliente: Identificador del cliente autenticado.

        Returns:
            Datos actualizados de la mascota.

        Raises:
            LookupError: Si la mascota no existe.
        """
        mascota = self.repository.cambiar_estado(
            id_mascota=id_mascota,
            id_cliente=id_cliente,
            estado="ACTIVA",
        )

        if mascota is None:
            raise LookupError(
                "Mascota no encontrada."
            )

        return mascota

    