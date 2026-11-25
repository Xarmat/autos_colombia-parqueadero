"""Administración de cuentas de operarios y administradores."""
from typing import Optional

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from models.entidades import Administrador, Operario
from models.enums import Turno
from services.administrador_service import AdministradorService
from ui.comun import ejecutar, limitar_campo, mostrar_ok


class _TablaCuentas(QTableWidget):
    """Permite ajustar columnas arrastrando sus bordes en el encabezado o las filas."""

    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self._columna_redimensionando: Optional[int] = None
        self._x_inicial = 0
        self._ancho_inicial = 0
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

    def _columna_en_borde(self, x: int) -> Optional[int]:
        encabezado = self.horizontalHeader()
        tolerancia = 5
        for columna in range(self.columnCount() - 1):
            borde = (
                encabezado.sectionViewportPosition(columna)
                + self.columnWidth(columna)
            )
            if abs(x - borde) <= tolerancia:
                return columna
        return None

    def eventFilter(self, origen, evento):
        if origen is not self.viewport():
            return super().eventFilter(origen, evento)

        if evento.type() == QEvent.Type.MouseButtonPress:
            if evento.button() == Qt.MouseButton.LeftButton:
                columna = self._columna_en_borde(evento.position().toPoint().x())
                if columna is not None:
                    self._columna_redimensionando = columna
                    self._x_inicial = evento.position().toPoint().x()
                    self._ancho_inicial = self.columnWidth(columna)
                    return True

        elif evento.type() == QEvent.Type.MouseMove:
            x = evento.position().toPoint().x()
            if self._columna_redimensionando is not None:
                ancho = self._ancho_inicial + x - self._x_inicial
                ancho = max(
                    self.horizontalHeader().minimumSectionSize(),
                    min(self.horizontalHeader().maximumSectionSize(), ancho),
                )
                self.setColumnWidth(self._columna_redimensionando, ancho)
                return True
            cursor = (
                Qt.CursorShape.SplitHCursor
                if self._columna_en_borde(x) is not None
                else Qt.CursorShape.ArrowCursor
            )
            self.viewport().setCursor(cursor)

        elif evento.type() == QEvent.Type.MouseButtonRelease:
            if self._columna_redimensionando is not None:
                self._columna_redimensionando = None
                cursor = (
                    Qt.CursorShape.SplitHCursor
                    if self._columna_en_borde(evento.position().toPoint().x()) is not None
                    else Qt.CursorShape.ArrowCursor
                )
                self.viewport().setCursor(cursor)
                return True

        return super().eventFilter(origen, evento)


