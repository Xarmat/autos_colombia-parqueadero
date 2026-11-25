"""Acceso a las decisiones de renovación y solicitudes de baja de clientes."""
from typing import Optional

from models.entidades import SolicitudCliente
from models.enums import TipoSolicitudCliente


class SolicitudClienteRepository:
    @staticmethod
    def _a_solicitud(fila) -> SolicitudCliente:
        return SolicitudCliente(
            id_solicitud=fila["id_solicitud"],
            id_propietario=fila["id_propietario"],
            nombre_cliente=fila["nombre_cliente"],
            documento=fila["documento"],
            placa=fila["placa"],
            tipo=TipoSolicitudCliente(fila["tipo"]),
            estado=fila["estado"],
            fecha_solicitud=fila["fecha_solicitud"],
        )

    def buscar_pendiente(
        self, conn, id_propietario: int, placa: Optional[str], tipo: TipoSolicitudCliente
    ) -> bool:
        """Impide que un mismo cliente envíe dos veces la misma decisión pendiente."""
        fila = conn.execute(
            "SELECT 1 FROM solicitud_cliente "
            "WHERE id_propietario=%s AND placa IS NOT DISTINCT FROM %s "
            "AND tipo=%s AND estado='PENDIENTE' LIMIT 1",
            (id_propietario, placa, tipo.value),
        ).fetchone()
        return fila is not None

    def crear(
        self, conn, id_propietario: int, placa: Optional[str], tipo: TipoSolicitudCliente
    ) -> None:
        conn.execute(
            "INSERT INTO solicitud_cliente (id_propietario, placa, tipo) "
            "VALUES (%s, %s, %s)",
            (id_propietario, placa, tipo.value),
        )

    def listar_pendientes(self, conn) -> list[SolicitudCliente]:
        filas = conn.execute(
            "SELECT s.id_solicitud, s.id_propietario, p.nombre AS nombre_cliente, "
            "p.documento, s.placa, s.tipo, s.estado, s.fecha_solicitud "
            "FROM solicitud_cliente s "
            "JOIN propietario p ON p.id_propietario=s.id_propietario "
            "WHERE s.estado='PENDIENTE' ORDER BY s.fecha_solicitud",
        ).fetchall()
        return [self._a_solicitud(fila) for fila in filas]

    def buscar_por_id(self, conn, id_solicitud: int) -> Optional[dict]:
        return conn.execute(
            "SELECT id_solicitud, id_propietario, placa, tipo, estado "
            "FROM solicitud_cliente WHERE id_solicitud=%s FOR UPDATE",
            (id_solicitud,),
        ).fetchone()

    def resolver(
        self,
        conn,
        id_solicitud: int,
        id_administrador: int,
        estado: str,
        respuesta: str,
    ) -> None:
        conn.execute(
            "UPDATE solicitud_cliente SET estado=%s, id_administrador=%s, "
            "respuesta=%s, fecha_resolucion=now() "
            "WHERE id_solicitud=%s AND estado='PENDIENTE'",
            (estado, id_administrador, respuesta, id_solicitud),
        )
