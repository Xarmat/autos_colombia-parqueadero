"""Registro de ingreso por placa, con alta contextual para placas no registradas."""
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout)

from excepciones.errores import VehiculoNoRegistrado
from models.entidades import Sesion
from services.cliente_service import ClienteService
from services.ingreso_service import IngresoService
from ui.cliente_ingreso_view import ClienteIngresoView
from ui.comun import ejecutar, limitar_campo, mostrar_info, mostrar_ok


class IngresoView(QDialog):
    def __init__(
        self, sesion: Sesion, servicio: IngresoService,
        servicio_cliente: ClienteService | None = None, parent=None,
    ):
        super().__init__(parent)
        self._sesion = sesion
        self._servicio = servicio
        self._servicio_cliente = servicio_cliente
        self._placa_no_registrada = False

        self.setWindowTitle("Registrar ingreso")
        self.setMinimumWidth(560)

        # --- Controles ---
        titulo = QLabel("Registrar ingreso")
        titulo.setObjectName("titulo")
        self.txt_placa = QLineEdit()
        self.txt_placa.setPlaceholderText("Placa, por ejemplo ABC123")
        limitar_campo(self.txt_placa, 6, tipo="placa")
        self.btn_verificar = QPushButton("Verificar")
        self.btn_crear_cliente = QPushButton("Crear cliente")
        self.btn_crear_cliente.setObjectName("secundario")
        self.btn_crear_cliente.setVisible(False)
        self.btn_crear_cliente.setEnabled(servicio_cliente is not None)
        self.lbl_mensaje = QLabel("")
        self.btn_confirmar = QPushButton("Confirmar ingreso")
        self.btn_confirmar.setEnabled(False)  # solo se habilita tras verificar con éxito
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("secundario")

        # --- Distribución ---
        fila_placa = QHBoxLayout()
        fila_placa.addWidget(self.txt_placa)
        fila_placa.addWidget(self.btn_verificar)
        fila_placa.addWidget(self.btn_crear_cliente)
        layout = QVBoxLayout(self)
        layout.addWidget(titulo)
        layout.addLayout(fila_placa)
        layout.addWidget(self.lbl_mensaje)
        layout.addWidget(self.btn_confirmar)
        layout.addWidget(btn_cerrar)

        # --- Eventos ---
        self.txt_placa.textEdited.connect(self._al_editar_placa)
        self.txt_placa.returnPressed.connect(self._verificar)
        self.btn_verificar.clicked.connect(self._verificar)
        self.btn_crear_cliente.clicked.connect(self._crear_cliente)
        self.btn_confirmar.clicked.connect(self._confirmar)
        btn_cerrar.clicked.connect(self.accept)

    def _al_editar_placa(self, texto: str) -> None:
        """Pone la placa en mayúsculas y borra resultados anteriores."""
        if texto != texto.upper():
            self.txt_placa.setText(texto.upper())
        self._reiniciar()

    def _reiniciar(self) -> None:
        self.btn_confirmar.setEnabled(False)
        self.btn_crear_cliente.setVisible(False)
        self._placa_no_registrada = False
        mostrar_info(self.lbl_mensaje, "")

    def _verificar(self) -> None:
        """Paso 1: confirma únicamente que la placa puede ingresar."""
        self._reiniciar()
        def verificar():
            try:
                return self._servicio.verificar_ingreso(self.txt_placa.text())
            except VehiculoNoRegistrado:
                self._placa_no_registrada = True
                raise

        ok, _ = ejecutar(self.lbl_mensaje, verificar)
        if not ok:
            self.btn_crear_cliente.setVisible(
                self._placa_no_registrada and self._servicio_cliente is not None
            )
            return
        mostrar_info(self.lbl_mensaje, "Placa registrada y habilitada. Confirma el ingreso.")
        self.btn_confirmar.setEnabled(True)

    def _crear_cliente(self) -> None:
        if not self._placa_no_registrada or self._servicio_cliente is None:
            return
        dialogo = ClienteIngresoView(
            self.txt_placa.text(), self._servicio_cliente, self._sesion, self
        )
        if dialogo.exec():
            self._verificar()

    def _confirmar(self) -> None:
        """Paso 2: asigna la celda y registra el ingreso."""
        ok, movimiento = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.registrar_ingreso(self.txt_placa.text(), self._sesion))
        self.btn_confirmar.setEnabled(False)  # evita registrar dos veces con doble clic
        if ok:
            mostrar_ok(self.lbl_mensaje, "Ingreso registrado.")
