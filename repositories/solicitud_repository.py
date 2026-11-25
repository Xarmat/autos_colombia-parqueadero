"""Acceso a las solicitudes de corrección enviadas por los operarios."""
from typing import List, Optional

from excepciones.errores import SolicitudNoDisponible
from models.entidades import SolicitudCambio


class SolicitudRepository:
    @staticmethod
    def _a_solicitud(fila) -> SolicitudCambio:
        return SolicitudCambio(
            id_solicitud=fila["id_solicitud"],
            id_operario=fila["id_operario"],
            id_movimiento=fila["id_movimiento"],
            placa_reportada=fila["placa_reportada"],
            tipo=fila["tipo"],
            descripcion=fila["descripcion"],
            estado=fila["estado"],
            respuesta=fila["respuesta"],
            placa_corregida=fila["placa_corregida"],
            fecha_solicitud=fila["fecha_solicitud"],
            nombre_operario=fila["nombre_operario"],
            usuario_operario=fila["usuario_operario"],
        )

    def crear(self, conn, id_operario: int, placa: Optional[str], tipo: str,
              descripcion: str) -> SolicitudCambio:
        fila = conn.execute(
            """
            INSERT INTO solicitud_cambio
                (id_operario, id_movimiento, placa_reportada, tipo, descripcion)
            VALUES (
                %s,
                (SELECT id_movimiento FROM movimiento
                 WHERE placa=%s
                 ORDER BY fecha_ingreso DESC LIMIT 1),
                %s, %s, %s
            )
            RETURNING id_solicitud
            """,
            (id_operario, placa, placa, tipo, descripcion),
        ).fetchone()
        fila = conn.execute(
            """
            SELECT s.id_solicitud, s.id_operario, s.id_movimiento, s.placa_reportada,
                   s.tipo, s.descripcion, s.estado, s.respuesta, s.placa_corregida,
                   s.fecha_solicitud, o.nombre AS nombre_operario, o.usuario AS usuario_operario
            FROM solicitud_cambio s JOIN operario o ON o.id_operario=s.id_operario
            WHERE s.id_solicitud=%s
            """,
            (fila["id_solicitud"],),
        ).fetchone()
        return self._a_solicitud(fila)

    def listar(self, conn) -> List[SolicitudCambio]:
        filas = conn.execute(
            """
            SELECT s.id_solicitud, s.id_operario, s.id_movimiento, s.placa_reportada,
                   s.tipo, s.descripcion, s.estado, s.respuesta, s.placa_corregida,
                   s.fecha_solicitud, o.nombre AS nombre_operario, o.usuario AS usuario_operario
            FROM solicitud_cambio s JOIN operario o ON o.id_operario=s.id_operario
            ORDER BY CASE s.estado WHEN 'PENDIENTE' THEN 0 ELSE 1 END,
                     s.fecha_solicitud DESC
            """
        ).fetchall()
        return [self._a_solicitud(fila) for fila in filas]

    def resolver(self, conn, id_solicitud: int, id_administrador: int, respuesta: str,
                 placa_corregida: Optional[str], rechazar: bool = False) -> None:
        solicitud = conn.execute(
            "SELECT id_movimiento, placa_reportada, tipo, estado "
            "FROM solicitud_cambio WHERE id_solicitud=%s FOR UPDATE",
            (id_solicitud,),
        ).fetchone()
        if solicitud is None or solicitud["estado"] != "PENDIENTE":
            raise SolicitudNoDisponible("La solicitud ya fue atendida o no existe.")

        es_error_placa = solicitud["tipo"] in {"ENTRADA", "SALIDA"}
        if (es_error_placa and solicitud["id_movimiento"] is not None
                and not placa_corregida and not rechazar):
            raise SolicitudNoDisponible(
                "Indica la placa correcta o rechaza la solicitud explicando el motivo."
            )
        if placa_corregida and not rechazar:
            if not es_error_placa or solicitud["id_movimiento"] is None:
                raise SolicitudNoDisponible(
                    "No se encontró un movimiento asociado para corregir la placa."
                )
            movimiento = conn.execute(
                """
                SELECT m.id_celda, m.placa, m.fecha_salida,
                       m.id_puerta_salida, m.id_operario_salida,
                       c.tipo AS tipo_celda, v.tipo AS tipo_vehiculo,
                       v.habilitado AS vehiculo_habilitado,
                       p.habilitado AS propietario_habilitado
                FROM movimiento m
                JOIN celda c ON c.id_celda=m.id_celda
                JOIN vehiculo v ON v.placa=%s
                JOIN propietario p ON p.id_propietario=v.id_propietario
                WHERE m.id_movimiento=%s
                FOR UPDATE OF m
                """,
                (placa_corregida, solicitud["id_movimiento"]),
            ).fetchone()
            if movimiento is None:
                raise SolicitudNoDisponible("La placa corregida no está registrada.")
            if movimiento["placa"] != solicitud["placa_reportada"]:
                raise SolicitudNoDisponible(
                    "El movimiento cambió desde que se creó la solicitud; vuelve a consultar."
                )
            if placa_corregida == solicitud["placa_reportada"]:
                raise SolicitudNoDisponible("La placa correcta debe ser diferente de la reportada.")
            if movimiento["tipo_celda"] != movimiento["tipo_vehiculo"]:
                raise SolicitudNoDisponible(
                    "La placa correcta no corresponde al tipo de celda asignada."
                )
            if not movimiento["vehiculo_habilitado"] or not movimiento["propietario_habilitado"]:
                raise SolicitudNoDisponible("El vehículo o su propietario están inhabilitados.")
            duplicado = conn.execute(
                "SELECT 1 FROM movimiento WHERE placa=%s AND fecha_salida IS NULL "
                "AND id_movimiento<>%s",
                (placa_corregida, solicitud["id_movimiento"]),
            ).fetchone()
            if duplicado:
                if solicitud["tipo"] != "SALIDA" or movimiento["fecha_salida"] is None:
                    raise SolicitudNoDisponible("La placa correcta ya tiene un ingreso activo.")
                movimiento_correcto = conn.execute(
                    """
                    SELECT m.id_movimiento, m.id_celda, m.fecha_ingreso
                    FROM movimiento m
                    WHERE m.placa=%s AND m.fecha_salida IS NULL
                      AND m.id_movimiento<>%s
                    FOR UPDATE
                    """,
                    (placa_corregida, solicitud["id_movimiento"]),
                ).fetchone()
                if movimiento_correcto is None:
                    raise SolicitudNoDisponible("No se pudo localizar el ingreso activo correcto.")
                if movimiento["fecha_salida"] < movimiento_correcto["fecha_ingreso"]:
                    raise SolicitudNoDisponible(
                        "La salida registrada es anterior al ingreso de la placa correcta."
                    )
                placa_reportada_activa = conn.execute(
                    "SELECT 1 FROM movimiento WHERE placa=%s AND fecha_salida IS NULL "
                    "AND id_movimiento<>%s",
                    (solicitud["placa_reportada"], solicitud["id_movimiento"]),
                ).fetchone()
                if placa_reportada_activa:
                    raise SolicitudNoDisponible(
                        "La placa reportada ya tiene otro ingreso activo; no se puede restaurar."
                    )
                celda_reutilizada = conn.execute(
                    "SELECT 1 FROM movimiento WHERE id_celda=%s "
                    "AND fecha_salida IS NULL AND id_movimiento<>%s",
                    (movimiento["id_celda"], solicitud["id_movimiento"]),
                ).fetchone()
                if celda_reutilizada:
                    raise SolicitudNoDisponible(
                        "La celda del registro equivocado ya fue reasignada. "
                        "No se puede restaurar el estado automáticamente."
                    )
                if conn.execute(
                    "SELECT 1 FROM celda WHERE id_celda=%s AND habilitada",
                    (movimiento["id_celda"],),
                ).fetchone() is None:
                    raise SolicitudNoDisponible(
                        "La celda del registro equivocado está bloqueada; "
                        "resuelve primero la ubicación física del vehículo."
                    )
                conn.execute(
                    "UPDATE movimiento SET fecha_salida=NULL, id_puerta_salida=NULL, "
                    "id_operario_salida=NULL WHERE id_movimiento=%s",
                    (solicitud["id_movimiento"],),
                )
                conn.execute(
                    "UPDATE movimiento SET fecha_salida=%s, id_puerta_salida=%s, "
                    "id_operario_salida=%s WHERE id_movimiento=%s",
                    (movimiento["fecha_salida"], movimiento["id_puerta_salida"],
                     movimiento["id_operario_salida"], movimiento_correcto["id_movimiento"]),
                )
                conn.execute(
                    "UPDATE correccion_celda SET estado='COMPLETADA', fecha_completada=now() "
                    "WHERE id_movimiento=%s AND estado='PENDIENTE'",
                    (movimiento_correcto["id_movimiento"],),
                )
            else:
                conn.execute(
                    "UPDATE movimiento SET placa=%s WHERE id_movimiento=%s",
                    (placa_corregida, solicitud["id_movimiento"]),
                )

        conn.execute(
            """
            UPDATE solicitud_cambio
            SET estado=%s, respuesta=%s, placa_corregida=%s,
                id_administrador=%s, fecha_resolucion=now()
            WHERE id_solicitud=%s
            """,
            ("RECHAZADA" if rechazar else "RESUELTA", respuesta,
             placa_corregida if not rechazar else None, id_administrador, id_solicitud),
        )
