"""Acceso a las tablas vehiculo y propietario (solo lectura en esta iteración)."""
from typing import Optional

from models.entidades import Propietario, Vehiculo
from models.enums import TipoVehiculo


class VehiculoRepository:
    def asegurar_esquema(self, conn) -> None:
        """Garantiza que las columnas de estado existan en bases anteriores."""
        conn.execute(
            "ALTER TABLE propietario ADD COLUMN IF NOT EXISTS habilitado BOOLEAN NOT NULL DEFAULT true;"
            "ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS habilitado BOOLEAN NOT NULL DEFAULT true;"
        )

    def buscar_por_placa(self, conn, placa: str) -> Optional[Vehiculo]:
        """Busca el vehículo junto con su propietario. None si la placa no está registrada."""
        self.asegurar_esquema(conn)
        fila = conn.execute(
            "SELECT v.placa, v.tipo, v.marca, v.color, v.id_propietario, v.habilitado, "
            "       p.nombre, p.documento, p.telefono, p.habilitado AS propietario_habilitado "
            "FROM vehiculo v JOIN propietario p ON p.id_propietario = v.id_propietario "
            "WHERE v.placa = %s",
            (placa,),
        ).fetchone()
        if fila is None:
            return None
        propietario = Propietario(
            id_propietario=fila["id_propietario"],
            nombre=fila["nombre"],
            documento=fila["documento"],
            telefono=fila["telefono"],
            habilitado=bool(fila["propietario_habilitado"]),
        )
        return Vehiculo(
            placa=fila["placa"],
            tipo=TipoVehiculo(fila["tipo"]),
            marca=fila["marca"],
            color=fila["color"],
            id_propietario=fila["id_propietario"],
            propietario=propietario,
            habilitado=bool(fila["habilitado"]),
        )
