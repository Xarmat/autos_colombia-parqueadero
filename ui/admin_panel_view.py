"""Panel de administración: personal, clientes, celdas y solicitudes."""
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout

from models.entidades import Administrador, SesionAdministrador
from services.contenedor import Servicios
from ui.celda_view import EstadoCeldasView
from ui.cliente_view import ClientesVehiculosView
from ui.comun import ejecutar, mostrar_info
from ui.personal_view import PersonalView
from ui.solicitudes_view import SolicitudesView
from ui.solicitudes_cliente_view import SolicitudesClienteView


class AdminPanelView(QDialog):
    def __init__(self, administrador: Administrador, servicios: Servicios, parent=None):
        super().__init__(parent)
        self._administrador = administrador
        self._servicios = servicios
        self._sesion = SesionAdministrador(administrador)
        self.setWindowTitle("Autos Colombia - Administración")
        self.setFixedWidth(500)

        titulo = QLabel("Panel de administración")
        titulo.setObjectName("titulo")
        quien = QLabel(f"Administrador: {administrador.nombre}")
        quien.setObjectName("subtitulo")
        self.lbl_ocupacion = QLabel("")
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)

        self.btn_personal = QPushButton("Personal y cuentas")
        self.btn_clientes = QPushButton("Clientes y vehículos")
        self.btn_celdas = QPushButton("Administrar celdas")
        self.btn_solicitudes = QPushButton("Solicitudes de operarios")
        self.btn_solicitudes_cliente = QPushButton("Solicitudes de clientes")
        self.btn_cerrar = QPushButton("Cerrar sesión")

        for boton in (
            self.btn_personal, self.btn_clientes, self.btn_celdas, self.btn_solicitudes,
            self.btn_solicitudes_cliente,
        ):
            boton.setObjectName("accion_panel")
        self.btn_cerrar.setObjectName("secundario")

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.btn_personal, 0, 0)
        grid.addWidget(self.btn_clientes, 0, 1)
        grid.addWidget(self.btn_celdas, 1, 0)
        grid.addWidget(self.btn_solicitudes, 1, 1)
        grid.addWidget(self.btn_solicitudes_cliente, 2, 0, 1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addWidget(titulo)
        layout.addWidget(quien)
        layout.addWidget(self.lbl_ocupacion)
        layout.addWidget(self.lbl_mensaje)
        layout.addLayout(grid)
        layout.addWidget(self.btn_cerrar)

        self.btn_personal.clicked.connect(self._abrir_personal)
        self.btn_clientes.clicked.connect(self._abrir_clientes)
        self.btn_celdas.clicked.connect(self._abrir_celdas)
        self.btn_solicitudes.clicked.connect(self._abrir_solicitudes)
        self.btn_solicitudes_cliente.clicked.connect(self._abrir_solicitudes_cliente)
        self.btn_cerrar.clicked.connect(self.accept)
        self._refrescar()

    def _refrescar(self) -> None:
        ok, ocupacion = ejecutar(
            self.lbl_mensaje, self._servicios.ocupacion.consultar_ocupacion
        )
        if ok:
            self.lbl_ocupacion.setText(
                f"Motos: {ocupacion.motos_ocupadas} dentro, {ocupacion.motos_libres} disponibles\n"
                f"Vehículos: {ocupacion.vehiculos_ocupados} dentro, "
                f"{ocupacion.vehiculos_libres} disponibles"
            )
            mostrar_info(self.lbl_mensaje, "")

    def _abrir_personal(self) -> None:
        PersonalView(self._servicios.administrador, self).exec()

    def _abrir_clientes(self) -> None:
        ClientesVehiculosView(self._servicios.cliente, self).exec()

    def _abrir_celdas(self) -> None:
        EstadoCeldasView(self._sesion, self._servicios.celda, self).exec()
        self._refrescar()

    def _abrir_solicitudes(self) -> None:
        SolicitudesView(
            self._administrador, self._servicios.solicitud, self._abrir_celdas, self
        ).exec()
        self._refrescar()

    def _abrir_solicitudes_cliente(self) -> None:
        SolicitudesClienteView(
            self._administrador, self._servicios.solicitudes_cliente, self
        ).exec()
