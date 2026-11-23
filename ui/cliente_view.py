"""Ventanas para la gestión de clientes y sus vehículos (RF-01, RF-02, RF-03, RF-05)."""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog,
                               QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from excepciones.errores import ParqueaderoError
from models.entidades import Propietario, Vehiculo
from models.enums import TipoVehiculo
from services.cliente_service import ClienteService
from ui.comun import ejecutar, limitar_campo, mostrar_error, mostrar_info, mostrar_ok


class NuevoClienteView(QDialog):
    """Formulario modal para registrar un nuevo cliente con clave inicial."""

    def __init__(self, servicio: ClienteService, parent=None):
        super().__init__(parent)
        self._servicio = servicio
        self.cliente_creado: Optional[Propietario] = None

        self.setWindowTitle("Nuevo cliente")
        self.setFixedWidth(360)

        titulo = QLabel("Nuevo cliente")
        titulo.setObjectName("titulo")

        lbl_nombre = QLabel("Nombre")
        lbl_nombre.setObjectName("campo_label")
        self.txt_nombre = QLineEdit()
        limitar_campo(self.txt_nombre, 50, tipo="texto")

        lbl_documento = QLabel("Documento")
        lbl_documento.setObjectName("campo_label")
        self.txt_documento = QLineEdit()
        limitar_campo(self.txt_documento, 10, tipo="digitos")

        lbl_telefono = QLabel("Teléfono (opcional)")
        lbl_telefono.setObjectName("campo_label")
        self.txt_telefono = QLineEdit()
        limitar_campo(self.txt_telefono, 10, tipo="digitos")

        lbl_clave = QLabel("Clave inicial (6 a 10 caracteres)")
        lbl_clave.setObjectName("campo_label")
        self.txt_clave = QLineEdit()
        self.txt_clave.setEchoMode(QLineEdit.EchoMode.Password)
        limitar_campo(self.txt_clave, 10)

        self.lbl_mensaje = QLabel("El documento no puede repetirse.")
        self.lbl_mensaje.setObjectName("campo_label")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(20)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("secundario")

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)
        fila_botones.addWidget(self.btn_guardar)
        fila_botones.addWidget(self.btn_cancelar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)

        layout.addWidget(lbl_nombre)
        layout.addWidget(self.txt_nombre)
        layout.addSpacing(4)

        layout.addWidget(lbl_documento)
        layout.addWidget(self.txt_documento)
        layout.addSpacing(4)

        layout.addWidget(lbl_telefono)
        layout.addWidget(self.txt_telefono)
        layout.addSpacing(4)

        layout.addWidget(lbl_clave)
        layout.addWidget(self.txt_clave)
        layout.addSpacing(4)

        layout.addWidget(self.lbl_mensaje)
        layout.addSpacing(6)
        layout.addLayout(fila_botones)

        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_cancelar.clicked.connect(self.reject)
        self.txt_clave.returnPressed.connect(self._guardar)

    def _guardar(self) -> None:
        try:
            self.cliente_creado = self._servicio.registrar_cliente(
                nombre=self.txt_nombre.text(),
                documento=self.txt_documento.text(),
                telefono=self.txt_telefono.text(),
                clave=self.txt_clave.text(),
            )
            self.accept()
        except ParqueaderoError as err:
            mostrar_error(self.lbl_mensaje, str(err))


