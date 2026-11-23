"""Repositorio para la gestión de celdas con estado extendido.

Extiende CeldaRepository con las consultas necesarias para la pantalla
de estado de celdas (HU-C1) y la corrección de celda (HU-C2).
"""
from dataclasses import dataclass
from typing import List, Optional

import psycopg

from excepciones.errores import CeldaOcupada, DatosInvalidos
from models.entidades import Celda, Movimiento
from models.enums import TipoVehiculo
from repositories.celda_repository import CeldaRepository


@dataclass
class CeldaConEstado:
    """Celda enriquecida con su estado real (libre/ocupada) y la placa si está ocupada."""
    id_celda: int
    codigo: str
    tipo: TipoVehiculo
    libre: bool
    placa: Optional[str] = None      # solo cuando libre=False
    id_movimiento: Optional[int] = None   # para la corrección


class CeldaEstadoRepository(CeldaRepository):
    """Extiende CeldaRepository sin romper los métodos existentes."""

    def listar_todas_con_estado(self, conn) -> List[CeldaConEstado]:
        """Lista las 80 celdas con su estado real calculado en una sola consulta."""
        filas = conn.execute(
            """
            SELECT c.id_celda, c.codigo, c.tipo,
                   m.placa, m.id_movimiento
            FROM celda c
            LEFT JOIN movimiento m
                ON m.id_celda = c.id_celda AND m.fecha_salida IS NULL
            ORDER BY c.tipo, c.codigo
            """
        ).fetchall()
        return [
            CeldaConEstado(
                id_celda=f["id_celda"],
                codigo=f["codigo"],
                tipo=TipoVehiculo(f["tipo"]),
                libre=f["placa"] is None,
                placa=f["placa"],
                id_movimiento=f["id_movimiento"],
            )
            for f in filas
        ]

    def listar_libres_del_tipo(self, conn, tipo: TipoVehiculo) -> List[Celda]:
        """Celdas libres del tipo indicado (para el selector de celda destino)."""
        filas = conn.execute(
            """
            SELECT c.id_celda, c.codigo, c.tipo
            FROM celda c
            WHERE c.tipo = %s
              AND NOT EXISTS (
                SELECT 1 FROM movimiento m
                WHERE m.id_celda = c.id_celda AND m.fecha_salida IS NULL
              )
            ORDER BY c.codigo
            """,
            (tipo.value,),
        ).fetchall()
        return [Celda(f["id_celda"], f["codigo"], TipoVehiculo(f["tipo"])) for f in filas]

    def corregir_celda(
        self,
        conn,
        id_movimiento: int,
        id_celda_destino: int,
        id_operario: int,
        motivo: str,
    ) -> None:
        """Mueve el movimiento activo a una nueva celda libre del mismo tipo.

        1. Bloquea la celda destino (FOR UPDATE) para evitar que otra transacción
           la tome simultáneamente.
        2. Actualiza id_celda en el movimiento.
        3. Registra la corrección como novedad en la tabla novedad.
        """
        # 1. Bloquear y verificar que la celda destino sigue libre
        try:
            fila_celda = conn.execute(
                """
                SELECT id_celda FROM celda
                WHERE id_celda = %s
                  AND NOT EXISTS (
                    SELECT 1 FROM movimiento m2
                    WHERE m2.id_celda = celda.id_celda AND m2.fecha_salida IS NULL
                  )
                FOR UPDATE
                """,
                (id_celda_destino,),
            ).fetchone()
        except psycopg.errors.LockNotAvailable:
            raise CeldaOcupada()

        if fila_celda is None:
            raise DatosInvalidos("La celda destino ya no está disponible. Elige otra.")

        # 2. Reubicar el movimiento
        conn.execute(
            "UPDATE movimiento SET id_celda = %s WHERE id_movimiento = %s",
            (id_celda_destino, id_movimiento),
        )

        # 3. Registrar como novedad para trazabilidad (RNF-03)
        conn.execute(
            "INSERT INTO novedad (id_movimiento, id_operario, descripcion) "
            "VALUES (%s, %s, %s)",
            (id_movimiento, id_operario, f"[Corrección de celda] {motivo}"),
        )
