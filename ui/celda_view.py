"""Pantallas de Estado de celdas (HU-C1) y Corrección de celda (HU-C2).

Estado de celdas:
  - Filtros por tipo (Todas / Motos / Vehículos) y estado (Todas / Libres / Ocupadas).
  - Cuadrícula de tarjetas de colores: verde=libre, rojo=ocupada con placa.
  - Botón "Corregir celda" habilitado solo cuando se selecciona una celda ocupada.

Corrección de celda:
  - Selector de vehículo (placa - celda actual) pre-rellenado con la selección.
  - Celda actual (solo lectura) y selector de celda destino (libres del mismo tipo).
  - Campo de motivo (texto libre).
  - Botón "Aplicar corrección".
"""
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
    QLineEdit, QGridLayout, QFrame,
)

from models.entidades import Sesion
from models.enums import TipoVehiculo
from repositories.celda_estado_repository import CeldaConEstado
from services.celda_service import CeldaService
from ui.comun import (ejecutar, limitar_texto, mostrar_error, mostrar_info,
                      mostrar_ok)


# ─────────────────────────── Tarjeta de celda ────────────────────────────────

class _TarjetaCelda(QPushButton):
    """Botón cuadrado que representa una celda con su código y estado."""

    _ESTILO_LIBRE = (
        "QPushButton{"
        "  background:#1a3a1a; color:#4ade80; border:1px solid #166534;"
        "  border-radius:6px; font-size:11px; font-weight:600; padding:2px;"
        "}"
        "QPushButton:hover{ background:#1e4a1e; }"
        "QPushButton:checked{"
        "  background:#166534; border:2px solid #4ade80; color:#ffffff;"
        "}"
    )
    _ESTILO_OCUPADA = (
        "QPushButton{"
        "  background:#3a1a1a; color:#fca5a5; border:1px solid #991b1b;"
        "  border-radius:6px; font-size:11px; font-weight:600; padding:2px;"
        "}"
        "QPushButton:hover{ background:#4a1a1a; }"
        "QPushButton:checked{"
        "  background:#991b1b; border:2px solid #ef4444; color:#ffffff;"
        "}"
    )

    def __init__(self, celda: CeldaConEstado, parent=None):
        super().__init__(parent)
        self.celda = celda
        self.setCheckable(True)
        self.setFixedSize(72, 56)
        self.setStyleSheet(self._ESTILO_LIBRE if celda.libre else self._ESTILO_OCUPADA)
        texto = celda.codigo + "\n" + (celda.placa if celda.placa else "libre")
        self.setText(texto)
        self.setCursor(Qt.PointingHandCursor)


# ─────────────────────────── Ventana corrección ───────────────────────────────