class _CuentaView(QDialog):
    def __init__(self, servicio: AdministradorService, tipo: str,
                 cuenta=None, reemplazar: Optional[Operario] = None, parent=None):
        super().__init__(parent)
        self._servicio = servicio
        self._tipo = tipo
        self._cuenta = cuenta
        self._reemplazar = reemplazar
        self.setWindowTitle("Editar cuenta" if cuenta else "Nueva cuenta")
        self.setMinimumWidth(390)

        self.txt_nombre = QLineEdit(cuenta.nombre if cuenta else "")
        limitar_campo(self.txt_nombre, 30, tipo="texto")
        self.txt_usuario = QLineEdit(cuenta.usuario if cuenta else "")
        self.txt_clave = QLineEdit()
        self.txt_clave.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_clave.setPlaceholderText(
            "Vacío = conservar; 6 a 10 caracteres" if cuenta else "6 a 10 caracteres"
        )
        limitar_campo(self.txt_clave, 10)
        limitar_campo(self.txt_usuario, 14, tipo="alfanumerico")
        self.lbl_turno = QLabel("Turno")
        self.cmb_turno = QComboBox()
        self.cmb_turno.addItem("Día", Turno.DIA)
        self.cmb_turno.addItem("Noche", Turno.NOCHE)
        self.cmb_reemplazo = QComboBox()
        self.lbl_reemplazo = QLabel("Operario que reemplaza")
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)

        formulario = QFormLayout()
        formulario.addRow("Nombre", self.txt_nombre)
        formulario.addRow("Usuario", self.txt_usuario)
        formulario.addRow("Contraseña", self.txt_clave)
        if tipo == "operario":
            formulario.addRow(self.lbl_turno, self.cmb_turno)
            if not cuenta:
                formulario.addRow(self.lbl_reemplazo, self.cmb_reemplazo)
        else:
            self.lbl_turno.hide()
            self.cmb_turno.hide()
            self.lbl_reemplazo.hide()
            self.cmb_reemplazo.hide()

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("btn_entrar")
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        fila = QHBoxLayout()
        fila.addWidget(self.btn_guardar)
        fila.addWidget(btn_cancelar)

        layout = QVBoxLayout(self)
        layout.addLayout(formulario)
        layout.addWidget(self.lbl_mensaje)
        layout.addLayout(fila)

        if cuenta and tipo == "operario":
            self.cmb_turno.setCurrentIndex(
                self.cmb_turno.findData(cuenta.turno)
            )
        self.cmb_turno.currentIndexChanged.connect(self._cargar_reemplazos)
        self.btn_guardar.clicked.connect(self._guardar)
        btn_cancelar.clicked.connect(self.reject)
        if tipo == "operario" and not cuenta:
            self._cargar_reemplazos()

    def _cargar_reemplazos(self) -> None:
        turno = self.cmb_turno.currentData()
        self.cmb_reemplazo.clear()
        self.cmb_reemplazo.addItem("Crear en un puesto disponible", None)
        ok, operarios = ejecutar(self.lbl_mensaje, self._servicio.listar_operarios)
        if not ok:
            return
        for operario in operarios:
            if operario.habilitado and operario.turno == turno:
                self.cmb_reemplazo.addItem(
                    f"{operario.nombre} ({operario.usuario})", operario.id_operario
                )
        if self._reemplazar is not None:
            idx = self.cmb_reemplazo.findData(self._reemplazar.id_operario)
            if idx >= 0:
                self.cmb_reemplazo.setCurrentIndex(idx)
            self.cmb_reemplazo.setEnabled(False)

    def _guardar(self) -> None:
        nombre = self.txt_nombre.text()
        usuario = self.txt_usuario.text()
        clave = self.txt_clave.text()
        if self._tipo == "operario":
            turno = self.cmb_turno.currentData()
            if self._cuenta:
                accion = lambda: self._servicio.actualizar_operario(
                    self._cuenta.id_operario, nombre, usuario, turno, clave
                )
            else:
                accion = lambda: self._servicio.crear_operario(
                    nombre, usuario, clave, turno, self.cmb_reemplazo.currentData()
                )
        elif self._cuenta:
            accion = lambda: self._servicio.actualizar_administrador(
                self._cuenta.id_administrador, nombre, usuario, clave
            )
        else:
            accion = lambda: self._servicio.crear_administrador(nombre, usuario, clave)
        ok, _ = ejecutar(self.lbl_mensaje, accion)
        if ok:
            mostrar_ok(self.lbl_mensaje, "Cuenta guardada.")
            self.accept()


