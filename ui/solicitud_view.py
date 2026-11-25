"""Formulario para que el operario reporte un error al administrador."""
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QVBoxLayout,
)

from models.entidades import Sesion
from services.solicitud_service import SolicitudService
from ui.comun import ejecutar, limitar_campo, limitar_texto, mostrar_ok


class SolicitudView(QDialog):
    def __init__(self, sesion: Sesion, servicio: SolicitudService, parent=None):
        super().__init__(parent)
        self._sesion = sesion
        self._servicio = servicio
        self.setWindowTitle("Solicitar corrección al administrador")
        self.setMinimumWidth(440)

        titulo = QLabel("Reportar una situación")
        titulo.setObjectName("titulo")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Error en placa al ingresar", "ENTRADA")
        self.cmb_tipo.addItem("Error en placa al salir", "SALIDA")
        self.cmb_tipo.addItem("Corrección de celda", "CELDA")
        self.cmb_tipo.addItem("Otra situación", "OTRA")
        self.txt_placa = QLineEdit()
        self.txt_placa.setPlaceholderText("Placa relacionada (si aplica)")
        limitar_campo(self.txt_placa, 6, tipo="placa")
        self.txt_descripcion = QPlainTextEdit()
        self.txt_descripcion.setPlaceholderText(
            "Describe qué ocurrió para que el administrador pueda revisarlo."
        )
        self.txt_descripcion.setFixedHeight(120)
        limitar_texto(self.txt_descripcion, 1000)
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.btn_enviar = QPushButton("Enviar solicitud")
        self.btn_enviar.setObjectName("btn_entrar")
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        fila = QHBoxLayout()
        fila.addWidget(self.btn_enviar)
        fila.addWidget(btn_cancelar)

        layout = QVBoxLayout(self)
        layout.addWidget(titulo)
        layout.addWidget(QLabel("Tipo de solicitud"))
        layout.addWidget(self.cmb_tipo)
        layout.addWidget(QLabel("Placa"))
        layout.addWidget(self.txt_placa)
        layout.addWidget(QLabel("Situación"))
        layout.addWidget(self.txt_descripcion)
        layout.addWidget(self.lbl_mensaje)
        layout.addLayout(fila)

        self.cmb_tipo.currentIndexChanged.connect(self._actualizar_placa)
        self.btn_enviar.clicked.connect(self._enviar)
        btn_cancelar.clicked.connect(self.reject)
        self._actualizar_placa()

    def _actualizar_placa(self) -> None:
        requiere_placa = self.cmb_tipo.currentData() in {"ENTRADA", "SALIDA", "CELDA"}
        self.txt_placa.setEnabled(requiere_placa)
        if not requiere_placa:
            self.txt_placa.clear()

    def _enviar(self) -> None:
        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.crear(
                self._sesion,
                self.cmb_tipo.currentData(),
                self.txt_placa.text(),
                self.txt_descripcion.toPlainText(),
            ),
        )
        if ok:
            mostrar_ok(self.lbl_mensaje, "Solicitud enviada al administrador.")
            self.btn_enviar.setEnabled(False)