class CorregirCeldaView(QDialog):
    """Modal para reubicar un vehículo en otra celda libre del mismo tipo."""

    def __init__(
        self,
        celdas_ocupadas: List[CeldaConEstado],
        seleccionada: Optional[CeldaConEstado],
        sesion: Sesion,
        servicio: CeldaService,
        parent=None,
    ):
        super().__init__(parent)
        self._sesion = sesion
        self._servicio = servicio
        self._celdas_ocupadas = celdas_ocupadas

        self.setWindowTitle("Corregir celda de un vehículo")
        self.setFixedWidth(480)

        # ── Título ──────────────────────────────────────────────────
        titulo = QLabel("Corregir celda")
        titulo.setObjectName("titulo")

        # ── Selector de vehículo ─────────────────────────────────────
        lbl_vehiculo = QLabel("Vehículo")
        lbl_vehiculo.setObjectName("campo_label")
        self.cmb_vehiculo = QComboBox()
        for c in celdas_ocupadas:
            self.cmb_vehiculo.addItem(f"{c.placa} - celda {c.codigo}", c)

        # Pre-seleccionar la celda que venía marcada en la cuadrícula
        if seleccionada is not None:
            for i in range(self.cmb_vehiculo.count()):
                if self.cmb_vehiculo.itemData(i) is seleccionada:
                    self.cmb_vehiculo.setCurrentIndex(i)
                    break

        # ── Celda actual y destino ───────────────────────────────────
        lbl_actual = QLabel("Celda actual")
        lbl_actual.setObjectName("campo_label")
        self.txt_actual = QLineEdit()
        self.txt_actual.setReadOnly(True)

        lbl_destino = QLabel("Celda destino")
        lbl_destino.setObjectName("campo_label")
        self.cmb_destino = QComboBox()

        fila_celdas = QHBoxLayout()
        fila_celdas.setSpacing(12)
        col_actual = QVBoxLayout()
        col_actual.addWidget(lbl_actual)
        col_actual.addWidget(self.txt_actual)
        col_destino = QVBoxLayout()
        col_destino.addWidget(lbl_destino)
        col_destino.addWidget(self.cmb_destino)
        fila_celdas.addLayout(col_actual, 1)
        fila_celdas.addLayout(col_destino, 1)

        lbl_hint = QLabel("Solo se listan celdas libres del mismo tipo.")
        lbl_hint.setObjectName("campo_label")

        # ── Motivo ───────────────────────────────────────────────────
        lbl_motivo = QLabel("Motivo")
        lbl_motivo.setObjectName("campo_label")
        self.txt_motivo = QPlainTextEdit()
        self.txt_motivo.setPlaceholderText(
            "Ej. El vehículo se parqueó en otra celda por indicación del cliente."
        )
        self.txt_motivo.setFixedHeight(90)
        limitar_texto(self.txt_motivo, 250)

        # ── Mensaje y botones ────────────────────────────────────────
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(20)

        self.btn_aplicar = QPushButton("Aplicar corrección")
        self.btn_aplicar.setObjectName("btn_entrar")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("secundario")

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)
        fila_botones.addWidget(self.btn_aplicar)
        fila_botones.addWidget(self.btn_cancelar)

        # ── Layout ──────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)

        layout.addWidget(titulo)
        layout.addSpacing(4)
        layout.addWidget(lbl_vehiculo)
        layout.addWidget(self.cmb_vehiculo)
        layout.addSpacing(4)
        layout.addLayout(fila_celdas)
        layout.addWidget(lbl_hint)
        layout.addSpacing(4)
        layout.addWidget(lbl_motivo)
        layout.addWidget(self.txt_motivo)
        layout.addWidget(self.lbl_mensaje)
        layout.addSpacing(6)
        layout.addLayout(fila_botones)

        # ── Eventos ─────────────────────────────────────────────────
        self.cmb_vehiculo.currentIndexChanged.connect(self._al_cambiar_vehiculo)
        self.btn_aplicar.clicked.connect(self._aplicar)
        self.btn_cancelar.clicked.connect(self.reject)

        # Inicializar con el primer vehículo
        self._al_cambiar_vehiculo()

    def _al_cambiar_vehiculo(self) -> None:
        """Actualiza celda actual y recarga la lista de celdas destino."""
        celda: Optional[CeldaConEstado] = self.cmb_vehiculo.currentData()
        if celda is None:
            self.txt_actual.clear()
            self.cmb_destino.clear()
            return

        self.txt_actual.setText(celda.codigo)

        ok, libres = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.listar_celdas_libres(celda.tipo),
        )
        self.cmb_destino.clear()
        if ok and libres:
            for c in libres:
                self.cmb_destino.addItem(c.codigo, c)
            mostrar_info(self.lbl_mensaje, "")
        else:
            mostrar_error(self.lbl_mensaje, "No hay celdas libres disponibles para este tipo.")

    def _aplicar(self) -> None:
        celda_origen: Optional[CeldaConEstado] = self.cmb_vehiculo.currentData()
        celda_destino = self.cmb_destino.currentData()

        if celda_origen is None:
            mostrar_error(self.lbl_mensaje, "Selecciona un vehículo.")
            return
        if celda_destino is None:
            mostrar_error(self.lbl_mensaje, "No hay celdas destino disponibles.")
            return

        motivo = self.txt_motivo.toPlainText().strip()
        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.corregir_celda(
                id_movimiento=celda_origen.id_movimiento,
                id_celda_destino=celda_destino.id_celda,
                motivo=motivo,
                sesion=self._sesion,
            ),
        )
        if ok:
            mostrar_ok(
                self.lbl_mensaje,
                f"Corrección aplicada: {celda_origen.placa} ahora está en la celda {celda_destino.codigo}.",
            )
            self.btn_aplicar.setEnabled(False)


# ─────────────────────────── Pantalla Estado de celdas ───────────────────────

