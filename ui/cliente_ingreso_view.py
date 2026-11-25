"""Alta contextual de un cliente y el vehículo cuya placa está por ingresar."""
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout,
)
from PySide6.QtCore import QDate

from models.entidades import Sesion
from models.enums import MedioPago, TipoVehiculo
from services.cliente_service import ClienteService
from ui.comun import ejecutar, limitar_campo, mostrar_ok
from ui.pago_view import ComprobantePagoView


class ClienteIngresoView(QDialog):
    def __init__(
        self, placa: str, servicio: ClienteService, sesion: Sesion, parent=None
    ):
        super().__init__(parent)
        self._servicio = servicio
        self._sesion = sesion
        self.setWindowTitle("Registrar cliente y vehículo")
        self.setMinimumWidth(390)

        self.txt_nombre = QLineEdit()
        limitar_campo(self.txt_nombre, 30, tipo="texto")
        self.txt_documento = QLineEdit()
        limitar_campo(self.txt_documento, 10, tipo="digitos")
        self.txt_telefono = QLineEdit()
        limitar_campo(self.txt_telefono, 10, tipo="digitos")
        self.txt_clave = QLineEdit()
        self.txt_clave.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_clave.setPlaceholderText("6 a 10 caracteres")
        limitar_campo(self.txt_clave, 10)

        self.txt_placa = QLineEdit(placa.strip().upper())
        limitar_campo(self.txt_placa, 6, tipo="placa")
        self.txt_placa.setReadOnly(True)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Vehículo", TipoVehiculo.VEHICULO)
        self.cmb_tipo.addItem("Moto", TipoVehiculo.MOTO)
        self.txt_marca = QLineEdit()
        limitar_campo(self.txt_marca, 30, tipo="texto")
        self.txt_color = QLineEdit()
        limitar_campo(self.txt_color, 20, tipo="texto")
        self.fecha_inicio = QDateEdit(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setMinimumDate(QDate.currentDate())
        self.fecha_inicio.setDisplayFormat("dd/MM/yyyy")
        self.cmb_medio = QComboBox()
        self.cmb_medio.addItem("Efectivo", MedioPago.EFECTIVO)
        self.cmb_medio.addItem("Código QR", MedioPago.QR)
        self.cmb_medio.addItem("Recibo bancario presentado", MedioPago.RECIBO_BANCARIO)
        self.lbl_mensaje = QLabel(
            "El pago inicial es adelantado. Si el recibo es bancario, revísalo antes de registrarlo."
        )
        self.lbl_mensaje.setWordWrap(True)

        formulario = QFormLayout()
        formulario.addRow("Nombre completo", self.txt_nombre)
        formulario.addRow("Documento", self.txt_documento)
        formulario.addRow("Teléfono (opcional)", self.txt_telefono)
        formulario.addRow("Clave inicial", self.txt_clave)
        formulario.addRow("Placa", self.txt_placa)
        formulario.addRow("Tipo", self.cmb_tipo)
        formulario.addRow("Marca", self.txt_marca)
        formulario.addRow("Color", self.txt_color)
        formulario.addRow("Inicio de mensualidad", self.fecha_inicio)
        formulario.addRow("Medio de pago", self.cmb_medio)

        self.btn_guardar = QPushButton("Crear cliente y vehículo")
        self.btn_guardar.setObjectName("btn_entrar")
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        botones = QHBoxLayout()
        botones.addWidget(self.btn_guardar)
        botones.addWidget(btn_cancelar)

        layout = QVBoxLayout(self)
        layout.addLayout(formulario)
        layout.addWidget(self.lbl_mensaje)
        layout.addLayout(botones)

        self.btn_guardar.clicked.connect(self._guardar)
        btn_cancelar.clicked.connect(self.reject)

    def _guardar(self) -> None:
        fecha_inicio = self.fecha_inicio.date().toPython()
        ok, resultado = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.registrar_cliente_con_vehiculo(
                nombre=self.txt_nombre.text(),
                documento=self.txt_documento.text(),
                telefono=self.txt_telefono.text(),
                clave=self.txt_clave.text(),
                placa=self.txt_placa.text(),
                tipo=self.cmb_tipo.currentData(),
                marca=self.txt_marca.text(),
                color=self.txt_color.text(),
                fecha_inicio=fecha_inicio,
                medio_pago=self.cmb_medio.currentData(),
                sesion=self._sesion,
            ),
        )
        if ok:
            _, _, comprobante = resultado
            mostrar_ok(self.lbl_mensaje, "Cliente, vehículo y pago registrados.")
            ComprobantePagoView(comprobante, self).exec()
            self.accept()
