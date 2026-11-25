"""Consultas y operaciones administrativas para personal y cuentas de administración."""
from typing import List, Optional

from models.entidades import Administrador, Operario
from models.enums import Turno


class AdministradorRepository:
    def usuario_en_uso(self, conn, usuario: str, excluir_operario: Optional[int] = None,
                       excluir_administrador: Optional[int] = None) -> bool:
        fila = conn.execute(
            "SELECT EXISTS ("
            "SELECT 1 FROM operario WHERE usuario=%s AND id_operario IS DISTINCT FROM %s "
            "UNION ALL "
            "SELECT 1 FROM administrador WHERE usuario=%s "
            "AND id_administrador IS DISTINCT FROM %s"
            ") AS existe",
            (usuario, excluir_operario, usuario, excluir_administrador),
        ).fetchone()
        return fila["existe"]

    def buscar_por_usuario(self, conn, usuario: str) -> Optional[Administrador]:
        fila = conn.execute(
            "SELECT id_administrador, nombre, usuario, clave_hash, habilitado "
            "FROM administrador WHERE usuario = %s",
            (usuario,),
        ).fetchone()
        return self._a_administrador(fila) if fila else None

    @staticmethod
    def _a_administrador(fila) -> Administrador:
        return Administrador(
            id_administrador=fila["id_administrador"],
            nombre=fila["nombre"],
            usuario=fila["usuario"],
            clave_hash=fila["clave_hash"],
            habilitado=fila["habilitado"],
        )

    def listar_administradores(self, conn) -> List[Administrador]:
        filas = conn.execute(
            "SELECT id_administrador, nombre, usuario, clave_hash, habilitado "
            "FROM administrador ORDER BY nombre"
        ).fetchall()
        return [self._a_administrador(fila) for fila in filas]

    def crear_administrador(self, conn, nombre: str, usuario: str, clave_hash: str) -> Administrador:
        fila = conn.execute(
            "INSERT INTO administrador (nombre, usuario, clave_hash) "
            "VALUES (%s, %s, %s) "
            "RETURNING id_administrador, nombre, usuario, clave_hash, habilitado",
            (nombre, usuario, clave_hash),
        ).fetchone()
        return self._a_administrador(fila)

    def actualizar_administrador(self, conn, id_administrador: int, nombre: str,
                                 usuario: str, clave_hash: Optional[str]) -> None:
        if clave_hash:
            conn.execute(
                "UPDATE administrador SET nombre=%s, usuario=%s, clave_hash=%s "
                "WHERE id_administrador=%s",
                (nombre, usuario, clave_hash, id_administrador),
            )
        else:
            conn.execute(
                "UPDATE administrador SET nombre=%s, usuario=%s WHERE id_administrador=%s",
                (nombre, usuario, id_administrador),
            )

    def cambiar_estado_administrador(self, conn, id_administrador: int, habilitado: bool) -> None:
        conn.execute(
            "UPDATE administrador SET habilitado=%s WHERE id_administrador=%s",
            (habilitado, id_administrador),
        )

    def contar_administradores_habilitados(self, conn) -> int:
        fila = conn.execute(
            "SELECT COUNT(*) AS cantidad FROM administrador WHERE habilitado"
        ).fetchone()
        return fila["cantidad"]

    @staticmethod
    def _a_operario(fila) -> Operario:
        return Operario(
            id_operario=fila["id_operario"],
            nombre=fila["nombre"],
            usuario=fila["usuario"],
            clave_hash=fila["clave_hash"],
            turno=Turno(fila["turno"]),
            habilitado=fila["habilitado"],
        )

    def listar_operarios(self, conn) -> List[Operario]:
        filas = conn.execute(
            "SELECT id_operario, nombre, usuario, clave_hash, turno, habilitado "
            "FROM operario ORDER BY turno, nombre"
        ).fetchall()
        return [self._a_operario(fila) for fila in filas]

    def buscar_operario_por_id(self, conn, id_operario: int) -> Optional[Operario]:
        fila = conn.execute(
            "SELECT id_operario, nombre, usuario, clave_hash, turno, habilitado "
            "FROM operario WHERE id_operario=%s",
            (id_operario,),
        ).fetchone()
        return self._a_operario(fila) if fila else None

    def contar_operarios_habilitados(self, conn, turno: Turno) -> int:
        fila = conn.execute(
            "SELECT COUNT(*) AS cantidad FROM operario WHERE turno=%s AND habilitado",
            (turno.value,),
        ).fetchone()
        return fila["cantidad"]

    def crear_operario(self, conn, nombre: str, usuario: str, clave_hash: str,
                       turno: Turno) -> Operario:
        fila = conn.execute(
            "INSERT INTO operario (nombre, usuario, clave_hash, turno) "
            "VALUES (%s, %s, %s, %s) "
            "RETURNING id_operario, nombre, usuario, clave_hash, turno, habilitado",
            (nombre, usuario, clave_hash, turno.value),
        ).fetchone()
        return self._a_operario(fila)

    def actualizar_operario(self, conn, id_operario: int, nombre: str, usuario: str,
                            turno: Turno, clave_hash: Optional[str]) -> None:
        if clave_hash:
            conn.execute(
                "UPDATE operario SET nombre=%s, usuario=%s, turno=%s, clave_hash=%s "
                "WHERE id_operario=%s",
                (nombre, usuario, turno.value, clave_hash, id_operario),
            )
        else:
            conn.execute(
                "UPDATE operario SET nombre=%s, usuario=%s, turno=%s WHERE id_operario=%s",
                (nombre, usuario, turno.value, id_operario),
            )

    def cambiar_estado_operario(self, conn, id_operario: int, habilitado: bool) -> None:
        conn.execute(
            "UPDATE operario SET habilitado=%s WHERE id_operario=%s",
            (habilitado, id_operario),
        )
