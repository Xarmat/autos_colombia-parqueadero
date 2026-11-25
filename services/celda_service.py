"""Caso de uso: estado de celdas y corrección de celda (HU-C1 y HU-C2)."""
from typing import List, Optional

from database.conexion import transaccion
from excepciones.errores import DatosInvalidos
from models.entidades import Celda
from models.enums import TipoVehiculo
from repositories.celda_estado_repository import CeldaConEstado, CeldaEstadoRepository


class CeldaService:
    def __init__(self, repo: CeldaEstadoRepository):
        self._repo = repo

    def listar_celdas(
        self,
        tipo: Optional[TipoVehiculo] = None,
        solo_libres: Optional[bool] = None,
    ) -> List[CeldaConEstado]:
        """Devuelve las celdas filtradas por tipo y/o estado.

        tipo=None → todas; solo_libres=None → todas.
        """
        with transaccion() as conn:
            celdas = self._repo.listar_todas_con_estado(conn)

        if tipo is not None:
            celdas = [c for c in celdas if c.tipo == tipo]
        if solo_libres is True:
            celdas = [c for c in celdas if c.libre]
        elif solo_libres is False:
            celdas = [c for c in celdas if not c.libre]
        return celdas

    def listar_celdas_libres(self, tipo: TipoVehiculo) -> List[Celda]:
        """Celdas libres del tipo indicado (para el combo selector de destino)."""
        with transaccion() as conn:
            return self._repo.listar_libres_del_tipo(conn, tipo)

    def corregir_celda(
        self,
        id_movimiento: int,
        id_celda_destino: int,
        motivo: str,
        id_administrador: int,
    ) -> None:
        """Asigna la celda destino y reserva la anterior hasta completar el traslado."""
        motivo = (motivo or "").strip()
        if not motivo:
            raise DatosInvalidos("Escribe el motivo de la corrección.")

        with transaccion() as conn:
            self._repo.corregir_celda(
                conn,
                id_movimiento=id_movimiento,
                id_celda_destino=id_celda_destino,
                id_administrador=id_administrador,
                motivo=motivo,
            )

    def cambiar_estado_celda(self, id_celda: int, habilitada: bool, motivo: str = "") -> None:
        motivo = (motivo or "").strip()
        if not habilitada and not motivo:
            raise DatosInvalidos("Escribe el motivo para bloquear la celda.")
        with transaccion() as conn:
            self._repo.cambiar_estado(conn, id_celda, habilitada, motivo or None)

    def finalizar_traslado(self, id_correccion: int) -> None:
        with transaccion() as conn:
            self._repo.finalizar_correccion(conn, id_correccion)
