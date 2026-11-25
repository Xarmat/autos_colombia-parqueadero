"""Casos de uso para las decisiones de renovación y solicitudes de baja."""
from typing import Optional

from database.conexion import transaccion
from excepciones.errores import (ClienteConVehiculoDentro, DatosInvalidos,
                                 SolicitudNoDisponible, SolicitudYaExiste)
from models.entidades import SolicitudCliente
from models.enums import TipoSolicitudCliente
from repositories.cliente_repository import ClienteRepository
from repositories.solicitud_cliente_repository import SolicitudClienteRepository
from services.pago_service import PagoService


class SolicitudClienteService:
    def __init__(
        self,
        solicitud_repo: SolicitudClienteRepository,
        cliente_repo: ClienteRepository,
        pago_service: PagoService,
    ):
        self._repo = solicitud_repo
        self._clientes = cliente_repo
        self._pagos = pago_service

    def registrar_decision(
        self,
        id_propietario: int,
        tipo: TipoSolicitudCliente,
        placa: Optional[str] = None,
    ) -> None:
        try:
            tipo = TipoSolicitudCliente(tipo)
        except ValueError as error:
            raise DatosInvalidos("Selecciona una decisión de renovación válida.") from error
        if tipo is TipoSolicitudCliente.CONTINUAR and not placa:
            raise DatosInvalidos("Selecciona el vehículo que deseas renovar.")

        with transaccion() as conn:
            cliente = self._clientes.buscar_por_id(conn, id_propietario)
            if cliente is None or not cliente.habilitado:
                raise SolicitudNoDisponible("El cliente no está habilitado.")
            if placa:
                vehiculo = self._clientes.buscar_vehiculo_por_placa(conn, placa)
                if vehiculo is None or vehiculo.id_propietario != id_propietario:
                    raise SolicitudNoDisponible("El vehículo no pertenece a este cliente.")
                estado_pago = self._pagos.consultar_estado_en_transaccion(
                    conn, placa, vehiculo.tipo
                )
                if (
                    not estado_pago.renovacion_disponible
                    and estado_pago.estado not in ("Pago pendiente", "Bloqueado")
                ):
                    raise SolicitudNoDisponible(
                        "La decisión estará disponible siete días antes del vencimiento."
                    )
            if self._repo.buscar_pendiente(conn, id_propietario, placa, tipo):
                raise SolicitudYaExiste()
            self._repo.crear(conn, id_propietario, placa, tipo)

    def listar_pendientes(self) -> list[SolicitudCliente]:
        with transaccion() as conn:
            return self._repo.listar_pendientes(conn)

    def resolver(
        self,
        id_solicitud: int,
        id_administrador: int,
        aceptar: bool,
        respuesta: str = "",
    ) -> None:
        with transaccion() as conn:
            solicitud = self._repo.buscar_por_id(conn, id_solicitud)
            if solicitud is None or solicitud["estado"] != "PENDIENTE":
                raise SolicitudNoDisponible("La solicitud ya fue atendida o no existe.")

            tipo = TipoSolicitudCliente(solicitud["tipo"])
            estado = "ATENDIDA" if aceptar else "RECHAZADA"
            if aceptar and tipo is TipoSolicitudCliente.BAJA:
                placa = self._clientes.buscar_placa_vehiculo_dentro(
                    conn, solicitud["id_propietario"]
                )
                if placa:
                    raise ClienteConVehiculoDentro(placa)
                self._clientes.cambiar_estado_cliente(
                    conn, solicitud["id_propietario"], False
                )

            texto = respuesta.strip()
            if not texto:
                texto = (
                    "Baja aprobada." if aceptar and tipo is TipoSolicitudCliente.BAJA
                    else "Solicitud atendida." if aceptar
                    else "Solicitud rechazada."
                )
            self._repo.resolver(
                conn, id_solicitud, id_administrador, estado, texto
            )
