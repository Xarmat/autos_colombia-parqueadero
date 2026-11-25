"""Portal del cliente (HU-U8 a HU-U11).

Permite al cliente autenticado consultar sus datos personales,
la lista de sus vehículos y el valor de su mensualidad.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QMessageBox,
)

from models.entidades import Propietario
from models.enums import TipoSolicitudCliente, TipoVehiculo
from services.cliente_service import ClienteService
from services.solicitud_cliente_service import SolicitudClienteService
from ui.comun import ejecutar


def _formato_moneda(valor: int) -> str:
    """Formatea un entero a formato de pesos colombianos: $ 120.000."""
    return f"$ {valor:,.0f}".replace(",", ".")


class ClientePortalView(QDialog):
    """Pantalla del portal exclusivo para clientes."""

    def __init__(
        self,
        cliente: Propietario,
        servicio: ClienteService,
        solicitudes: SolicitudClienteService,
        parent=None,
    ):
        super().__init__(parent)
        self._cliente = cliente
        self._servicio = servicio
        self._solicitudes = solicitudes

        self.setWindowTitle("Autos Colombia - Portal del cliente")
        self.setFixedWidth(740)

        # ── Encabezado ──────────────────────────────────────────────
        titulo = QLabel("Portal del cliente")
        titulo.setObjectName("titulo")

        subtitulo = QLabel(f"{cliente.nombre} · Documento {cliente.documento}")
        subtitulo.setObjectName("subtitulo")

        btn_cerrar_sesion = QPushButton("Cerrar sesión")
        btn_cerrar_sesion.setObjectName("secundario")
        btn_cerrar_sesion.setFixedWidth(130)
        btn_cerrar_sesion.clicked.connect(self.accept)

        col_titulos = QVBoxLayout()
        col_titulos.setSpacing(2)
        col_titulos.addWidget(titulo)
        col_titulos.addWidget(subtitulo)

        fila_header = QHBoxLayout()
        fila_header.addLayout(col_titulos, 1)
        fila_header.addWidget(btn_cerrar_sesion, alignment=Qt.AlignTop)

        # ── Tarjeta: Mis datos ───────────────────────────────────────
        card_datos = QFrame()
        card_datos.setObjectName("tarjeta_panel")
        layout_card_datos = QVBoxLayout(card_datos)
        layout_card_datos.setContentsMargins(16, 14, 16, 14)
        layout_card_datos.setSpacing(10)

        lbl_tit_datos = QLabel("Mis datos")
        lbl_tit_datos.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")

        fila_campos = QHBoxLayout()
        fila_campos.setSpacing(20)

        def _col_dato(etiqueta: str, valor: str) -> QVBoxLayout:
            col = QVBoxLayout()
            col.setSpacing(4)
            lbl_e = QLabel(etiqueta)
            lbl_e.setObjectName("campo_label")
            lbl_v = QLabel(valor)
            lbl_v.setStyleSheet("font-size: 15px; font-weight: 500; color: #ffffff;")
            col.addWidget(lbl_e)
            col.addWidget(lbl_v)
            return col

        fila_campos.addLayout(_col_dato("Nombre", cliente.nombre), 1)
        fila_campos.addLayout(_col_dato("Documento", cliente.documento), 1)
        fila_campos.addLayout(_col_dato("Teléfono", cliente.telefono or "No registrado"), 1)

        layout_card_datos.addWidget(lbl_tit_datos)
        layout_card_datos.addLayout(fila_campos)

        # ── Sección: Mis vehículos ──────────────────────────────────
        lbl_tit_vehiculos = QLabel("Mis vehículos")
        lbl_tit_vehiculos.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")

        self.tbl_vehiculos = QTableWidget()
        self.tbl_vehiculos.setColumnCount(6)
        self.tbl_vehiculos.setHorizontalHeaderLabels(
            ["Placa", "Tipo", "Marca", "Color", "Estado", "Pago"]
        )
        self.tbl_vehiculos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_vehiculos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_vehiculos.setSelectionMode(QAbstractItemView.NoSelection)
        self.tbl_vehiculos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_vehiculos.verticalHeader().setVisible(False)
        self.tbl_vehiculos.setShowGrid(False)
        self.tbl_vehiculos.setFixedHeight(120)
        self.lbl_alerta_pago = QLabel("")
        self.lbl_alerta_pago.setWordWrap(True)
        self.lbl_alerta_pago.hide()

        # ── Tarjeta: Valor a pagar este mes ──────────────────────────
        lbl_tit_pago = QLabel("Valor a pagar este mes")
        lbl_tit_pago.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")

        self.card_pago = QFrame()
        self.card_pago.setObjectName("tarjeta_panel")
        self.layout_card_pago = QVBoxLayout(self.card_pago)
        self.layout_card_pago.setContentsMargins(18, 16, 18, 16)
        self.layout_card_pago.setSpacing(10)

        # Contenedor dinámico para items
        self.layout_items_pago = QVBoxLayout()
        self.layout_items_pago.setSpacing(8)

        # Separador tenue
        separador = QFrame()
        separador.setFrameShape(QFrame.HLine)
        separador.setStyleSheet("background: #27272a; max-height: 1px;")

        # Fila Total
        self.lbl_total_valor = QLabel(_formato_moneda(0))
        self.lbl_total_valor.setStyleSheet("font-size: 18px; font-weight: 700; color: #4ade80;")

        lbl_total_txt = QLabel("Total mensual")
        lbl_total_txt.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")

        fila_total = QHBoxLayout()
        fila_total.addWidget(lbl_total_txt)
        fila_total.addStretch()
        fila_total.addWidget(self.lbl_total_valor)

        lbl_nota_pie = QLabel(
            "Consulta de solo lectura. El pago se registra con el operario; no hay cobro automático."
        )
        lbl_nota_pie.setStyleSheet("font-size: 13px; color: #9ca3af;")

        self.layout_card_pago.addLayout(self.layout_items_pago)
        self.layout_card_pago.addSpacing(4)
        self.layout_card_pago.addWidget(separador)
        self.layout_card_pago.addSpacing(2)
        self.layout_card_pago.addLayout(fila_total)
        self.layout_card_pago.addWidget(lbl_nota_pie)

        # Mensaje inferior (errores)
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setMinimumHeight(18)
        self.cmb_vehiculo_renovacion = QComboBox()
        self.cmb_vehiculo_renovacion.setVisible(False)
        self.btn_continuar = QPushButton("Indicar que continuaré")
        self.btn_continuar.setObjectName("secundario")
        self.btn_baja = QPushButton("Solicitar baja al administrador")
        self.btn_baja.setObjectName("secundario")
        self.btn_continuar.setVisible(False)
        self.btn_baja.setVisible(False)
        fila_renovacion = QHBoxLayout()
        fila_renovacion.addWidget(self.cmb_vehiculo_renovacion, 1)
        fila_renovacion.addWidget(self.btn_continuar)
        fila_renovacion.addWidget(self.btn_baja)

        # ── Layout principal ─────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addLayout(fila_header)
        layout.addSpacing(2)
        layout.addWidget(card_datos)
        layout.addSpacing(2)
        layout.addWidget(self.lbl_alerta_pago)
        layout.addWidget(lbl_tit_vehiculos)
        layout.addWidget(self.tbl_vehiculos)
        layout.addSpacing(2)
        layout.addWidget(lbl_tit_pago)
        layout.addWidget(self.card_pago)
        layout.addLayout(fila_renovacion)
        layout.addWidget(self.lbl_mensaje)

        self.btn_continuar.clicked.connect(self._indicar_continuidad)
        self.btn_baja.clicked.connect(self._solicitar_baja)
        self._cargar_datos()

    def _cargar_datos(self) -> None:
        """Consulta los vehículos del cliente y el cobro mensual calculado."""
        ok, resumen = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.obtener_resumen_mensual(self._cliente.id_propietario)
        )
        if not ok or not resumen:
            return

        vehiculos = resumen["vehiculos"]
        self.tbl_vehiculos.setRowCount(len(vehiculos))
        self.cmb_vehiculo_renovacion.clear()
        avisos_pendientes = []
        avisos_renovacion = []
        mostrar_acciones = False
        vehiculos_con_decision = []

        # Rellenar tabla
        for row, v in enumerate(vehiculos):
            tipo_txt = "Vehículo" if v.tipo == TipoVehiculo.VEHICULO else "Moto"
            estado_txt = "Habilitado" if v.habilitado else "Inhabilitado"
            estado_pago = v.estado_pago
            pago_txt = estado_pago.estado if estado_pago else "Sin datos"
            if estado_pago and estado_pago.decision_renovacion:
                pago_txt += f" · {estado_pago.decision_renovacion.lower()}"
            fin = estado_pago.fecha_cubierta_hasta if estado_pago else None
            fin_txt = _fecha_corta(fin) if fin else "Sin mensualidad"

            self.tbl_vehiculos.setItem(row, 0, QTableWidgetItem(v.placa))
            self.tbl_vehiculos.setItem(row, 1, QTableWidgetItem(tipo_txt))
            self.tbl_vehiculos.setItem(row, 2, QTableWidgetItem(v.marca))
            self.tbl_vehiculos.setItem(row, 3, QTableWidgetItem(v.color))
            self.tbl_vehiculos.setItem(row, 4, QTableWidgetItem(estado_txt))
            self.tbl_vehiculos.setItem(row, 5, QTableWidgetItem(f"{pago_txt} · {fin_txt}"))

            if estado_pago and estado_pago.estado in ("Pago pendiente", "Bloqueado"):
                avisos_pendientes.append(v.placa)
                mostrar_acciones = True
                vehiculos_con_decision.append((v.placa, tipo_txt))
            elif estado_pago and estado_pago.renovacion_disponible:
                avisos_renovacion.append(v.placa)
                mostrar_acciones = True
                vehiculos_con_decision.append((v.placa, tipo_txt))

        for placa, tipo_txt in vehiculos_con_decision:
            self.cmb_vehiculo_renovacion.addItem(f"{placa} · {tipo_txt}", placa)

        if avisos_pendientes:
            placas = ", ".join(avisos_pendientes)
            self.lbl_alerta_pago.setText(
                f"Pago pendiente para: {placas}. Desde el día 15 de mora se bloquean nuevos ingresos."
            )
            self.lbl_alerta_pago.setStyleSheet(
                "background:#7f1d1d;color:#ffffff;padding:10px;border-radius:6px;"
            )
            self.lbl_alerta_pago.show()
        elif avisos_renovacion:
            self.lbl_alerta_pago.setText(
                f"Tu mensualidad vence en siete días o menos: {', '.join(avisos_renovacion)}. "
                "Puedes indicar si continuarás; no se cobrará automáticamente."
            )
            self.lbl_alerta_pago.setStyleSheet(
                "background:#854d0e;color:#ffffff;padding:10px;border-radius:6px;"
            )
            self.lbl_alerta_pago.show()
        else:
            self.lbl_alerta_pago.hide()

        self.cmb_vehiculo_renovacion.setVisible(mostrar_acciones)
        self.btn_continuar.setVisible(mostrar_acciones)
        self.btn_baja.setVisible(mostrar_acciones)

        # Rellenar items de pago
        # Limpiar anteriores si hubiera
        while self.layout_items_pago.count():
            item = self.layout_items_pago.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Limpiar widgets internos del layout
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        items = resumen["items"]
        if not items:
            lbl_vacio = QLabel("No tienes vehículos registrados.")
            lbl_vacio.setStyleSheet("font-size: 14px; color: #9ca3af;")
            self.layout_items_pago.addWidget(lbl_vacio)
        else:
            for item in items:
                fila_item = QHBoxLayout()
                etiqueta = f"{item['placa']} ({item['tipo_str']})"
                lbl_nombre = QLabel(etiqueta)
                lbl_nombre.setStyleSheet("font-size: 14px; color: #e4e4e7;")

                lbl_tarifa = QLabel(_formato_moneda(item["tarifa"]))
                lbl_tarifa.setStyleSheet("font-size: 14px; color: #e4e4e7;")

                fila_item.addWidget(lbl_nombre)
                fila_item.addStretch()
                fila_item.addWidget(lbl_tarifa)
                self.layout_items_pago.addLayout(fila_item)

        total = resumen["total"]
        self.lbl_total_valor.setText(_formato_moneda(total))

    def _registrar_decision(self, tipo: TipoSolicitudCliente) -> None:
        placa = self.cmb_vehiculo_renovacion.currentData()
        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._solicitudes.registrar_decision(
                self._cliente.id_propietario, tipo, placa
            ),
        )
        if ok:
            self.lbl_mensaje.setText(
                "Tu decisión fue enviada al administrador. El pago sigue siendo presencial con el operario."
            )
            self._cargar_datos()

    def _indicar_continuidad(self) -> None:
        self._registrar_decision(TipoSolicitudCliente.CONTINUAR)

    def _solicitar_baja(self) -> None:
        respuesta = QMessageBox.question(
            self,
            "Solicitar baja",
            "La solicitud corresponde a tu cuenta y a todos tus vehículos. ¿Deseas enviarla al administrador?",
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self._registrar_decision(TipoSolicitudCliente.BAJA)


def _fecha_corta(fecha) -> str:
    return fecha.strftime("%d/%m/%Y")
