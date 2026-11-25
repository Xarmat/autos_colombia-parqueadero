"""Panel operativo restringido a entradas, salidas y solicitudes de cambio."""
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout

from models.entidades import Sesion
from services.contenedor import Servicios
from ui.ingreso_view import IngresoView
from ui.pago_view import PagoView
from ui.salida_view import SalidaView
from ui.solicitud_view import SolicitudView


class PanelView(QDialog):
    def __init__(self, sesion: Sesion, servicios: Servicios, parent=None):
        super().__init__(parent)
        self._sesion = sesion
        self._servicios = servicios

        self.setWindowTitle("Autos Colombia - Panel")
        self.setFixedWidth(420)

        # --- Encabezado: quién y desde dónde ---
        titulo = QLabel("Panel de operación")
        titulo.setObjectName("titulo")
        quien = QLabel(f"Operario: {sesion.operario.nombre} | {sesion.puerta.nombre}")
        quien.setObjectName("subtitulo")

        # --- Sección de acciones ---
        btn_ingreso = QPushButton("Registrar ingreso")
        btn_salida = QPushButton("Registrar salida")
        btn_solicitud = QPushButton("Solicitar cambio / reportar error")
        btn_pago = QPushButton("Registrar pago")
        btn_cerrar = QPushButton("Cerrar sesión")

        for boton in (btn_ingreso, btn_salida, btn_solicitud, btn_pago):
            boton.setObjectName("accion_panel")
        btn_cerrar.setObjectName("secundario")

        acciones = QGridLayout()
        acciones.setSpacing(10)
        acciones.addWidget(btn_ingreso, 0, 0)
        acciones.addWidget(btn_salida, 0, 1)
        acciones.addWidget(btn_pago, 1, 0, 1, 2)
        acciones.addWidget(btn_solicitud, 2, 0, 1, 2)
        acciones.addWidget(btn_cerrar, 3, 0, 1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        layout.addWidget(titulo)
        layout.addWidget(quien)
        layout.addLayout(acciones)

        # --- Eventos ---
        btn_ingreso.clicked.connect(self._abrir_ingreso)
        btn_salida.clicked.connect(self._abrir_salida)
        btn_pago.clicked.connect(self._abrir_pago)
        btn_solicitud.clicked.connect(self._abrir_solicitud)
        btn_cerrar.clicked.connect(self.accept)  # "aceptado" = volver al login (ver main.py)

    # Cada método abre su ventana de forma modal.
    def _abrir_ingreso(self) -> None:
        IngresoView(
            self._sesion, self._servicios.ingreso, self._servicios.cliente, self
        ).exec()

    def _abrir_salida(self) -> None:
        SalidaView(self._sesion, self._servicios.salida, self).exec()

    def _abrir_pago(self) -> None:
        PagoView(self._sesion, self._servicios.pagos, self).exec()

    def _abrir_solicitud(self) -> None:
        SolicitudView(self._sesion, self._servicios.solicitud, self).exec()
