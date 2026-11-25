"""Persistencia de pagos y periodos cubiertos por cada pago."""
from typing import Optional

from models.enums import MedioPago


class PagoRepository:
    def buscar_vehiculo(self, conn, placa: str, bloquear: bool = False) -> Optional[dict]:
        """Retorna los datos necesarios para consultar o registrar pagos."""
        consulta = (
            "SELECT v.placa, v.tipo, v.habilitado AS vehiculo_habilitado, "
            "v.fecha_habilitacion, "
            "p.id_propietario, p.nombre AS nombre_cliente, "
            "p.habilitado AS cliente_habilitado, p.fecha_nuevo_registro "
            "FROM vehiculo v JOIN propietario p ON p.id_propietario=v.id_propietario "
            "WHERE v.placa=%s"
        )
        if bloquear:
            consulta += " FOR UPDATE OF v"
        return conn.execute(consulta, (placa,)).fetchone()

    def listar_detalles(self, conn, placa: str) -> list[dict]:
        """Lista los periodos ya cubiertos, incluyendo quién registró cada pago."""
        return conn.execute(
            "SELECT d.concepto, d.fecha_inicio, d.fecha_fin, d.dia_ancla, d.valor, "
            "p.id_pago, p.fecha_pago, p.medio_pago, o.usuario AS usuario_operario "
            "FROM pago_detalle d JOIN pago p ON p.id_pago=d.id_pago "
            "JOIN operario o ON o.id_operario=p.id_operario "
            "WHERE d.placa=%s ORDER BY d.fecha_inicio, d.id_detalle",
            (placa,),
        ).fetchall()

    def registrar(
        self,
        conn,
        placa: str,
        id_operario: int,
        medio: MedioPago,
        valor_total: int,
        detalles: list[dict],
        fecha_activacion,
    ) -> dict:
        """Guarda el comprobante y sus coberturas en la transacción recibida."""
        fila = conn.execute(
            "INSERT INTO pago (placa, medio_pago, id_operario, valor_total) "
            "VALUES (%s, %s, %s, %s) "
            "RETURNING id_pago, fecha_pago, medio_pago, valor_total",
            (placa, medio.value, id_operario, valor_total),
        ).fetchone()
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO pago_detalle "
                "(id_pago, placa, concepto, fecha_inicio, fecha_fin, dia_ancla, "
                "fecha_activacion, valor) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        fila["id_pago"],
                        placa,
                        detalle["concepto"].value,
                        detalle["fecha_inicio"],
                        detalle["fecha_fin"],
                        detalle.get("dia_ancla"),
                        fecha_activacion,
                        detalle["valor"],
                    )
                    for detalle in detalles
                ],
            )
        vehiculo = self.buscar_vehiculo(conn, placa)
        operario = conn.execute(
            "SELECT usuario FROM operario WHERE id_operario=%s",
            (id_operario,),
        ).fetchone()
        return {
            **fila,
            "placa": placa,
            "nombre_cliente": vehiculo["nombre_cliente"],
            "tipo_vehiculo": vehiculo["tipo"],
            "usuario_operario": operario["usuario"],
            "detalles": detalles,
        }

    def obtener_ultima_solicitud_renovacion(self, conn, placa: str) -> Optional[str]:
        """Devuelve la decisión pendiente más reciente del cliente para la placa."""
        fila = conn.execute(
            "SELECT tipo FROM solicitud_cliente "
            "WHERE placa=%s AND estado='PENDIENTE' "
            "ORDER BY fecha_solicitud DESC LIMIT 1",
            (placa,),
        ).fetchone()
        return fila["tipo"] if fila else None
