"""Errores controlados del sistema.

Todos heredan de ParqueaderoError y llevan un mensaje pensado para el operario:
la interfaz solo tiene que mostrar str(error), sin saber qué falló por dentro.
"""


class ParqueaderoError(Exception):
    """Base de todos los errores controlados."""


class ErrorBaseDatos(ParqueaderoError):
    """No hay conexión con PostgreSQL o se perdió a mitad de una operación."""


class CredencialesInvalidas(ParqueaderoError):
    def __init__(self):
        # Mismo mensaje para usuario inexistente y clave errónea (no revela cuál falló).
        super().__init__("Usuario o contraseña incorrectos.")


class DatosInvalidos(ParqueaderoError):
    """Entrada vacía o con formato incorrecto (placa, descripción, etc.)."""


class VehiculoNoRegistrado(ParqueaderoError):
    def __init__(self, placa: str):
        super().__init__(f"El vehículo {placa} no está registrado, no puede ingresar.")


class VehiculoYaDentro(ParqueaderoError):
    def __init__(self, placa: str):
        super().__init__(f"El vehículo {placa} ya tiene un ingreso activo.")


class VehiculoNoEstaDentro(ParqueaderoError):
    def __init__(self, placa: str):
        super().__init__(f"El vehículo {placa} no tiene un ingreso activo.")


class SinCupo(ParqueaderoError):
    def __init__(self, tipo: str):
        super().__init__(f"No hay celdas disponibles para {tipo}.")


class ClienteYaExiste(ParqueaderoError):
    def __init__(self, documento: str):
        super().__init__(f"El documento {documento} ya está registrado.")


class VehiculoYaExiste(ParqueaderoError):
    def __init__(self, placa: str):
        super().__init__(f"La placa {placa} ya está registrada.")


class ClienteConVehiculoDentro(ParqueaderoError):
    def __init__(self, placa: str = ""):
        if placa:
            super().__init__(
                f"El vehículo {placa} está dentro del parqueadero. "
                "Registra su salida antes de inhabilitar al cliente."
            )
        else:
            super().__init__("No se puede inhabilitar al cliente porque tiene vehículos dentro del parqueadero.")


class TipoVehiculoDentro(ParqueaderoError):
    def __init__(self):
        super().__init__(
            "El vehículo está dentro del parqueadero, "
            "sólo se puede modificar la marca y el color."
        )


class ClienteInhabilitado(ParqueaderoError):
    def __init__(self):
        super().__init__("Tu cuenta está inhabilitada. Habla con el operario.")


class VehiculoDentro(ParqueaderoError):
    def __init__(self, placa: str):
        super().__init__(f"No se puede inhabilitar el vehículo {placa} porque está dentro del parqueadero.")


class VehiculoInhabilitado(ParqueaderoError):
    def __init__(self, placa: str):
        super().__init__(f"El vehículo {placa} está inhabilitado, no puede ingresar.")


class CeldaOcupada(ParqueaderoError):
    """Uso interno: otra puerta tomó la misma celda en el mismo instante.

    IngresoService la captura y reintenta con otra celda; el operario no la ve.
    """