class AgregarVehiculoView(QDialog):
    """Formulario modal para agregar un vehículo a un cliente."""

    def __init__(self, id_propietario: int, servicio: ClienteService, parent=None):
        super().__init__(parent)
        self._id_propietario = id_propietario
        self._servicio = servicio
        self.vehiculo_creado: Optional[Vehiculo] = None

        self.setWindowTitle("Agregar vehículo")
        self.setFixedWidth(360)

        lbl_placa = QLabel("Placa")
        lbl_placa.setObjectName("campo_label")
        self.txt_placa = QLineEdit()
        limitar_campo(self.txt_placa, 6, tipo="placa")
        self.txt_placa.textEdited.connect(lambda t: self.txt_placa.setText(t.upper()))

        lbl_tipo = QLabel("Tipo")
        lbl_tipo.setObjectName("campo_label")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Vehículo", TipoVehiculo.VEHICULO)
        self.cmb_tipo.addItem("Moto", TipoVehiculo.MOTO)

        lbl_marca = QLabel("Marca")
        lbl_marca.setObjectName("campo_label")
        self.txt_marca = QLineEdit()
        limitar_campo(self.txt_marca, 30, tipo="texto")

        lbl_color = QLabel("Color")
        lbl_color.setObjectName("campo_label")
        self.txt_color = QLineEdit()
        limitar_campo(self.txt_color, 20, tipo="texto")

        self.lbl_mensaje = QLabel("La placa no puede repetirse.")
        self.lbl_mensaje.setObjectName("campo_label")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(20)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("secundario")

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)
        fila_botones.addWidget(self.btn_guardar)
        fila_botones.addWidget(self.btn_cancelar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)

        layout.addWidget(lbl_placa)
        layout.addWidget(self.txt_placa)
        layout.addSpacing(4)

        layout.addWidget(lbl_tipo)
        layout.addWidget(self.cmb_tipo)
        layout.addSpacing(4)

        layout.addWidget(lbl_marca)
        layout.addWidget(self.txt_marca)
        layout.addSpacing(4)

        layout.addWidget(lbl_color)
        layout.addWidget(self.txt_color)
        layout.addSpacing(4)

        layout.addWidget(self.lbl_mensaje)
        layout.addSpacing(6)
        layout.addLayout(fila_botones)

        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_cancelar.clicked.connect(self.reject)
        self.txt_color.returnPressed.connect(self._guardar)

    def _guardar(self) -> None:
        try:
            self.vehiculo_creado = self._servicio.registrar_vehiculo(
                placa=self.txt_placa.text(),
                tipo=self.cmb_tipo.currentData(),
                marca=self.txt_marca.text(),
                color=self.txt_color.text(),
                id_propietario=self._id_propietario,
            )
            self.accept()
        except ParqueaderoError as err:
            mostrar_error(self.lbl_mensaje, str(err))


class EditarVehiculoView(QDialog):
    """Formulario modal para editar tipo, marca y color de un vehículo."""

    def __init__(self, vehiculo: Vehiculo, servicio: ClienteService, parent=None):
        super().__init__(parent)
        self._vehiculo = vehiculo
        self._servicio = servicio

        self.setWindowTitle("Editar vehículo")
        self.setFixedWidth(360)

        lbl_placa = QLabel("Placa")
        lbl_placa.setObjectName("campo_label")
        txt_placa = QLineEdit(vehiculo.placa)
        txt_placa.setEnabled(False)

        lbl_tipo = QLabel("Tipo")
        lbl_tipo.setObjectName("campo_label")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Vehículo", TipoVehiculo.VEHICULO)
        self.cmb_tipo.addItem("Moto", TipoVehiculo.MOTO)
        idx = 0 if vehiculo.tipo == TipoVehiculo.VEHICULO else 1
        self.cmb_tipo.setCurrentIndex(idx)
        self._esta_dentro = self._servicio.vehiculo_esta_dentro(vehiculo.placa)
        if self._esta_dentro:
            self.cmb_tipo.setEnabled(False)

        lbl_marca = QLabel("Marca")
        lbl_marca.setObjectName("campo_label")
        self.txt_marca = QLineEdit(vehiculo.marca)
        limitar_campo(self.txt_marca, 30, tipo="texto")

        lbl_color = QLabel("Color")
        lbl_color.setObjectName("campo_label")
        self.txt_color = QLineEdit(vehiculo.color)
        limitar_campo(self.txt_color, 20, tipo="texto")

        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(20)
        if self._esta_dentro:
            mostrar_error(
                self.lbl_mensaje,
                "El vehículo está dentro del parqueadero, "
                "sólo se puede modificar la marca y el color.",
            )

        self.btn_guardar = QPushButton("Guardar cambios")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("secundario")

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)
        fila_botones.addWidget(self.btn_guardar)
        fila_botones.addWidget(self.btn_cancelar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)

        layout.addWidget(lbl_placa)
        layout.addWidget(txt_placa)
        layout.addSpacing(4)

        layout.addWidget(lbl_tipo)
        layout.addWidget(self.cmb_tipo)
        layout.addSpacing(4)

        layout.addWidget(lbl_marca)
        layout.addWidget(self.txt_marca)
        layout.addSpacing(4)

        layout.addWidget(lbl_color)
        layout.addWidget(self.txt_color)
        layout.addSpacing(4)

        layout.addWidget(self.lbl_mensaje)
        layout.addSpacing(6)
        layout.addLayout(fila_botones)

        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_cancelar.clicked.connect(self.reject)

    def _guardar(self) -> None:
        try:
            self._servicio.actualizar_vehiculo(
                placa=self._vehiculo.placa,
                tipo=self.cmb_tipo.currentData(),
                marca=self.txt_marca.text(),
                color=self.txt_color.text(),
            )
            self.accept()
        except ParqueaderoError as err:
            mostrar_error(self.lbl_mensaje, str(err))


