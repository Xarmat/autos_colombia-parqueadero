"""Casos de uso para reportes de error del operario y su resolución."""
from typing import List, Optional

from database.conexion import transaccion
from excepciones.errores import DatosInvalidos
from models.entidades import Sesion, SolicitudCambio
from repositories.solicitud_repository import SolicitudRepository
from services.utilidades import normalizar_placa

_TIPOS = {"ENTRADA", "SALIDA", "CELDA", "OTRA"}


class SolicitudService:
    def __init__(self, repo: SolicitudRepository):
        self._repo = repo

    def crear(self, sesion: Sesion, tipo: str, placa: str, descripcion: str) -> SolicitudCambio:
        tipo = (tipo or "").strip().upper()
        placa = normalizar_placa(placa) if (placa or "").strip() else ""
        descripcion = (descripcion or "").strip()
        if tipo not in _TIPOS:
            raise DatosInvalidos("Selecciona el tipo de solicitud.")
        if not descripcion:
            raise DatosInvalidos("Describe la situación presentada.")
        if len(descripcion) > 1000:
            raise DatosInvalidos("La descripción no puede superar los 1000 caracteres.")
        if tipo in {"ENTRADA", "SALIDA", "CELDA"} and not placa:
            raise DatosInvalidos("Escribe la placa relacionada con la solicitud.")
        with transaccion() as conn:
            return self._repo.crear(
                conn, sesion.operario.id_operario, placa or None, tipo, descripcion
            )

    def listar(self) -> List[SolicitudCambio]:
        with transaccion() as conn:
            return self._repo.listar(conn)

    def resolver(self, id_solicitud: int, id_administrador: int, respuesta: str,
                 placa_corregida: str = "", rechazar: bool = False) -> None:
        respuesta = (respuesta or "").strip()
        placa_corregida = (placa_corregida or "").strip()
        if not respuesta:
            raise DatosInvalidos("Escribe la respuesta o solución aplicada.")
        if len(respuesta) > 1000:
            raise DatosInvalidos("La respuesta no puede superar los 1000 caracteres.")
        if placa_corregida:
            placa_corregida = normalizar_placa(placa_corregida)
        with transaccion() as conn:
            self._repo.resolver(
                conn, id_solicitud, id_administrador, respuesta,
                placa_corregida or None, rechazar,
            )