class PersonalView(QDialog):
    def __init__(self, servicio: AdministradorService, parent=None):
        super().__init__(parent)
        self._servicio = servicio
        self._operarios = []
        self._administradores = []
        self.setWindowTitle("Autos Colombia - Personal y cuentas")
        self.setMinimumSize(640, 430)
        self.setMaximumSize(980, 560)
        self.resize(820, 500)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Operarios", "operario")
        self.cmb_tipo.addItem("Administrador", "administrador")
        self.tabla = _TablaCuentas()
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Usuario", "Turno", "Estado"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tabla.setShowGrid(True)
        self.tabla.setGridStyle(Qt.PenStyle.SolidLine)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: #52525b; }")
        encabezado = self.tabla.horizontalHeader()
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        encabezado.setMinimumSectionSize(80)
        encabezado.setMaximumSectionSize(320)
        for columna, ancho in enumerate((280, 170, 110, 160)):
            self.tabla.setColumnWidth(columna, ancho)
        self.tabla.setFixedHeight(190)
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.btn_nuevo = QPushButton("Crear cuenta")
        self.btn_editar = QPushButton("Editar")
        self.btn_estado = QPushButton("Desactivar / reemplazar")
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_nuevo.setObjectName("accion_panel")
        self.btn_editar.setObjectName("secundario")
        self.btn_estado.setObjectName("secundario")

        botones = QHBoxLayout()
        for boton in (self.btn_nuevo, self.btn_editar, self.btn_estado, self.btn_cerrar):
            botones.addWidget(boton)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Cuentas del sistema"))
        layout.addWidget(self.cmb_tipo)
        layout.addWidget(self.tabla, 1)
        layout.addWidget(self.lbl_mensaje)
        layout.addLayout(botones)

        self.cmb_tipo.currentIndexChanged.connect(self._refrescar)
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        self.btn_nuevo.clicked.connect(self._crear)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_estado.clicked.connect(self._cambiar_estado)
        self.btn_cerrar.clicked.connect(self.accept)
        self._refrescar()

    def _cuentas(self):
        return self._operarios if self.cmb_tipo.currentData() == "operario" else self._administradores

    def _refrescar(self) -> None:
        ok, resultado = ejecutar(
            self.lbl_mensaje,
            self._servicio.listar_operarios if self.cmb_tipo.currentData() == "operario"
            else self._servicio.listar_administradores,
        )
        if not ok:
            return
        if self.cmb_tipo.currentData() == "operario":
            self._operarios = resultado
        else:
            self._administradores = resultado
        cuentas = self._cuentas()
        self.tabla.setRowCount(len(cuentas))
        for fila, cuenta in enumerate(cuentas):
            turno = cuenta.turno.value if isinstance(cuenta, Operario) else "—"
            valores = (cuenta.nombre, cuenta.usuario, turno,
                       "Habilitada" if cuenta.habilitado else "Inhabilitada")
            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                item.setToolTip(cuenta.nombre if columna == 0 else valor)
                self.tabla.setItem(fila, columna, item)
        self._actualizar_botones()

    def _seleccionada(self):
        fila = self.tabla.currentRow()
        cuentas = self._cuentas()
        return cuentas[fila] if 0 <= fila < len(cuentas) else None

    def _actualizar_botones(self) -> None:
        es_operario = self.cmb_tipo.currentData() == "operario"
        self.btn_nuevo.setVisible(es_operario)
        self.btn_estado.setVisible(es_operario)
        cuenta = self._seleccionada()
        self.btn_editar.setEnabled(cuenta is not None)
        self.btn_estado.setEnabled(es_operario and cuenta is not None)
        if cuenta is not None:
            self.btn_estado.setText(
                "Desactivar / reemplazar" if cuenta.habilitado else "Reactivar"
            )

    def _crear(self) -> None:
        tipo = self.cmb_tipo.currentData()
        if _CuentaView(self._servicio, tipo, parent=self).exec():
            self._refrescar()

    def _editar(self) -> None:
        cuenta = self._seleccionada()
        if cuenta is None:
            return
        if _CuentaView(self._servicio, self.cmb_tipo.currentData(), cuenta, parent=self).exec():
            self._refrescar()

    def _cambiar_estado(self) -> None:
        cuenta = self._seleccionada()
        if cuenta is None:
            return
        if isinstance(cuenta, Operario):
            if not cuenta.habilitado:
                ok, _ = ejecutar(
                    self.lbl_mensaje,
                    lambda: self._servicio.reactivar_operario(cuenta.id_operario),
                )
            else:
                dialogo = _CuentaView(
                    self._servicio, "operario", reemplazar=cuenta, parent=self
                )
                if dialogo.exec():
                    self._refrescar()
                    mostrar_ok(self.lbl_mensaje, "Operario reemplazado.")
                return
        else:
            habilitar = not cuenta.habilitado
            ok, _ = ejecutar(
                self.lbl_mensaje,
                lambda: self._servicio.cambiar_estado_administrador(
                    cuenta.id_administrador, habilitar
                ),
            )
        if ok:
            mostrar_ok(self.lbl_mensaje, "Estado de la cuenta actualizado.")
            self._refrescar()