class RestablecerClaveView(QDialog):
    """Formulario modal para cambiar la contraseña del cliente."""

    def __init__(self, id_propietario: int, servicio: ClienteService, parent=None):
        super().__init__(parent)
        self._id_propietario = id_propietario
        self._servicio = servicio

        self.setWindowTitle("Restablecer clave")
        self.setFixedWidth(360)

        lbl_clave = QLabel("Nueva contraseña (6 a 10 caracteres)")
        lbl_clave.setObjectName("campo_label")
        self.txt_clave = QLineEdit()
        self.txt_clave.setEchoMode(QLineEdit.EchoMode.Password)
        limitar_campo(self.txt_clave, 10)

        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(20)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("secundario")

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)
        fila_botones.addWidget(self.btn_guardar)
        fila_botones.addWidget(self.btn_cancelar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)

        layout.addWidget(lbl_clave)
        layout.addWidget(self.txt_clave)
        layout.addWidget(self.lbl_mensaje)
        layout.addSpacing(6)
        layout.addLayout(fila_botones)

        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_cancelar.clicked.connect(self.reject)
        self.txt_clave.returnPressed.connect(self._guardar)

    def _guardar(self) -> None:
        try:
            self._servicio.restablecer_clave(self._id_propietario, self.txt_clave.text())
            self.accept()
        except ParqueaderoError as err:
            mostrar_error(self.lbl_mensaje, str(err))


