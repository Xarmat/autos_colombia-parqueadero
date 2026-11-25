"""Reglas de vigencia, cobro y acceso por estado de pago."""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Optional

from dateutil.relativedelta import relativedelta

from database.conexion import transaccion
from excepciones.errores import (ClienteInhabilitado, DatosInvalidos, PagoPendiente,
                                 ServicioAunNoInicia, VehiculoInhabilitado,
                                 VehiculoNoRegistrado)
from models.entidades import (
    ComprobantePago, DetallePago, EstadoPagoVehiculo, Sesion,
)
from models.enums import ConceptoPago, MedioPago, TipoVehiculo
from repositories.pago_repository import PagoRepository

_DIAS_GRACIA = 15
_DIAS_AVISO_RENOVACION = 7
_TARIFAS = {
    TipoVehiculo.MOTO: 60_000,
    TipoVehiculo.VEHICULO: 120_000,
}


class PagoService:
    def __init__(
        self, pago_repo: PagoRepository, reloj: Callable[[], date] = date.today
    ):
        self._repo = pago_repo
        self._hoy = reloj

    @staticmethod
    def _periodo_mensual(inicio: date, dia_ancla: int) -> tuple[date, date]:
        """Calcula el cierre anterior al siguiente inicio, conservando el ancla."""
        siguiente_inicio = inicio + relativedelta(months=1, day=dia_ancla)
        return inicio, siguiente_inicio - timedelta(days=1)

    @staticmethod
    def _valor_prorrateado(tarifa: int, dias_ciclo: int, dias_cobrables: int) -> int:
        """Redondea el prorrateo al peso más cercano."""
        valor = Decimal(tarifa) * dias_cobrables / dias_ciclo
        return int(valor.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _mensualidades(detalles: list[dict]) -> list[dict]:
        return [
            detalle for detalle in detalles
            if ConceptoPago(detalle["concepto"]) is ConceptoPago.MENSUALIDAD
        ]

    def _vehiculo(self, conn, placa: str, bloquear: bool = False) -> dict:
        fila = self._repo.buscar_vehiculo(conn, placa, bloquear)
        if fila is None:
            raise VehiculoNoRegistrado(placa)
        return fila

    def _pagos_vigentes(self, conn, vehiculo: dict, placa: str) -> list[dict]:
        """Ignora coberturas anteriores a la última reactivación lógica."""
        activado_desde = max(
            vehiculo["fecha_habilitacion"], vehiculo["fecha_nuevo_registro"]
        )
        return [
            detalle for detalle in self._repo.listar_detalles(conn, placa)
            if detalle["fecha_pago"] >= activado_desde
        ]

    def consultar_estado_en_transaccion(
        self, conn, placa: str, tipo: Optional[TipoVehiculo] = None
    ) -> EstadoPagoVehiculo:
        """Calcula el estado actual y el siguiente periodo de la placa."""
        vehiculo = self._vehiculo(conn, placa)
        tipo = TipoVehiculo(tipo or vehiculo["tipo"])
        tarifa = _TARIFAS[tipo]
        pagos = self._pagos_vigentes(conn, vehiculo, placa)
        mensualidades = self._mensualidades(pagos)
        decision = self._repo.obtener_ultima_solicitud_renovacion(conn, placa)

        if not mensualidades:
            return EstadoPagoVehiculo(
                placa=placa,
                estado="Pago pendiente",
                tarifa_mensual=tarifa,
                decision_renovacion=decision,
            )

        hoy = self._hoy()
        vigente = [
            detalle for detalle in mensualidades
            if detalle["fecha_inicio"] <= hoy <= detalle["fecha_fin"]
        ]
        if vigente:
            referencia = max(vigente, key=lambda detalle: detalle["fecha_inicio"])
            estado = "Al día"
            dias_mora = 0
            bloqueado = False
        else:
            vencidas = [
                detalle for detalle in mensualidades if detalle["fecha_fin"] < hoy
            ]
            if not vencidas:
                referencia = min(
                    mensualidades, key=lambda detalle: detalle["fecha_inicio"]
                )
                estado = "Próximo"
                dias_mora = 0
                bloqueado = True
            else:
                referencia = max(vencidas, key=lambda detalle: detalle["fecha_fin"])
                dias_mora = (hoy - referencia["fecha_fin"]).days
                bloqueado = dias_mora >= _DIAS_GRACIA
                estado = "Bloqueado" if bloqueado else "Pago pendiente"

        ultima = max(mensualidades, key=lambda detalle: detalle["fecha_inicio"])
        periodo_prepagado = ultima["fecha_inicio"] > referencia["fecha_inicio"]
        if estado == "Bloqueado":
            siguiente_inicio = hoy
            dia_ancla = hoy.day
        else:
            siguiente_inicio = ultima["fecha_fin"] + timedelta(days=1)
            dia_ancla = ultima["dia_ancla"] or ultima["fecha_inicio"].day
        _, siguiente_fin = self._periodo_mensual(siguiente_inicio, dia_ancla)
        dias_para_vencer = (referencia["fecha_fin"] - hoy).days
        renovacion_disponible = (
            estado == "Al día"
            and not periodo_prepagado
            and 0 <= dias_para_vencer <= _DIAS_AVISO_RENOVACION
        )

        return EstadoPagoVehiculo(
            placa=placa,
            estado=estado,
            tarifa_mensual=tarifa,
            fecha_inicio=referencia["fecha_inicio"],
            fecha_vencimiento=referencia["fecha_fin"],
            fecha_cubierta_hasta=max(
                detalle["fecha_fin"] for detalle in mensualidades
            ),
            dias_mora=dias_mora,
            bloqueado_ingreso=bloqueado,
            siguiente_inicio=siguiente_inicio,
            siguiente_fin=siguiente_fin,
            decision_renovacion=decision,
            renovacion_disponible=renovacion_disponible,
        )

    def consultar_estado(self, placa: str) -> EstadoPagoVehiculo:
        with transaccion() as conn:
            return self.consultar_estado_en_transaccion(conn, placa)

    def validar_ingreso(self, conn, placa: str) -> None:
        """Permite los primeros 14 días de gracia y bloquea desde el día 15."""
        estado = self.consultar_estado_en_transaccion(conn, placa)
        vehiculo = self._vehiculo(conn, placa)
        if not vehiculo["vehiculo_habilitado"]:
            raise VehiculoInhabilitado(placa)
        if not vehiculo["cliente_habilitado"]:
            raise ClienteInhabilitado()
        if estado.fecha_inicio is None:
            raise PagoPendiente(placa)
        if self._hoy() < estado.fecha_inicio:
            raise ServicioAunNoInicia(
                placa, estado.fecha_inicio.strftime("%d/%m/%Y")
            )
        if estado.bloqueado_ingreso:
            raise PagoPendiente(placa, estado.dias_mora)

    def _calcular_detalles(
        self,
        tipo: TipoVehiculo,
        pagos: list[dict],
        fecha_pago: date,
        fecha_inicio: Optional[date],
    ) -> list[dict]:
        tarifa = _TARIFAS[tipo]
        mensualidades = self._mensualidades(pagos)

        if not mensualidades:
            if fecha_inicio is None:
                raise DatosInvalidos("Selecciona la fecha de inicio de la mensualidad.")
            if fecha_inicio < fecha_pago:
                raise DatosInvalidos(
                    "La mensualidad inicial debe comenzar el día del pago o después."
                )
            inicio = fecha_inicio
            dia_ancla = inicio.day
            _, fin = self._periodo_mensual(inicio, dia_ancla)
            return [{
                "concepto": ConceptoPago.MENSUALIDAD,
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "dia_ancla": dia_ancla,
                "valor": tarifa,
            }]

        ultima = max(mensualidades, key=lambda detalle: detalle["fecha_inicio"])
        vencimiento = ultima["fecha_fin"]
        dias_mora = (fecha_pago - vencimiento).days

        if dias_mora >= _DIAS_GRACIA:
            prorrateo_inicio = vencimiento + timedelta(days=1)
            prorrateo_fin = vencimiento + timedelta(days=_DIAS_GRACIA)
            dias_ciclo = (ultima["fecha_fin"] - ultima["fecha_inicio"]).days + 1
            valor_prorrateo = self._valor_prorrateado(
                tarifa, dias_ciclo, _DIAS_GRACIA
            )
            inicio = fecha_pago
            dia_ancla = inicio.day
            _, fin = self._periodo_mensual(inicio, dia_ancla)
            return [
                {
                    "concepto": ConceptoPago.PRORRATEO,
                    "fecha_inicio": prorrateo_inicio,
                    "fecha_fin": prorrateo_fin,
                    "dia_ancla": None,
                    "valor": valor_prorrateo,
                },
                {
                    "concepto": ConceptoPago.MENSUALIDAD,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                    "dia_ancla": dia_ancla,
                    "valor": tarifa,
                },
            ]

        inicio = vencimiento + timedelta(days=1)
        dia_ancla = ultima["dia_ancla"] or ultima["fecha_inicio"].day
        _, fin = self._periodo_mensual(inicio, dia_ancla)
        return [{
            "concepto": ConceptoPago.MENSUALIDAD,
            "fecha_inicio": inicio,
            "fecha_fin": fin,
            "dia_ancla": dia_ancla,
            "valor": tarifa,
        }]

    def previsualizar_pago(
        self, placa: str, fecha_inicio: Optional[date] = None
    ) -> dict:
        """Calcula el monto y las vigencias sin guardar el pago."""
        with transaccion() as conn:
            vehiculo = self._vehiculo(conn, placa)
            pagos = self._pagos_vigentes(conn, vehiculo, placa)
            detalles = self._calcular_detalles(
                TipoVehiculo(vehiculo["tipo"]), pagos, self._hoy(), fecha_inicio
            )
            estado = self.consultar_estado_en_transaccion(conn, placa)
        return {
            "estado": estado,
            "detalles": detalles,
            "total": sum(detalle["valor"] for detalle in detalles),
        }

    def registrar_pago_en_transaccion(
        self,
        conn,
        placa: str,
        medio: MedioPago,
        sesion: Sesion,
        fecha_inicio: Optional[date] = None,
        continuar: Optional[bool] = None,
    ) -> ComprobantePago:
        """Guarda el pago y sus periodos dentro de una transacción existente."""
        if not isinstance(sesion, Sesion):
            raise DatosInvalidos("Solo un operario autenticado puede registrar pagos.")
        try:
            medio = MedioPago(medio)
        except ValueError as error:
            raise DatosInvalidos("Selecciona un medio de pago válido.") from error

        vehiculo = self._vehiculo(conn, placa, bloquear=True)
        if not vehiculo["vehiculo_habilitado"] or not vehiculo["cliente_habilitado"]:
            raise DatosInvalidos(
                "El cliente y el vehículo deben estar habilitados para registrar el pago."
            )

        pagos_previos = self._pagos_vigentes(conn, vehiculo, placa)
        mensualidades = self._mensualidades(pagos_previos)
        if mensualidades:
            ultima = max(mensualidades, key=lambda detalle: detalle["fecha_inicio"])
            dias_mora = (self._hoy() - ultima["fecha_fin"]).days
            if dias_mora >= _DIAS_GRACIA and continuar is not True:
                raise DatosInvalidos(
                    "Confirma que el cliente continuará para registrar el prorrateo "
                    "y la siguiente mensualidad."
                )
        detalles = self._calcular_detalles(
            TipoVehiculo(vehiculo["tipo"]), pagos_previos, self._hoy(), fecha_inicio
        )
        valor_total = sum(detalle["valor"] for detalle in detalles)
        fecha_activacion = max(
            vehiculo["fecha_habilitacion"], vehiculo["fecha_nuevo_registro"]
        )
        comprobante = self._repo.registrar(
            conn, placa, sesion.operario.id_operario, medio, valor_total, detalles,
            fecha_activacion,
        )

        return ComprobantePago(
            id_pago=comprobante["id_pago"],
            placa=placa,
            nombre_cliente=comprobante["nombre_cliente"],
            tipo_vehiculo=TipoVehiculo(comprobante["tipo_vehiculo"]),
            fecha_pago=comprobante["fecha_pago"],
            medio_pago=MedioPago(comprobante["medio_pago"]),
            usuario_operario=comprobante["usuario_operario"],
            valor_total=valor_total,
            detalles=[
                DetallePago(
                    concepto=detalle["concepto"],
                    fecha_inicio=detalle["fecha_inicio"],
                    fecha_fin=detalle["fecha_fin"],
                    valor=detalle["valor"],
                )
                for detalle in detalles
            ],
        )

    def registrar_pago(
        self,
        placa: str,
        medio: MedioPago,
        sesion: Sesion,
        fecha_inicio: Optional[date] = None,
        continuar: Optional[bool] = None,
    ) -> ComprobantePago:
        with transaccion() as conn:
            return self.registrar_pago_en_transaccion(
                conn, placa, medio, sesion, fecha_inicio, continuar
            )
