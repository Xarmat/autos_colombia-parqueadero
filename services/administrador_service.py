"""Casos de uso de administración de cuentas de operarios y administradores."""
from typing import List, Optional

from database.conexion import transaccion
from excepciones.errores import (DatosInvalidos, OperarioNoDisponible,
                                 UltimoAdministrador, UsuarioYaExiste)
from models.entidades import Administrador, Operario
from models.enums import Turno
from models.seguridad import generar_hash
from repositories.administrador_repository import AdministradorRepository

_CUPO_POR_TURNO = {Turno.DIA: 2, Turno.NOCHE: 1}


class AdministradorService:
    def __init__(self, repo: AdministradorRepository):
        self._repo = repo

    def listar_operarios(self) -> List[Operario]:
        with transaccion() as conn:
            return self._repo.listar_operarios(conn)

    def listar_administradores(self) -> List[Administrador]:
        with transaccion() as conn:
            return self._repo.listar_administradores(conn)

    @staticmethod
    def _validar_cuenta(nombre: str, usuario: str, clave: Optional[str] = None) -> tuple[str, str]:
        nombre = (nombre or "").strip()
        usuario = (usuario or "").strip()
        if not nombre or len(nombre) > 30:
            raise DatosInvalidos("El nombre es obligatorio y no puede superar los 30 caracteres.")
        if not usuario or len(usuario) > 14 or not usuario.isalnum():
            raise DatosInvalidos("El usuario debe contener de 1 a 14 letras o números.")
        if clave is not None and not (6 <= len(clave) <= 10):
            raise DatosInvalidos("La contraseña debe tener entre 6 y 10 caracteres.")
        return nombre, usuario

    def crear_operario(self, nombre: str, usuario: str, clave: str, turno: Turno,
                       reemplazar_id: Optional[int] = None) -> Operario:
        nombre, usuario = self._validar_cuenta(nombre, usuario, clave)
        clave = clave or ""
        turno = Turno(turno)
        with transaccion() as conn:
            conn.execute("LOCK TABLE operario, administrador IN SHARE ROW EXCLUSIVE MODE")
            if self._repo.usuario_en_uso(conn, usuario):
                raise UsuarioYaExiste(usuario)
            if reemplazar_id is not None:
                anterior = self._repo.buscar_operario_por_id(conn, reemplazar_id)
                if anterior is None or not anterior.habilitado or anterior.turno != turno:
                    raise DatosInvalidos("Selecciona un operario habilitado del mismo turno para reemplazar.")
                self._repo.cambiar_estado_operario(conn, reemplazar_id, False)
            cupo = _CUPO_POR_TURNO[turno]
            if self._repo.contar_operarios_habilitados(conn, turno) >= cupo:
                raise OperarioNoDisponible(turno.value)
            return self._repo.crear_operario(conn, nombre, usuario, generar_hash(clave), turno)

    def actualizar_operario(self, id_operario: int, nombre: str, usuario: str,
                            turno: Turno, nueva_clave: str = "") -> None:
        nombre, usuario = self._validar_cuenta(nombre, usuario, nueva_clave or None)
        turno = Turno(turno)
        with transaccion() as conn:
            conn.execute("LOCK TABLE operario, administrador IN SHARE ROW EXCLUSIVE MODE")
            operario = self._repo.buscar_operario_por_id(conn, id_operario)
            if operario is None:
                raise DatosInvalidos("El operario ya no existe.")
            if self._repo.usuario_en_uso(conn, usuario, excluir_operario=id_operario):
                raise UsuarioYaExiste(usuario)
            if operario.habilitado and operario.turno != turno:
                raise DatosInvalidos(
                    "Para cambiar el turno, reemplaza la cuenta dentro del mismo turno."
                )
            if not operario.habilitado and operario.turno != turno:
                cupo = _CUPO_POR_TURNO[turno]
                if self._repo.contar_operarios_habilitados(conn, turno) >= cupo:
                    raise OperarioNoDisponible(turno.value)
            clave_hash = generar_hash(nueva_clave) if nueva_clave else None
            self._repo.actualizar_operario(
                conn, id_operario, nombre, usuario, turno, clave_hash
            )

    def reactivar_operario(self, id_operario: int) -> None:
        with transaccion() as conn:
            conn.execute("LOCK TABLE operario IN SHARE ROW EXCLUSIVE MODE")
            operario = self._repo.buscar_operario_por_id(conn, id_operario)
            if operario is None:
                raise DatosInvalidos("El operario ya no existe.")
            if operario.habilitado:
                return
            if self._repo.contar_operarios_habilitados(conn, operario.turno) >= _CUPO_POR_TURNO[operario.turno]:
                raise OperarioNoDisponible(operario.turno.value)
            self._repo.cambiar_estado_operario(conn, id_operario, True)

    def crear_administrador(self, nombre: str, usuario: str, clave: str) -> Administrador:
        nombre, usuario = self._validar_cuenta(nombre, usuario, clave)
        with transaccion() as conn:
            conn.execute("LOCK TABLE operario, administrador IN SHARE ROW EXCLUSIVE MODE")
            if self._repo.listar_administradores(conn):
                raise DatosInvalidos("El sistema solo permite una cuenta de administrador.")
            if self._repo.usuario_en_uso(conn, usuario):
                raise UsuarioYaExiste(usuario)
            return self._repo.crear_administrador(conn, nombre, usuario, generar_hash(clave))

    def actualizar_administrador(self, id_administrador: int, nombre: str, usuario: str,
                                 nueva_clave: str = "") -> None:
        nombre, usuario = self._validar_cuenta(nombre, usuario, nueva_clave or None)
        with transaccion() as conn:
            conn.execute("LOCK TABLE operario, administrador IN SHARE ROW EXCLUSIVE MODE")
            if self._repo.usuario_en_uso(
                conn, usuario, excluir_administrador=id_administrador
            ):
                raise UsuarioYaExiste(usuario)
            if not any(a.id_administrador == id_administrador
                       for a in self._repo.listar_administradores(conn)):
                raise DatosInvalidos("La cuenta de administrador ya no existe.")
            clave_hash = generar_hash(nueva_clave) if nueva_clave else None
            self._repo.actualizar_administrador(
                conn, id_administrador, nombre, usuario, clave_hash
            )

    def cambiar_estado_administrador(self, id_administrador: int, habilitado: bool) -> None:
        with transaccion() as conn:
            conn.execute("LOCK TABLE administrador IN SHARE ROW EXCLUSIVE MODE")
            administradores = self._repo.listar_administradores(conn)
            actual = next((a for a in administradores
                           if a.id_administrador == id_administrador), None)
            if actual is None:
                raise DatosInvalidos("La cuenta de administrador ya no existe.")
            if not habilitado and actual.habilitado:
                if self._repo.contar_administradores_habilitados(conn) <= 1:
                    raise UltimoAdministrador()
            self._repo.cambiar_estado_administrador(conn, id_administrador, habilitado)