class ClientesVehiculosView(QDialog):
    """Pantalla principal de gestión de clientes y sus vehículos."""

    def __init__(self, servicio: ClienteService, parent=None):
        super().__init__(parent)
        self._servicio = servicio
        self._clientes = []
        self._cliente_seleccionado: Optional[Propietario] = None
        self._vehiculos_cliente = []

        self.setWindowTitle("Autos Colombia - Clientes y vehículos")
        self.resize(820, 680)
        self.setMinimumSize(800, 640)

        # --- Buscador superior ---
        lbl_buscar = QLabel("Buscar por documento, nombre o placa")
        lbl_buscar.setObjectName("campo_label")
        self.txt_buscar = QLineEdit()
        limitar_campo(self.txt_buscar, 50)
        self.btn_buscar = QPushButton("Buscar")
        self.btn_nuevo_cliente = QPushButton("Nuevo cliente")

        fila_busqueda = QHBoxLayout()
        fila_busqueda.setSpacing(10)
        fila_busqueda.addWidget(self.txt_buscar, 1)
        fila_busqueda.addWidget(self.btn_buscar)
        fila_busqueda.addWidget(self.btn_nuevo_cliente)

        # --- Tabla de clientes (izquierda) ---
        self.tbl_clientes = QTableWidget()
        self.tbl_clientes.setColumnCount(3)
        self.tbl_clientes.setHorizontalHeaderLabels(["Documento", "Nombre", "Estado"])
        self.tbl_clientes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_clientes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_clientes.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_clientes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_clientes.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_clientes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_clientes.verticalHeader().setVisible(False)
        self.tbl_clientes.setShowGrid(False)
        self.tbl_clientes.setMinimumHeight(160)

        # --- Formulario Datos del cliente (derecha) ---
        lbl_datos_titulo = QLabel("Datos del cliente")
        lbl_datos_titulo.setObjectName("titulo")
        lbl_datos_titulo.setStyleSheet("font-size: 16px;")

        lbl_nombre = QLabel("Nombre")
        lbl_nombre.setObjectName("campo_label")
        self.txt_nombre = QLineEdit()
        limitar_campo(self.txt_nombre, 50, tipo="texto")

        lbl_documento = QLabel("Documento")
        lbl_documento.setObjectName("campo_label")
        self.txt_documento = QLineEdit()
        self.txt_documento.setReadOnly(True)

        lbl_telefono = QLabel("Teléfono")
        lbl_telefono.setObjectName("campo_label")
        self.txt_telefono = QLineEdit()
        limitar_campo(self.txt_telefono, 10, tipo="digitos")

        self.btn_guardar_cliente = QPushButton("Guardar cambios")
        self.btn_restablecer_clave = QPushButton("Restablecer clave")
        self.btn_restablecer_clave.setObjectName("secundario")

        fila_botones_cliente = QHBoxLayout()
        fila_botones_cliente.setSpacing(10)
        fila_botones_cliente.addWidget(self.btn_guardar_cliente)
        fila_botones_cliente.addWidget(self.btn_restablecer_clave)

        self.btn_inhabilitar_cliente = QPushButton("Inhabilitar cliente")
        self.btn_inhabilitar_cliente.setObjectName("secundario")

        panel_derecho_widget = QWidget()
        panel_derecho = QVBoxLayout(panel_derecho_widget)
        panel_derecho.setContentsMargins(0, 0, 0, 0)
        panel_derecho.setSpacing(6)
        panel_derecho.addWidget(lbl_datos_titulo)
        panel_derecho.addWidget(lbl_nombre)
        panel_derecho.addWidget(self.txt_nombre)
        panel_derecho.addWidget(lbl_documento)
        panel_derecho.addWidget(self.txt_documento)
        panel_derecho.addWidget(lbl_telefono)
        panel_derecho.addWidget(self.txt_telefono)
        panel_derecho.addSpacing(4)
        panel_derecho.addLayout(fila_botones_cliente)
        panel_derecho.addWidget(self.btn_inhabilitar_cliente)

        self.tbl_clientes.setMinimumHeight(240)

        seccion_superior = QHBoxLayout()
        seccion_superior.setSpacing(20)
        seccion_superior.addWidget(self.tbl_clientes, 1)
        seccion_superior.addWidget(panel_derecho_widget, 1)

        # --- Sección inferior: Vehículos del cliente ---
        lbl_vehiculos_titulo = QLabel("Vehículos del cliente")
        lbl_vehiculos_titulo.setObjectName("titulo")
        lbl_vehiculos_titulo.setStyleSheet("font-size: 16px;")

        self.tbl_vehiculos = QTableWidget()
        self.tbl_vehiculos.setColumnCount(5)
        self.tbl_vehiculos.setHorizontalHeaderLabels(["Placa", "Tipo", "Marca", "Color", "Estado"])
        self.tbl_vehiculos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_vehiculos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_vehiculos.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_vehiculos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_vehiculos.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_vehiculos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_vehiculos.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_vehiculos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_vehiculos.verticalHeader().setVisible(False)
        self.tbl_vehiculos.setShowGrid(False)
        self.tbl_vehiculos.setMinimumHeight(130)

        self.btn_agregar_vehiculo = QPushButton("Agregar vehículo")
        self.btn_editar_vehiculo = QPushButton("Editar vehículo")
        self.btn_editar_vehiculo.setObjectName("secundario")
        self.btn_inhabilitar_vehiculo = QPushButton("Inhabilitar vehículo")
        self.btn_inhabilitar_vehiculo.setObjectName("secundario")

        fila_botones_veh = QHBoxLayout()
        fila_botones_veh.setSpacing(10)
        fila_botones_veh.addWidget(self.btn_agregar_vehiculo)
        fila_botones_veh.addWidget(self.btn_editar_vehiculo)
        fila_botones_veh.addWidget(self.btn_inhabilitar_vehiculo)
        fila_botones_veh.addStretch()

        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        layout.addWidget(lbl_buscar)
        layout.addLayout(fila_busqueda)
        layout.addSpacing(6)
        layout.addLayout(seccion_superior)
        layout.addSpacing(8)
        layout.addWidget(lbl_vehiculos_titulo)
        layout.addWidget(self.tbl_vehiculos, 1)
        layout.addLayout(fila_botones_veh)
        layout.addWidget(self.lbl_mensaje)

        # --- Eventos ---
        self.btn_buscar.clicked.connect(self._buscar)
        self.txt_buscar.returnPressed.connect(self._buscar)
        self.btn_nuevo_cliente.clicked.connect(self._abrir_nuevo_cliente)
        self.tbl_clientes.itemSelectionChanged.connect(self._al_seleccionar_cliente)
        self.tbl_clientes.currentCellChanged.connect(lambda r, c, pr, pc: self._al_seleccionar_cliente(r))
        self.btn_guardar_cliente.clicked.connect(self._guardar_cliente)
        self.btn_restablecer_clave.clicked.connect(self._abrir_restablecer_clave)
        self.btn_inhabilitar_cliente.clicked.connect(self._alternar_estado_cliente)
        self.tbl_vehiculos.itemSelectionChanged.connect(self._al_seleccionar_vehiculo)
        self.tbl_vehiculos.currentCellChanged.connect(lambda r, c, pr, pc: self._al_seleccionar_vehiculo(r))
        self.btn_agregar_vehiculo.clicked.connect(self._abrir_agregar_vehiculo)
        self.btn_editar_vehiculo.clicked.connect(self._abrir_editar_vehiculo)
        self.btn_inhabilitar_vehiculo.clicked.connect(self._alternar_estado_vehiculo)

        self._buscar()

    def _buscar(self) -> None:
        """Carga clientes que coincidan con el término."""
        termino = self.txt_buscar.text().strip()
        ok, clientes = ejecutar(self.lbl_mensaje, lambda: self._servicio.buscar_clientes(termino))
        if not ok:
            return

        self._clientes = clientes or []
        self.tbl_clientes.setRowCount(len(self._clientes))

        for row, cli in enumerate(self._clientes):
            estado_txt = "Habilitado" if cli.habilitado else "Inhabilitado"
            self.tbl_clientes.setItem(row, 0, QTableWidgetItem(cli.documento))
            self.tbl_clientes.setItem(row, 1, QTableWidgetItem(cli.nombre))
            self.tbl_clientes.setItem(row, 2, QTableWidgetItem(estado_txt))

        if self._clientes:
            self.tbl_clientes.setCurrentCell(0, 0)
            self._al_seleccionar_cliente(0)
        else:
            self._limpiar_detalles_cliente()

    def _al_seleccionar_cliente(self, row: Optional[int] = None) -> None:
        """Carga los datos y vehículos del cliente seleccionado."""
        if row is None or row < 0:
            row = self.tbl_clientes.currentRow()
        if row < 0:
            selected = self.tbl_clientes.selectedItems()
            if selected:
                row = selected[0].row()
        if row < 0 or row >= len(self._clientes):
            self._limpiar_detalles_cliente()
            return

        cliente = self._clientes[row]
        self._cliente_seleccionado = cliente

        self.txt_nombre.setText(cliente.nombre)
        self.txt_documento.setText(cliente.documento)
        self.txt_telefono.setText(cliente.telefono or "")

        if cliente.habilitado:
            self.btn_inhabilitar_cliente.setText("Inhabilitar cliente")
        else:
            self.btn_inhabilitar_cliente.setText("Habilitar cliente")

        self._cargar_vehiculos_cliente(cliente.id_propietario)

    def _limpiar_detalles_cliente(self) -> None:
        self._cliente_seleccionado = None
        self.txt_nombre.clear()
        self.txt_documento.clear()
        self.txt_telefono.clear()
        self.tbl_vehiculos.setRowCount(0)
        self._vehiculos_cliente = []

    def _cargar_vehiculos_cliente(self, id_propietario: int) -> None:
        """Llena la tabla de vehículos del cliente."""
        ok, vehiculos = ejecutar(
            self.lbl_mensaje, lambda: self._servicio.listar_vehiculos(id_propietario)
        )
        if not ok:
            return

        self._vehiculos_cliente = vehiculos or []
        self.tbl_vehiculos.setRowCount(len(self._vehiculos_cliente))

        for row, v in enumerate(self._vehiculos_cliente):
            tipo_txt = "Vehículo" if v.tipo == TipoVehiculo.VEHICULO else "Moto"
            estado_txt = "Habilitado" if v.habilitado else "Inhabilitado"

            self.tbl_vehiculos.setItem(row, 0, QTableWidgetItem(v.placa))
            self.tbl_vehiculos.setItem(row, 1, QTableWidgetItem(tipo_txt))
            self.tbl_vehiculos.setItem(row, 2, QTableWidgetItem(v.marca))
            self.tbl_vehiculos.setItem(row, 3, QTableWidgetItem(v.color))
            self.tbl_vehiculos.setItem(row, 4, QTableWidgetItem(estado_txt))

        if self._vehiculos_cliente:
            self.tbl_vehiculos.selectRow(0)
        else:
            self.btn_inhabilitar_vehiculo.setText("Inhabilitar vehículo")

    def _al_seleccionar_vehiculo(self, row: Optional[int] = None) -> None:
        if row is None or row < 0:
            row = self.tbl_vehiculos.currentRow()
        if row < 0:
            selected = self.tbl_vehiculos.selectedItems()
            if selected:
                row = selected[0].row()
        if row < 0 or row >= len(self._vehiculos_cliente):
            return
        veh = self._vehiculos_cliente[row]
        if veh.habilitado:
            self.btn_inhabilitar_vehiculo.setText("Inhabilitar vehículo")
        else:
            self.btn_inhabilitar_vehiculo.setText("Habilitar vehículo")

    def _abrir_nuevo_cliente(self) -> None:
        dlg = NuevoClienteView(self._servicio, self)
        if dlg.exec():
            mostrar_ok(self.lbl_mensaje, "Cliente registrado con éxito.")
            self._buscar()
            # Seleccionar el recién creado
            if dlg.cliente_creado:
                for row, c in enumerate(self._clientes):
                    if c.documento == dlg.cliente_creado.documento:
                        self.tbl_clientes.selectRow(row)
                        break

    def _guardar_cliente(self) -> None:
        if not self._cliente_seleccionado:
            mostrar_error(self.lbl_mensaje, "Selecciona un cliente para guardar cambios.")
            return

        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.actualizar_cliente(
                id_propietario=self._cliente_seleccionado.id_propietario,
                nombre=self.txt_nombre.text(),
                telefono=self.txt_telefono.text(),
            ),
        )
        if ok:
            mostrar_ok(self.lbl_mensaje, "Cambios guardados con éxito.")
            doc_actual = self._cliente_seleccionado.documento
            self._buscar()
            for row, c in enumerate(self._clientes):
                if c.documento == doc_actual:
                    self.tbl_clientes.selectRow(row)
                    break

    def _abrir_restablecer_clave(self) -> None:
        if not self._cliente_seleccionado:
            mostrar_error(self.lbl_mensaje, "Selecciona un cliente.")
            return
        dlg = RestablecerClaveView(self._cliente_seleccionado.id_propietario, self._servicio, self)
        if dlg.exec():
            mostrar_ok(self.lbl_mensaje, "Contraseña actualizada con éxito.")

    def _alternar_estado_cliente(self) -> None:
        if not self._cliente_seleccionado:
            mostrar_error(self.lbl_mensaje, "Selecciona un cliente.")
            return

        nuevo_estado = not self._cliente_seleccionado.habilitado
        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.cambiar_estado_cliente(
                self._cliente_seleccionado.id_propietario, nuevo_estado
            ),
        )
        if ok:
            if nuevo_estado:
                mostrar_ok(self.lbl_mensaje, "Cliente habilitado, junto con sus vehículos.")
            else:
                mostrar_ok(self.lbl_mensaje, "Cliente inhabilitado, junto con sus vehículos.")
            doc_actual = self._cliente_seleccionado.documento
            self._buscar()
            for row, c in enumerate(self._clientes):
                if c.documento == doc_actual:
                    self.tbl_clientes.selectRow(row)
                    break

    def _abrir_agregar_vehiculo(self) -> None:
        if not self._cliente_seleccionado:
            mostrar_error(self.lbl_mensaje, "Selecciona un cliente primero para agregar un vehículo.")
            return

        dlg = AgregarVehiculoView(self._cliente_seleccionado.id_propietario, self._servicio, self)
        if dlg.exec():
            mostrar_ok(self.lbl_mensaje, "Vehículo agregado con éxito.")
            self._cargar_vehiculos_cliente(self._cliente_seleccionado.id_propietario)

    def _abrir_editar_vehiculo(self) -> None:
        row = self.tbl_vehiculos.currentRow()
        if row < 0 or row >= len(self._vehiculos_cliente):
            mostrar_error(self.lbl_mensaje, "Selecciona un vehículo para editar.")
            return

        veh = self._vehiculos_cliente[row]
        dlg = EditarVehiculoView(veh, self._servicio, self)
        if dlg.exec():
            mostrar_ok(self.lbl_mensaje, "Vehículo actualizado con éxito.")
            self._cargar_vehiculos_cliente(self._cliente_seleccionado.id_propietario)

    def _alternar_estado_vehiculo(self) -> None:
        row = self.tbl_vehiculos.currentRow()
        if row < 0 or row >= len(self._vehiculos_cliente):
            mostrar_error(self.lbl_mensaje, "Selecciona un vehículo.")
            return

        veh = self._vehiculos_cliente[row]
        nuevo_estado = not veh.habilitado
        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.cambiar_estado_vehiculo(veh.placa, nuevo_estado),
        )
        if ok:
            accion = "habilitado" if nuevo_estado else "inhabilitado"
            mostrar_ok(self.lbl_mensaje, f"Vehículo {accion} correctamente.")
            self._cargar_vehiculos_cliente(self._cliente_seleccionado.id_propietario)
