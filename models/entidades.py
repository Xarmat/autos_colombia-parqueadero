"""Entidades del dominio (las clases del diagrama de clases).

Son datos puros: no saben nada de PostgreSQL ni de la interfaz.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from models.enums import (ConceptoPago, MedioPago, TipoSolicitudCliente,
                          TipoVehiculo, Turno)
from models.seguridad import comprobar_clave


@dataclass
class Propietario:
    id_propietario: int
    nombre: str
    documento: str
    telefono: Optional[str] = None
    habilitado: bool = True
    clave_hash: Optional[str] = None
    fecha_nuevo_registro: Optional[datetime] = None


@dataclass
class Vehiculo:
    placa: str
    tipo: TipoVehiculo
    marca: str
    color: str
    id_propietario: int
    propietario: Optional[Propietario] = None  # se llena cuando la consulta lo trae
    habilitado: bool = True
    estado_pago: Optional["EstadoPagoVehiculo"] = None


@dataclass
class DetallePago:
    concepto: ConceptoPago
    fecha_inicio: date
    fecha_fin: date
    valor: int


@dataclass
class EstadoPagoVehiculo:
    placa: str
    estado: str
    tarifa_mensual: int
    fecha_inicio: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    fecha_cubierta_hasta: Optional[date] = None
    dias_mora: int = 0
    bloqueado_ingreso: bool = True
    siguiente_inicio: Optional[date] = None
    siguiente_fin: Optional[date] = None
    decision_renovacion: Optional[str] = None
    renovacion_disponible: bool = False


@dataclass
class ComprobantePago:
    id_pago: int
    placa: str
    nombre_cliente: str
    tipo_vehiculo: TipoVehiculo
    fecha_pago: datetime
    medio_pago: MedioPago
    usuario_operario: str
    valor_total: int
    detalles: list[DetallePago]


@dataclass
class SolicitudCliente:
    id_solicitud: int
    id_propietario: int
    nombre_cliente: str
    documento: str
    placa: Optional[str]
    tipo: TipoSolicitudCliente
    estado: str
    fecha_solicitud: datetime


@dataclass
class Celda:
    id_celda: int
    codigo: str
    tipo: TipoVehiculo
    habilitada: bool = True
    motivo_bloqueo: Optional[str] = None


@dataclass
class Puerta:
    id_puerta: int
    nombre: str


@dataclass
class Operario:
    id_operario: int
    nombre: str
    usuario: str
    clave_hash: str
    turno: Turno
    habilitado: bool = True

    def verificar_clave(self, clave: str) -> bool:
        """True si la clave escrita corresponde al hash guardado."""
        return comprobar_clave(clave, self.clave_hash)


@dataclass
class Movimiento:
    """Una visita completa: nace al ingresar y se cierra al salir."""
    id_movimiento: int
    placa: str
    id_celda: int
    fecha_ingreso: datetime
    id_puerta_ingreso: int
    id_operario_ingreso: int
    fecha_salida: Optional[datetime] = None
    id_puerta_salida: Optional[int] = None
    id_operario_salida: Optional[int] = None
    celda: Optional[Celda] = None  # se llena cuando la consulta o el servicio la conoce

    def esta_activo(self) -> bool:
        """El vehículo sigue dentro mientras no tenga fecha de salida."""
        return self.fecha_salida is None


@dataclass
class Novedad:
    id_novedad: int
    id_movimiento: int
    id_operario: int
    descripcion: str
    fecha_hora: datetime


@dataclass
class Ocupacion:
    """Foto del estado del parqueadero: celdas libres y ocupadas por tipo."""
    motos_libres: int
    motos_ocupadas: int
    vehiculos_libres: int
    vehiculos_ocupados: int

    @property
    def total_dentro(self) -> int:
        return self.motos_ocupadas + self.vehiculos_ocupados


@dataclass
class Sesion:
    """Quién está trabajando y desde qué puerta; se crea al iniciar sesión."""
    operario: Operario
    puerta: Puerta


@dataclass
class Administrador:
    id_administrador: int
    nombre: str
    usuario: str
    clave_hash: str
    habilitado: bool = True

    def verificar_clave(self, clave: str) -> bool:
        return comprobar_clave(clave, self.clave_hash)


@dataclass
class SesionAdministrador:
    administrador: Administrador


@dataclass
class SolicitudCambio:
    id_solicitud: int
    id_operario: int
    id_movimiento: Optional[int]
    placa_reportada: Optional[str]
    tipo: str
    descripcion: str
    estado: str
    respuesta: Optional[str]
    placa_corregida: Optional[str]
    fecha_solicitud: datetime
    nombre_operario: str = ""
    usuario_operario: str = ""