class EstadoCeldasView(QDialog):
    """Vista principal del estado de las 80 celdas con filtros y corrección."""

    def __init__(self, sesion: Sesion, servicio: CeldaService, parent=None):
        super().__init__(parent)
        self._sesion = sesion
        self._servicio = servicio
        self._celdas: List[CeldaConEstado] = []
        self._tarjetas: List[_TarjetaCelda] = []
        self._seleccionada: Optional[CeldaConEstado] = None

        self.setWindowTitle("Autos Colombia - Estado de celdas")
        self.resize(820, 580)
        self.setMinimumSize(760, 500)

        # ── Filtros ─────────────────────────────────────────────────
        lbl_tipo = QLabel("Tipo")
        lbl_tipo.setObjectName("campo_label")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Todas", None)
        self.cmb_tipo.addItem("Motos", TipoVehiculo.MOTO)
        self.cmb_tipo.addItem("Vehículos", TipoVehiculo.VEHICULO)
        self.cmb_tipo.setFixedWidth(170)

        lbl_estado_f = QLabel("Estado")
        lbl_estado_f.setObjectName("campo_label")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItem("Todas", None)
        self.cmb_estado.addItem("Libres", True)
        self.cmb_estado.addItem("Ocupadas", False)
        self.cmb_estado.setFixedWidth(170)

        self.btn_corregir = QPushButton("Corregir celda")
        self.btn_corregir.setObjectName("accion_panel")
        self.btn_corregir.setEnabled(False)
        self.btn_corregir.setFixedWidth(160)
        self.btn_corregir.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        col_tipo = QVBoxLayout()
        col_tipo.setSpacing(2)
        col_tipo.addWidget(lbl_tipo)
        col_tipo.addWidget(self.cmb_tipo)

        col_estado = QVBoxLayout()
        col_estado.setSpacing(2)
        col_estado.addWidget(lbl_estado_f)
        col_estado.addWidget(self.cmb_estado)

        fila_filtros = QHBoxLayout()
        fila_filtros.setSpacing(16)
        fila_filtros.addLayout(col_tipo)
        fila_filtros.addLayout(col_estado)
        fila_filtros.addStretch()
        fila_filtros.addWidget(self.btn_corregir, alignment=Qt.AlignBottom)

        # ── Leyenda ──────────────────────────────────────────────────
        def _indicador(color: str, borde: str, texto: str) -> QHBoxLayout:
            caja = QFrame()
            caja.setFixedSize(16, 16)
            caja.setStyleSheet(
                f"background:{color}; border:1px solid {borde};"
                "border-radius:3px;"
            )
            lbl = QLabel(texto)
            fila = QHBoxLayout()
            fila.setSpacing(6)
            fila.addWidget(caja)
            fila.addWidget(lbl)
            return fila

        fila_leyenda = QHBoxLayout()
        fila_leyenda.setSpacing(24)
        fila_leyenda.addLayout(_indicador("#1a3a1a", "#166534", "Libre"))
        fila_leyenda.addLayout(_indicador("#3a1a1a", "#991b1b", "Ocupada"))
        fila_leyenda.addStretch()

        self.lbl_resumen = QLabel("Celdas totales = 0 | Celdas disponibles = 0 | Celdas ocupadas = 0")
        self.lbl_resumen.setStyleSheet("font-size: 14px; font-weight: 600; color: #d4d4d8;")

        # ── Área scrollable con la cuadrícula ────────────────────────
        self._contenedor_grid = QWidget()
        self._grid_layout = QVBoxLayout(self._contenedor_grid)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._contenedor_grid)
        scroll.setStyleSheet(
            "QScrollArea{ border: none; background: transparent; }"
            "QWidget{ background: transparent; }"
        )

        # ── Mensajes ─────────────────────────────────────────────────
        self.lbl_hint = QLabel(
            "Seleccionar una celda ocupada y pulsar Corregir celda permite moverla a otra libre."
        )
        self.lbl_hint.setObjectName("campo_label")
        self.lbl_hint.setWordWrap(True)

        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(18)

        # ── Layout principal ─────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        layout.addLayout(fila_filtros)
        layout.addLayout(fila_leyenda)
        layout.addWidget(self.lbl_resumen)
        layout.addWidget(scroll, 1)
        layout.addWidget(self.lbl_hint)
        layout.addWidget(self.lbl_mensaje)

        # ── Eventos ──────────────────────────────────────────────────
        self.cmb_tipo.currentIndexChanged.connect(self._refrescar)
        self.cmb_estado.currentIndexChanged.connect(self._refrescar)
        self.btn_corregir.clicked.connect(self._abrir_correccion)

        self._refrescar()

    # ── Lógica interna ────────────────────────────────────────────────

    def _refrescar(self) -> None:
        """Recarga las celdas desde el servicio y dibuja la cuadrícula."""
        tipo = self.cmb_tipo.currentData()
        solo_libres = self.cmb_estado.currentData()

        ok, celdas = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.listar_celdas(tipo, solo_libres),
        )
        if not ok:
            return

        self._celdas = celdas or []
        disponibles = sum(1 for celda in self._celdas if celda.libre)
        ocupadas = len(self._celdas) - disponibles
        self.lbl_resumen.setText(
            f"Celdas totales = {len(self._celdas)} "
            f"| Celdas disponibles = {disponibles} "
            f"| Celdas ocupadas = {ocupadas}"
        )
        self._seleccionada = None
        self.btn_corregir.setEnabled(False)
        self._dibujar_cuadricula()

    def _dibujar_cuadricula(self) -> None:
        """Elimina los widgets anteriores y reconstruye la cuadrícula."""
        # Limpiar
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tarjetas.clear()

        # Separar por tipo
        motos = [c for c in self._celdas if c.tipo == TipoVehiculo.MOTO]
        vehiculos = [c for c in self._celdas if c.tipo == TipoVehiculo.VEHICULO]

        COLUMNAS = 10

        def _seccion(titulo_txt: str, celdas: List[CeldaConEstado]) -> None:
            if not celdas:
                return
            lbl = QLabel(titulo_txt)
            lbl.setStyleSheet("font-size:15px; font-weight:700; color:#ffffff;")
            self._grid_layout.addWidget(lbl)

            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(6)
            grid.setContentsMargins(0, 0, 0, 0)

            for idx, celda in enumerate(celdas):
                tarjeta = _TarjetaCelda(celda)
                tarjeta.clicked.connect(self._al_clic_tarjeta)
                self._tarjetas.append(tarjeta)
                grid.addWidget(tarjeta, idx // COLUMNAS, idx % COLUMNAS)

            self._grid_layout.addWidget(grid_widget)

        _seccion("Motos", motos)
        _seccion("Vehículos", vehiculos)

        # Nota si se ven celdas de vehículos recortadas
        total_v = len([c for c in self._celdas if c.tipo == TipoVehiculo.VEHICULO])
        if total_v > 30 and self.cmb_estado.currentData() is None and self.cmb_tipo.currentData() != TipoVehiculo.MOTO:
            lbl_nota = QLabel("V31 a V70 se muestran al desplazarse")
            lbl_nota.setObjectName("campo_label")
            self._grid_layout.addWidget(lbl_nota)

        self._grid_layout.addStretch()

    def _al_clic_tarjeta(self) -> None:
        """Deselecciona la anterior y marca la nueva, habilitando el botón si está ocupada."""
        tarjeta: _TarjetaCelda = self.sender()

        # Deseleccionar todas las demás
        for t in self._tarjetas:
            if t is not tarjeta:
                t.setChecked(False)

        if tarjeta.isChecked():
            self._seleccionada = tarjeta.celda
            # Solo habilitar corrección si la celda está ocupada
            self.btn_corregir.setEnabled(not tarjeta.celda.libre)
            if tarjeta.celda.libre:
                mostrar_info(self.lbl_mensaje, "Solo puedes corregir celdas ocupadas.")
            else:
                mostrar_info(self.lbl_mensaje, "")
        else:
            self._seleccionada = None
            self.btn_corregir.setEnabled(False)
            mostrar_info(self.lbl_mensaje, "")

    def _abrir_correccion(self) -> None:
        """Abre el modal de corrección con las celdas ocupadas disponibles."""
        # Obtener todas las celdas ocupadas (sin filtro)
        ok, todas = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.listar_celdas(tipo=None, solo_libres=False),
        )
        if not ok:
            return
        if not todas:
            mostrar_info(self.lbl_mensaje, "No hay celdas ocupadas en este momento.")
            return

        dlg = CorregirCeldaView(todas, self._seleccionada, self._sesion, self._servicio, self)
        dlg.exec()
        # Siempre refrescar al cerrar por si cambió algo
        self._refrescar()
