"""Ventana de inicio de sesión.

Flujo: el operario escribe usuario y clave, elige la puerta desde la que trabaja
y pulsa Entrar. Si las credenciales son válidas se cierra con éxito y deja la
Sesion (operario + puerta) disponible en `self.sesion`.
"""
from typing import Optional

from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout)

from models.entidades import Propietario, Sesion
from services.auth_service import AuthService
from services.cliente_service import ClienteService
from ui.comun import ejecutar, limitar_campo, mostrar_error


class LoginView(QDialog):
    def __init__(self, auth: AuthService, cliente_servicio: Optional[ClienteService] = None, parent=None):
        super().__init__(parent)
        self._auth = auth
        self._cliente_servicio = cliente_servicio
        self.sesion: Optional[Sesion] = None
        self.cliente: Optional[Propietario] = None
        self.rol_autenticado: str = "operario"
        self._rol_actual = "operario"

        self.setWindowTitle("Autos Colombia - Inicio de sesión")
        self.setFixedWidth(380)

        # --- Controles ---
        titulo = QLabel("Autos Colombia")
        titulo.setObjectName("titulo")

        lbl_rol = QLabel("Ingresar como")
        lbl_rol.setObjectName("campo_label")

        self.btn_operario = QPushButton("Operario")
        self.btn_operario.setObjectName("segmento_activo")
        self.btn_cliente = QPushButton("Cliente")
        self.btn_cliente.setObjectName("segmento_inactivo")

        fila_roles = QHBoxLayout()
        fila_roles.setSpacing(10)
        fila_roles.addWidget(self.btn_operario)
        fila_roles.addWidget(self.btn_cliente)

        self.lbl_usuario = QLabel("Usuario o documento")
        self.lbl_usuario.setObjectName("campo_label")
        self.txt_usuario = QLineEdit()
        limitar_campo(self.txt_usuario, 20, tipo="alfanumerico")

        lbl_clave = QLabel("Contraseña")
        lbl_clave.setObjectName("campo_label")
        self.txt_clave = QLineEdit()
        self.txt_clave.setEchoMode(QLineEdit.EchoMode.Password)
        limitar_campo(self.txt_clave, 20)

        self.lbl_puerta = QLabel("Puerta (solo operarios)")
        self.lbl_puerta.setObjectName("campo_label")
        self.cmb_puerta = QComboBox()

        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(22)

        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.setObjectName("btn_entrar")
        self.btn_entrar.setDefault(True)

        # --- Distribución ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)

        layout.addWidget(titulo)
        layout.addSpacing(10)

        layout.addWidget(lbl_rol)
        layout.addLayout(fila_roles)
        layout.addSpacing(6)

        layout.addWidget(self.lbl_usuario)
        layout.addWidget(self.txt_usuario)
        layout.addSpacing(6)

        layout.addWidget(lbl_clave)
        layout.addWidget(self.txt_clave)
        layout.addSpacing(6)

        layout.addWidget(self.lbl_puerta)
        layout.addWidget(self.cmb_puerta)

        layout.addWidget(self.lbl_mensaje)
        layout.addWidget(self.btn_entrar)

        # --- Eventos ---
        self.btn_operario.clicked.connect(lambda: self._seleccionar_rol("operario"))
        self.btn_cliente.clicked.connect(lambda: self._seleccionar_rol("cliente"))
        self.btn_entrar.clicked.connect(self._entrar)
        self.txt_usuario.returnPressed.connect(self._entrar)
        self.txt_clave.returnPressed.connect(self._entrar)

        self._cargar_puertas()

    def _seleccionar_rol(self, rol: str) -> None:
        """Alterna el rol activo entre operario y cliente."""
        self._rol_actual = rol
        if rol == "operario":
            self.btn_operario.setObjectName("segmento_activo")
            self.btn_cliente.setObjectName("segmento_inactivo")
            self.cmb_puerta.setEnabled(True)
            self.lbl_puerta.setStyleSheet("")
            self.lbl_usuario.setText("Usuario o documento")
            limitar_campo(self.txt_usuario, 20, tipo="alfanumerico")
        else:
            self.btn_operario.setObjectName("segmento_inactivo")
            self.btn_cliente.setObjectName("segmento_activo")
            self.cmb_puerta.setEnabled(False)
            self.lbl_puerta.setStyleSheet("color: #666666;")
            self.lbl_usuario.setText("Documento")
            limitar_campo(self.txt_usuario, 10, tipo="digitos")

        # Refrescar hojas de estilo en los botones de selección
        for btn in (self.btn_operario, self.btn_cliente):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _cargar_puertas(self) -> None:
        """Llena la lista de puertas desde la base al abrir la ventana."""
        ok, puertas = ejecutar(self.lbl_mensaje, self._auth.listar_puertas)
        if ok and puertas:
            for puerta in puertas:
                self.cmb_puerta.addItem(puerta.nombre, puerta)

    def _entrar(self) -> None:
        """Valida las credenciales; si son correctas, guarda la sesión o el cliente y cierra."""
        if self._rol_actual == "cliente":
            if self._cliente_servicio is None:
                mostrar_error(self.lbl_mensaje, "Servicio de clientes no disponible.")
                return

            ok, cliente = ejecutar(
                self.lbl_mensaje,
                lambda: self._cliente_servicio.autenticar_cliente(
                    self.txt_usuario.text(), self.txt_clave.text()
                ),
            )
            if ok:
                self.cliente = cliente
                self.rol_autenticado = "cliente"
                self.accept()
            else:
                self.txt_clave.clear()
                self.txt_clave.setFocus()
            return

        puerta = self.cmb_puerta.currentData()
        if puerta is None:
            mostrar_error(self.lbl_mensaje, "No hay puertas configuradas en el sistema.")
            return

        ok, operario = ejecutar(
            self.lbl_mensaje,
            lambda: self._auth.iniciar_sesion(self.txt_usuario.text(), self.txt_clave.text()),
        )
        if ok:
            self.sesion = Sesion(operario=operario, puerta=puerta)
            self.rol_autenticado = "operario"
            self.accept()
        else:
            self.txt_clave.clear()
            self.txt_clave.setFocus()
