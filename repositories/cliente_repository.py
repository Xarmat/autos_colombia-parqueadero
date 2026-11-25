"""Acceso a las tablas propietario y vehiculo para la gestión de clientes y vehículos."""
from typing import List, Optional

from models.entidades import Propietario, Vehiculo
from models.enums import TipoVehiculo


class ClienteRepository:
    @staticmethod
    def _tipo_db(tipo: TipoVehiculo) -> str:
        """Convierte tanto enums como strings devueltos por Qt a su valor de base de datos."""
        return TipoVehiculo(tipo).value

    def asegurar_esquema(self, conn) -> None:
        """Garantiza que existan las columnas de estado y clave en PostgreSQL."""
        conn.execute(
            "ALTER TABLE propietario ADD COLUMN IF NOT EXISTS clave_hash VARCHAR(255) DEFAULT '';"
            "ALTER TABLE propietario ADD COLUMN IF NOT EXISTS habilitado BOOLEAN NOT NULL DEFAULT true;"
            "ALTER TABLE propietario ADD COLUMN IF NOT EXISTS fecha_nuevo_registro TIMESTAMP NOT NULL DEFAULT now();"
            "ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS habilitado BOOLEAN NOT NULL DEFAULT true;"
            "ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS fecha_habilitacion TIMESTAMP NOT NULL DEFAULT now();"
        )

    def buscar_clientes(self, conn, termino: str = "") -> List[Propietario]:
        """Busca clientes por documento, nombre o placa (búsqueda parcial).

        Si `termino` está vacío, lista todos los clientes.
        """
        self.asegurar_esquema(conn)
        termino = (termino or "").strip()
        if not termino:
            query = (
                "SELECT id_propietario, nombre, documento, telefono, habilitado, clave_hash, fecha_nuevo_registro "
                "FROM propietario ORDER BY nombre ASC"
            )
            filas = conn.execute(query).fetchall()
        else:
            patron = f"%{termino}%"
            query = """
                SELECT DISTINCT p.id_propietario, p.nombre, p.documento, p.telefono,
                       p.habilitado, p.clave_hash, p.fecha_nuevo_registro
                FROM propietario p
                LEFT JOIN vehiculo v ON v.id_propietario = p.id_propietario
                WHERE p.documento ILIKE %s
                   OR p.nombre ILIKE %s
                   OR v.placa ILIKE %s
                ORDER BY p.nombre ASC
            """
            filas = conn.execute(query, (patron, patron, patron)).fetchall()

        return [
            Propietario(
                id_propietario=f["id_propietario"],
                nombre=f["nombre"],
                documento=f["documento"],
                telefono=f["telefono"],
                habilitado=bool(f.get("habilitado", True)),
                clave_hash=f.get("clave_hash", ""),
                fecha_nuevo_registro=f.get("fecha_nuevo_registro"),
            )
            for f in filas
        ]

    def buscar_por_documento(self, conn, documento: str) -> Optional[Propietario]:
        """Busca un cliente por su documento exacto."""
        self.asegurar_esquema(conn)
        fila = conn.execute(
            "SELECT id_propietario, nombre, documento, telefono, habilitado, clave_hash, fecha_nuevo_registro "
            "FROM propietario WHERE documento = %s",
            (documento,),
        ).fetchone()
        if fila is None:
            return None
        return Propietario(
            id_propietario=fila["id_propietario"],
            nombre=fila["nombre"],
            documento=fila["documento"],
            telefono=fila["telefono"],
            habilitado=bool(fila.get("habilitado", True)),
            clave_hash=fila.get("clave_hash", ""),
            fecha_nuevo_registro=fila.get("fecha_nuevo_registro"),
        )

    def buscar_por_id(self, conn, id_propietario: int) -> Optional[Propietario]:
        """Busca un cliente por su id."""
        self.asegurar_esquema(conn)
        fila = conn.execute(
            "SELECT id_propietario, nombre, documento, telefono, habilitado, clave_hash, fecha_nuevo_registro "
            "FROM propietario WHERE id_propietario = %s",
            (id_propietario,),
        ).fetchone()
        if fila is None:
            return None
        return Propietario(
            id_propietario=fila["id_propietario"],
            nombre=fila["nombre"],
            documento=fila["documento"],
            telefono=fila["telefono"],
            habilitado=bool(fila.get("habilitado", True)),
            clave_hash=fila.get("clave_hash", ""),
            fecha_nuevo_registro=fila.get("fecha_nuevo_registro"),
        )

    def listar_vehiculos_cliente(self, conn, id_propietario: int) -> List[Vehiculo]:
        """Retorna todos los vehículos asociados a un cliente."""
        self.asegurar_esquema(conn)
        filas = conn.execute(
            "SELECT placa, tipo, marca, color, id_propietario, habilitado "
            "FROM vehiculo WHERE id_propietario = %s ORDER BY placa ASC",
            (id_propietario,),
        ).fetchall()
        return [
            Vehiculo(
                placa=f["placa"],
                tipo=TipoVehiculo(f["tipo"]),
                marca=f["marca"],
                color=f["color"],
                id_propietario=f["id_propietario"],
                habilitado=bool(f.get("habilitado", True)),
            )
            for f in filas
        ]

    def crear_cliente(
        self, conn, nombre: str, documento: str, telefono: Optional[str], clave_hash: str
    ) -> Propietario:
        """Inserta un nuevo cliente en la base de datos."""
        self.asegurar_esquema(conn)
        fila = conn.execute(
            "INSERT INTO propietario (nombre, documento, telefono, clave_hash, habilitado) "
            "VALUES (%s, %s, %s, %s, true) "
            "RETURNING id_propietario, nombre, documento, telefono, habilitado, clave_hash, fecha_nuevo_registro",
            (nombre, documento, telefono, clave_hash),
        ).fetchone()
        return Propietario(
            id_propietario=fila["id_propietario"],
            nombre=fila["nombre"],
            documento=fila["documento"],
            telefono=fila["telefono"],
            habilitado=fila["habilitado"],
            clave_hash=fila["clave_hash"],
            fecha_nuevo_registro=fila["fecha_nuevo_registro"],
        )

    def actualizar_cliente(
        self, conn, id_propietario: int, nombre: str, telefono: Optional[str]
    ) -> None:
        """Actualiza los datos básicos del cliente (nombre y teléfono)."""
        self.asegurar_esquema(conn)
        conn.execute(
            "UPDATE propietario SET nombre = %s, telefono = %s WHERE id_propietario = %s",
            (nombre, telefono, id_propietario),
        )

    def cambiar_estado_cliente(self, conn, id_propietario: int, habilitado: bool) -> None:
        """Cambia el estado del cliente y sincroniza el estado de todos sus vehículos."""
        self.asegurar_esquema(conn)
        conn.execute(
            "UPDATE propietario SET habilitado = %s, "
            "fecha_nuevo_registro = CASE WHEN %s THEN CURRENT_TIMESTAMP "
            "ELSE fecha_nuevo_registro END WHERE id_propietario = %s",
            (habilitado, habilitado, id_propietario),
        )
        conn.execute(
            "UPDATE vehiculo SET habilitado = %s, "
            "fecha_habilitacion = CASE WHEN %s THEN CURRENT_TIMESTAMP "
            "ELSE fecha_habilitacion END WHERE id_propietario = %s",
            (habilitado, habilitado, id_propietario),
        )

    def reactivar_cliente(self, conn, id_propietario: int) -> None:
        """Reactiva el usuario y sus vehículos sin reemplazar sus datos anteriores."""
        self.cambiar_estado_cliente(conn, id_propietario, True)

    def cambiar_clave_cliente(self, conn, id_propietario: int, clave_hash: str) -> None:
        """Actualiza la contraseña del cliente."""
        self.asegurar_esquema(conn)
        conn.execute(
            "UPDATE propietario SET clave_hash = %s WHERE id_propietario = %s",
            (clave_hash, id_propietario),
        )

    def buscar_vehiculo_por_placa(self, conn, placa: str) -> Optional[Vehiculo]:
        """Comprueba si una placa ya está registrada."""
        self.asegurar_esquema(conn)
        fila = conn.execute(
            "SELECT placa, tipo, marca, color, id_propietario, habilitado "
            "FROM vehiculo WHERE placa = %s",
            (placa,),
        ).fetchone()
        if fila is None:
            return None
        return Vehiculo(
            placa=fila["placa"],
            tipo=TipoVehiculo(fila["tipo"]),
            marca=fila["marca"],
            color=fila["color"],
            id_propietario=fila["id_propietario"],
            habilitado=bool(fila.get("habilitado", True)),
        )

    def crear_vehiculo(
        self, conn, placa: str, tipo: TipoVehiculo, marca: str, color: str, id_propietario: int
    ) -> Vehiculo:
        """Inserta un nuevo vehículo asociado al cliente."""
        self.asegurar_esquema(conn)
        conn.execute(
            "INSERT INTO vehiculo (placa, id_propietario, tipo, marca, color, habilitado) "
            "VALUES (%s, %s, %s, %s, %s, true)",
            (placa, id_propietario, self._tipo_db(tipo), marca, color),
        )
        return Vehiculo(
            placa=placa,
            tipo=TipoVehiculo(tipo),
            marca=marca,
            color=color,
            id_propietario=id_propietario,
            habilitado=True,
        )

    def actualizar_vehiculo(
        self, conn, placa: str, tipo: TipoVehiculo, marca: str, color: str
    ) -> None:
        """Actualiza los datos del vehículo (tipo, marca, color)."""
        self.asegurar_esquema(conn)
        conn.execute(
            "UPDATE vehiculo SET tipo = %s, marca = %s, color = %s WHERE placa = %s",
            (self._tipo_db(tipo), marca, color, placa),
        )

    def cambiar_estado_vehiculo(self, conn, placa: str, habilitado: bool) -> None:
        """Cambia el estado de habilitación de un vehículo."""
        self.asegurar_esquema(conn)
        conn.execute(
            "UPDATE vehiculo SET habilitado = %s, "
            "fecha_habilitacion = CASE WHEN %s THEN CURRENT_TIMESTAMP "
            "ELSE fecha_habilitacion END WHERE placa = %s",
            (habilitado, habilitado, placa),
        )

    def cliente_tiene_vehiculos_dentro(self, conn, id_propietario: int) -> bool:
        """Verifica si alguno de los vehículos del cliente tiene un movimiento activo."""
        fila = conn.execute(
            "SELECT 1 FROM movimiento m "
            "JOIN vehiculo v ON v.placa = m.placa "
            "WHERE v.id_propietario = %s AND m.fecha_salida IS NULL LIMIT 1",
            (id_propietario,),
        ).fetchone()
        return fila is not None

    def buscar_placa_vehiculo_dentro(self, conn, id_propietario: int) -> Optional[str]:
        """Retorna la placa de un vehículo activo asociado al cliente."""
        fila = conn.execute(
            "SELECT v.placa FROM movimiento m "
            "JOIN vehiculo v ON v.placa = m.placa "
            "WHERE v.id_propietario = %s AND m.fecha_salida IS NULL "
            "ORDER BY v.placa ASC LIMIT 1",
            (id_propietario,),
        ).fetchone()
        return fila["placa"] if fila is not None else None

    def vehiculo_esta_dentro(self, conn, placa: str) -> bool:
        """Verifica si el vehículo tiene un movimiento activo."""
        fila = conn.execute(
            "SELECT 1 FROM movimiento WHERE placa = %s AND fecha_salida IS NULL LIMIT 1",
            (placa,),
        ).fetchone()
        return fila is not None
