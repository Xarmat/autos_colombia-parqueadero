"""Casos de uso para la gestión de clientes y sus vehículos."""
from datetime import date
from typing import List, Optional

from database.conexion import transaccion
from excepciones.errores import (ClienteConVehiculoDentro, ClienteInhabilitado,
                                 ClienteYaExiste, CredencialesInvalidas, DatosInvalidos,
                                 TipoVehiculoDentro, VehiculoDentro, VehiculoYaExiste)
from models.entidades import ComprobantePago, Propietario, Sesion, Vehiculo
from models.enums import MedioPago, TipoVehiculo
from models.seguridad import comprobar_clave, generar_hash
from repositories.cliente_repository import ClienteRepository
from services.pago_service import PagoService
from services.utilidades import normalizar_placa


class ClienteService:
    def __init__(self, cliente_repo: ClienteRepository, pago_service: PagoService):
        self._repo = cliente_repo
        self._pagos = pago_service

    @staticmethod
    def _validar_datos_cliente(nombre: str, documento: str, telefono: Optional[str],
                               clave: str) -> tuple[str, str, Optional[str], str]:
        nombre = (nombre or "").strip()
        documento = (documento or "").strip()
        telefono = (telefono or "").strip() or None
        clave = (clave or "").strip()
        if not nombre:
            raise DatosInvalidos("Escribe el nombre del cliente.")
        if len(nombre) > 30:
            raise DatosInvalidos("El nombre del cliente no puede superar los 30 caracteres.")
        if not documento:
            raise DatosInvalidos("Escribe el documento del cliente.")
        if not documento.isdigit():
            raise DatosInvalidos("El documento debe contener únicamente dígitos numéricos.")
        if len(documento) > 10:
            raise DatosInvalidos("El documento no puede superar los 10 dígitos.")
        if telefono:
            if not telefono.isdigit():
                raise DatosInvalidos("El teléfono debe contener únicamente dígitos numéricos.")
            if len(telefono) > 10:
                raise DatosInvalidos("El teléfono no puede superar los 10 dígitos.")
        if not clave:
            raise DatosInvalidos("Escribe una clave inicial para el cliente.")
        if not (6 <= len(clave) <= 10):
            raise DatosInvalidos("La clave debe tener entre 6 y 10 caracteres.")
        return nombre, documento, telefono, clave

    @staticmethod
    def _validar_datos_vehiculo(
        placa: str, tipo: TipoVehiculo, marca: str, color: str
    ) -> tuple[str, TipoVehiculo, str, str]:
        placa = normalizar_placa(placa)
        tipo = TipoVehiculo(tipo)
        marca = (marca or "").strip()
        color = (color or "").strip()
        if not marca:
            raise DatosInvalidos("Escribe la marca del vehículo.")
        if len(marca) > 30:
            raise DatosInvalidos("La marca no puede superar los 30 caracteres.")
        if not color:
            raise DatosInvalidos("Escribe el color del vehículo.")
        if len(color) > 20:
            raise DatosInvalidos("El color no puede superar los 20 caracteres.")
        return placa, tipo, marca, color

    def buscar_clientes(self, termino: str = "") -> List[Propietario]:
        """Busca clientes por coincidencia de documento, nombre o placa."""
        with transaccion() as conn:
            return self._repo.buscar_clientes(conn, termino)

    def listar_vehiculos(self, id_propietario: int) -> List[Vehiculo]:
        """Obtiene la lista de vehículos de un cliente."""
        with transaccion() as conn:
            vehiculos = self._repo.listar_vehiculos_cliente(conn, id_propietario)
            for vehiculo in vehiculos:
                vehiculo.estado_pago = self._pagos.consultar_estado_en_transaccion(
                    conn, vehiculo.placa, vehiculo.tipo
                )
            return vehiculos

    def registrar_cliente(
        self, nombre: str, documento: str, telefono: Optional[str], clave: str
    ) -> Propietario:
        """Registra un nuevo cliente con su clave inicial."""
        nombre, documento, telefono, clave = self._validar_datos_cliente(
            nombre, documento, telefono, clave
        )

        with transaccion() as conn:
            existente = self._repo.buscar_por_documento(conn, documento)
            if existente is not None:
                if existente.habilitado:
                    raise ClienteYaExiste(documento)
                self._repo.reactivar_cliente(conn, existente.id_propietario)
                return self._repo.buscar_por_id(conn, existente.id_propietario)

            clave_hash = generar_hash(clave)
            return self._repo.crear_cliente(conn, nombre, documento, telefono, clave_hash)

    def registrar_cliente_con_vehiculo(
        self, nombre: str, documento: str, telefono: Optional[str], clave: str,
        placa: str, tipo: TipoVehiculo, marca: str, color: str,
        fecha_inicio: date, medio_pago: MedioPago, sesion: Sesion,
    ) -> tuple[Propietario, Vehiculo, ComprobantePago]:
        """Crea o reactiva al cliente, el vehículo y el pago inicial atómicamente."""
        nombre, documento, telefono, clave = self._validar_datos_cliente(
            nombre, documento, telefono, clave
        )
        placa, tipo, marca, color = self._validar_datos_vehiculo(
            placa, tipo, marca, color
        )
        with transaccion() as conn:
            existente = self._repo.buscar_por_documento(conn, documento)
            if existente is not None and existente.habilitado:
                raise ClienteYaExiste(documento)
            if self._repo.buscar_vehiculo_por_placa(conn, placa) is not None:
                raise VehiculoYaExiste(placa)
            if existente is None:
                cliente = self._repo.crear_cliente(
                    conn, nombre, documento, telefono, generar_hash(clave)
                )
            else:
                self._repo.reactivar_cliente(conn, existente.id_propietario)
                cliente = self._repo.buscar_por_id(conn, existente.id_propietario)
            vehiculo = self._repo.crear_vehiculo(
                conn, placa, tipo, marca, color, cliente.id_propietario
            )
            comprobante = self._pagos.registrar_pago_en_transaccion(
                conn, placa, medio_pago, sesion, fecha_inicio
            )
            return cliente, vehiculo, comprobante

    def actualizar_cliente(
        self, id_propietario: int, nombre: str, telefono: Optional[str]
    ) -> None:
        """Actualiza el nombre y teléfono del cliente."""
        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip() or None

        if not nombre:
            raise DatosInvalidos("El nombre del cliente no puede estar vacío.")
        if len(nombre) > 30:
            raise DatosInvalidos("El nombre del cliente no puede superar los 30 caracteres.")
        if telefono:
            if not telefono.isdigit():
                raise DatosInvalidos("El teléfono debe contener únicamente dígitos numéricos.")
            if len(telefono) > 10:
                raise DatosInvalidos("El teléfono no puede superar los 10 dígitos.")

        with transaccion() as conn:
            self._repo.actualizar_cliente(conn, id_propietario, nombre, telefono)

    def cambiar_estado_cliente(self, id_propietario: int, habilitar: bool) -> None:
        """Inhabilita o habilita a un cliente.

        Si se inhabilita, ningún vehículo del cliente puede estar actualmente en el parqueadero.
        """
        with transaccion() as conn:
            if not habilitar:
                placa = self._repo.buscar_placa_vehiculo_dentro(conn, id_propietario)
                if placa:
                    raise ClienteConVehiculoDentro(placa)
            self._repo.cambiar_estado_cliente(conn, id_propietario, habilitar)

    def vehiculo_esta_dentro(self, placa: str) -> bool:
        """Indica si el vehículo tiene un ingreso activo."""
        with transaccion() as conn:
            return self._repo.vehiculo_esta_dentro(conn, normalizar_placa(placa))

    def restablecer_clave(self, id_propietario: int, nueva_clave: str) -> None:
        """Cambia la contraseña del cliente."""
        nueva_clave = (nueva_clave or "").strip()
        if not nueva_clave:
            raise DatosInvalidos("Escribe la nueva contraseña.")
        if not (6 <= len(nueva_clave) <= 10):
            raise DatosInvalidos("La clave debe tener entre 6 y 10 caracteres.")

        with transaccion() as conn:
            clave_hash = generar_hash(nueva_clave)
            self._repo.cambiar_clave_cliente(conn, id_propietario, clave_hash)

    def registrar_vehiculo(
        self, placa: str, tipo: TipoVehiculo, marca: str, color: str, id_propietario: int
    ) -> Vehiculo:
        """Registra un nuevo vehículo y lo vincula al cliente."""
        placa, tipo, marca, color = self._validar_datos_vehiculo(
            placa, tipo, marca, color
        )

        with transaccion() as conn:
            if self._repo.buscar_vehiculo_por_placa(conn, placa) is not None:
                raise VehiculoYaExiste(placa)

            return self._repo.crear_vehiculo(conn, placa, tipo, marca, color, id_propietario)

    def actualizar_vehiculo(
        self, placa: str, tipo: TipoVehiculo, marca: str, color: str
    ) -> None:
        """Actualiza tipo, marca y color del vehículo."""
        placa = normalizar_placa(placa)
        tipo = TipoVehiculo(tipo)
        marca = (marca or "").strip()
        color = (color or "").strip()

        if not marca:
            raise DatosInvalidos("Escribe la marca del vehículo.")
        if not color:
            raise DatosInvalidos("Escribe el color del vehículo.")

        with transaccion() as conn:
            vehiculo = self._repo.buscar_vehiculo_por_placa(conn, placa)
            if vehiculo is not None and self._repo.vehiculo_esta_dentro(conn, placa):
                if tipo != vehiculo.tipo:
                    raise TipoVehiculoDentro()
            self._repo.actualizar_vehiculo(conn, placa, tipo, marca, color)

    def cambiar_estado_vehiculo(self, placa: str, habilitar: bool) -> None:
        """Inhabilita o habilita un vehículo. No se puede inhabilitar si está dentro."""
        placa = normalizar_placa(placa)
        with transaccion() as conn:
            if not habilitar:
                if self._repo.vehiculo_esta_dentro(conn, placa):
                    raise VehiculoDentro(placa)
            self._repo.cambiar_estado_vehiculo(conn, placa, habilitar)

    def autenticar_cliente(self, documento: str, clave: str) -> Propietario:
        """Autentica a un cliente por su documento y contraseña."""
        documento = (documento or "").strip()
        clave = (clave or "").strip()
        if not documento or not clave:
            raise CredencialesInvalidas()

        with transaccion() as conn:
            cliente = self._repo.buscar_por_documento(conn, documento)
            if cliente is None:
                raise CredencialesInvalidas()
            if not cliente.habilitado:
                raise ClienteInhabilitado()
            if not cliente.clave_hash or not comprobar_clave(clave, cliente.clave_hash):
                raise CredencialesInvalidas()
            return cliente

    def obtener_resumen_mensual(self, id_propietario: int) -> dict:
        """Calcula el cobro mensual según los vehículos del cliente."""
        TARIFA_VEHICULO = 120_000
        TARIFA_MOTO = 60_000

        with transaccion() as conn:
            vehiculos = self._repo.listar_vehiculos_cliente(conn, id_propietario)
            for vehiculo in vehiculos:
                vehiculo.estado_pago = self._pagos.consultar_estado_en_transaccion(
                    conn, vehiculo.placa, vehiculo.tipo
                )

        items = []
        total = 0
        for v in vehiculos:
            tarifa = TARIFA_VEHICULO if v.tipo == TipoVehiculo.VEHICULO else TARIFA_MOTO
            tarifa_cobrable = tarifa if v.habilitado else 0
            items.append({
                "placa": v.placa,
                "tipo_str": "vehículo" if v.tipo == TipoVehiculo.VEHICULO else "moto",
                "tarifa": tarifa_cobrable,
                "habilitado": v.habilitado,
                "estado_pago": v.estado_pago,
            })
            if v.habilitado:
                total += tarifa

        return {
            "vehiculos": vehiculos,
            "items": items,
            "total": total,
        }
