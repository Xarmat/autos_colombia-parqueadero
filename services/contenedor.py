"""Punto único donde se arman los servicios con sus repositorios.

La interfaz recibe este objeto y nunca crea repositorios ni toca la base:
así cada capa solo conoce a la de abajo.
"""
from dataclasses import dataclass

from repositories.celda_estado_repository import CeldaEstadoRepository
from repositories.celda_repository import CeldaRepository
from repositories.cliente_repository import ClienteRepository
from repositories.movimiento_repository import MovimientoRepository
from repositories.novedad_repository import NovedadRepository
from repositories.operario_repository import OperarioRepository
from repositories.puerta_repository import PuertaRepository
from repositories.vehiculo_repository import VehiculoRepository
from services.auth_service import AuthService
from services.celda_service import CeldaService
from services.cliente_service import ClienteService
from services.ingreso_service import IngresoService
from services.novedad_service import NovedadService
from services.ocupacion_service import OcupacionService
from services.salida_service import SalidaService


@dataclass
class Servicios:
    auth: AuthService
    ingreso: IngresoService
    salida: SalidaService
    ocupacion: OcupacionService
    novedad: NovedadService
    cliente: ClienteService
    celda: CeldaService


def crear_servicios() -> Servicios:
    """Crea los repositorios una vez y se los entrega a cada servicio."""
    operarios, puertas = OperarioRepository(), PuertaRepository()
    vehiculos = VehiculoRepository()
    celdas_base = CeldaRepository()
    celdas_ext = CeldaEstadoRepository()
    movimientos, novedades = MovimientoRepository(), NovedadRepository()
    clientes = ClienteRepository()
    return Servicios(
        auth=AuthService(operarios, puertas),
        ingreso=IngresoService(vehiculos, celdas_base, movimientos),
        salida=SalidaService(movimientos),
        ocupacion=OcupacionService(celdas_base),
        novedad=NovedadService(movimientos, novedades),
        cliente=ClienteService(clientes),
        celda=CeldaService(celdas_ext),
    )
