"""Repositorio para la gestión de celdas con estado extendido.

Extiende CeldaRepository con las consultas necesarias para la pantalla
de estado de celdas (HU-C1) y la corrección de celda (HU-C2).
"""
from dataclasses import dataclass
from typing import List, Optional

import psycopg

from excepciones.errores import CeldaOcupada, DatosInvalidos
from models.entidades import Celda
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
    habilitada: bool = True
    motivo_bloqueo: Optional[str] = None
    id_correccion: Optional[int] = None


class CeldaEstadoRepository(CeldaRepository):
    """Extiende CeldaRepository sin romper los métodos existentes."""

    def listar_todas_con_estado(self, conn) -> List[CeldaConEstado]:
        """Lista las celdas, incluidos bloqueos administrativos y traslados pendientes."""
        filas = conn.execute(
            """
            SELECT c.id_celda, c.codigo, c.tipo,
                   m.placa, m.id_movimiento, c.habilitada, c.motivo_bloqueo,
                   cc.id_correccion
            FROM celda c
            LEFT JOIN movimiento m
                ON m.id_celda = c.id_celda AND m.fecha_salida IS NULL
            LEFT JOIN correccion_celda cc
                ON cc.id_celda_anterior = c.id_celda AND cc.estado = 'PENDIENTE'
            ORDER BY c.tipo, c.codigo
            """
        ).fetchall()
        return [
            CeldaConEstado(
                id_celda=f["id_celda"],
                codigo=f["codigo"],
                tipo=TipoVehiculo(f["tipo"]),
                libre=(f["placa"] is None and f["habilitada"] and f["id_correccion"] is None),
                placa=f["placa"],
                id_movimiento=f["id_movimiento"],
                habilitada=f["habilitada"],
                motivo_bloqueo=f["motivo_bloqueo"],
                id_correccion=f["id_correccion"],
            )
            for f in filas
        ]

    def listar_libres_del_tipo(self, conn, tipo: TipoVehiculo) -> List[Celda]:
        """Celdas libres del tipo indicado (para el selector de celda destino)."""
        filas = conn.execute(
            """
            SELECT c.id_celda, c.codigo, c.tipo
            FROM celda c
            WHERE c.tipo = %s AND c.habilitada
              AND NOT EXISTS (
                SELECT 1 FROM movimiento m
                WHERE m.id_celda = c.id_celda AND m.fecha_salida IS NULL
              )
              AND NOT EXISTS (
                SELECT 1 FROM correccion_celda cc
                WHERE cc.id_celda_anterior = c.id_celda AND cc.estado = 'PENDIENTE'
              )
            ORDER BY c.codigo
            """,
            (tipo.value,),
        ).fetchall()
        return [Celda(f["id_celda"], f["codigo"], TipoVehiculo(f["tipo"])) for f in filas]

    def cambiar_estado(self, conn, id_celda: int, habilitada: bool, motivo: Optional[str]) -> None:
        fila = conn.execute(
            """
            SELECT c.id_celda
            FROM celda c
            WHERE c.id_celda = %s
              AND NOT EXISTS (
                SELECT 1 FROM correccion_celda cc
                WHERE cc.estado='PENDIENTE'
                  AND (cc.id_celda_anterior=c.id_celda OR cc.id_celda_nueva=c.id_celda)
              )
            FOR UPDATE
            """,
            (id_celda,),
        ).fetchone()
        if fila is None:
            raise DatosInvalidos(
                "No se puede cambiar el estado de una celda ocupada o involucrada en una corrección pendiente."
            )
        conn.execute(
            "UPDATE celda SET habilitada=%s, motivo_bloqueo=%s WHERE id_celda=%s",
            (habilitada, motivo if not habilitada else None, id_celda),
        )

    def corregir_celda(
        self,
        conn,
        id_movimiento: int,
        id_celda_destino: int,
        id_administrador: int,
        motivo: str,
    ) -> None:
        """Asigna el destino y conserva la celda anterior bloqueada hasta el traslado."""
        try:
            fila_celda = conn.execute(
                """
                SELECT id_celda, tipo FROM celda
                WHERE id_celda = %s
                  AND habilitada
                  AND NOT EXISTS (
                    SELECT 1 FROM movimiento m2
                    WHERE m2.id_celda = celda.id_celda AND m2.fecha_salida IS NULL
                  )
                  AND NOT EXISTS (
                    SELECT 1 FROM correccion_celda cc
                    WHERE cc.id_celda_anterior=celda.id_celda AND cc.estado='PENDIENTE'
                  )
                FOR UPDATE
                """,
                (id_celda_destino,),
            ).fetchone()
        except psycopg.errors.LockNotAvailable:
            raise CeldaOcupada()

        if fila_celda is None:
            raise DatosInvalidos("La celda destino ya no está disponible. Elige otra.")

        movimiento = conn.execute(
            """
            SELECT m.id_celda, c.tipo
            FROM movimiento m JOIN celda c ON c.id_celda=m.id_celda
            WHERE m.id_movimiento=%s AND m.fecha_salida IS NULL
              AND NOT EXISTS (
                SELECT 1 FROM correccion_celda cc
                WHERE cc.id_movimiento=m.id_movimiento AND cc.estado='PENDIENTE'
              )
            FOR UPDATE OF m
            """,
            (id_movimiento,),
        ).fetchone()
        if movimiento is None:
            raise DatosInvalidos("El movimiento ya no está activo o tiene un traslado pendiente.")
        if movimiento["tipo"] != fila_celda["tipo"]:
            raise DatosInvalidos("La celda destino debe ser del mismo tipo que la celda actual.")
        id_celda_anterior = movimiento["id_celda"]
        if id_celda_anterior == id_celda_destino:
            raise DatosInvalidos("La celda destino debe ser diferente de la actual.")

        conn.execute(
            "UPDATE movimiento SET id_celda=%s WHERE id_movimiento=%s",
            (id_celda_destino, id_movimiento),
        )
        conn.execute(
            """
            INSERT INTO correccion_celda
                (id_movimiento, id_celda_anterior, id_celda_nueva, id_administrador, motivo)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_movimiento, id_celda_anterior, id_celda_destino, id_administrador, motivo),
        )

    def finalizar_correccion(self, conn, id_correccion: int) -> None:
        fila = conn.execute(
            "UPDATE correccion_celda SET estado='COMPLETADA', fecha_completada=now() "
            "WHERE id_correccion=%s AND estado='PENDIENTE' RETURNING id_correccion",
            (id_correccion,),
        ).fetchone()
        if fila is None:
            raise DatosInvalidos("El traslado ya fue completado o no existe.")
