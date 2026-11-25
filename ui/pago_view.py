"""Registro de pagos para el operario y comprobante imprimible."""
from datetime import date
from html import escape

from PySide6.QtCore import QDate
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QDateEdit, QTextBrowser,
)
from PySide6.QtGui import QTextDocument

from models.entidades import ComprobantePago, Sesion
from models.enums import ConceptoPago, MedioPago
from services.pago_service import PagoService
from ui.comun import ejecutar, limitar_campo, mostrar_info, mostrar_ok


def _moneda(valor: int) -> str:
    return f"$ {valor:,.0f}".replace(",", ".")


def _fecha(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


class ComprobantePagoView(QDialog):
    def __init__(self, comprobante: ComprobantePago, parent=None):
        super().__init__(parent)
        self._comprobante = comprobante
        self.setWindowTitle("Comprobante de pago")
        self.setMinimumWidth(420)

        titulo = QLabel("Autos Colombia - Comprobante de pago")
        titulo.setObjectName("titulo")
        self.documento = QTextBrowser()
        self.documento.setOpenExternalLinks(False)
        self.documento.setHtml(self._crear_html())

        btn_imprimir = QPushButton("Imprimir")
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("secundario")
        botones = QHBoxLayout()
        botones.addWidget(btn_imprimir)
        botones.addWidget(btn_cerrar)

        layout = QVBoxLayout(self)
        layout.addWidget(titulo)
        layout.addWidget(self.documento)
        layout.addLayout(botones)
        btn_imprimir.clicked.connect(self._imprimir)
        btn_cerrar.clicked.connect(self.accept)

    def _crear_html(self) -> str:
        pago = self._comprobante
        lineas = [
            f"<b>Comprobante:</b> P-{pago.id_pago:06d}",
            f"<b>Cliente:</b> {escape(pago.nombre_cliente)}",
            f"<b>Vehículo:</b> {escape(pago.placa)} - {escape(pago.tipo_vehiculo.etiqueta)}",
            f"<b>Fecha del pago:</b> {_fecha(pago.fecha_pago.date())}",
            f"<b>Medio de pago:</b> {escape(pago.medio_pago.name.replace('_', ' ').title())}",
            f"<b>Usuario:</b> {escape(pago.usuario_operario)}",
            f"<b>Valor pagado:</b> {_moneda(pago.valor_total)}",
            "<br><b>Vigencia y detalle</b>",
        ]
        for detalle in pago.detalles:
            concepto = (
                "Prorrateo de gracia"
                if detalle.concepto is ConceptoPago.PRORRATEO
                else "Mensualidad"
            )
            lineas.append(
                f"{concepto}: {_fecha(detalle.fecha_inicio)} - "
                f"{_fecha(detalle.fecha_fin)} · {_moneda(detalle.valor)}"
            )
        return "<div style='font-size:14px;line-height:1.6'>" + "<br>".join(lineas) + "</div>"

    def _imprimir(self) -> None:
        impresora = QPrinter()
        dialogo = QPrintDialog(impresora, self)
        if dialogo.exec():
            documento = QTextDocument()
            documento.setHtml(self._crear_html())
            documento.print_(impresora)


class PagoView(QDialog):
    """Permite consultar y registrar la mensualidad de un vehículo."""

    def __init__(self, sesion: Sesion, servicio: PagoService, parent=None):
        super().__init__(parent)
        self._sesion = sesion
        self._servicio = servicio
        self._placa_consultada = ""
        self._inicial = False
        self._requiere_continuidad = False

        self.setWindowTitle("Registrar pago por vehículo")
        self.setMinimumWidth(500)

        titulo = QLabel("Registrar pago por vehículo")
        titulo.setObjectName("titulo")
        self.txt_placa = QLineEdit()
        self.txt_placa.setPlaceholderText("Placa, por ejemplo ABC123")
        limitar_campo(self.txt_placa, 6, tipo="placa")
        self.btn_consultar = QPushButton("Consultar")

        self.lbl_estado = QLabel("Consulta la placa para ver el estado y el valor.")
        self.lbl_estado.setWordWrap(True)
        self.lbl_periodo = QLabel("")
        self.lbl_periodo.setWordWrap(True)
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: 700; color: #4ade80;")

        self.fecha_inicio = QDateEdit(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setMinimumDate(QDate.currentDate())
        self.fecha_inicio.setDisplayFormat("dd/MM/yyyy")
        self.lbl_fecha_inicio = QLabel("Inicio de mensualidad inicial")
        self.lbl_fecha_inicio.hide()
        self.fecha_inicio.hide()
        self.chk_continuidad = QCheckBox(
            "El cliente continuará: incluir la mensualidad completa después del prorrateo."
        )
        self.chk_continuidad.hide()
        self.lbl_no_continuidad = QLabel(
            "Si el cliente no continuará, no registres el pago. Puede solicitar la baja desde su portal."
        )
        self.lbl_no_continuidad.setWordWrap(True)
        self.lbl_no_continuidad.hide()
        self.cmb_medio = QComboBox()
        self.cmb_medio.addItem("Efectivo", MedioPago.EFECTIVO)
        self.cmb_medio.addItem("Código QR", MedioPago.QR)
        self.cmb_medio.addItem("Recibo bancario presentado", MedioPago.RECIBO_BANCARIO)

        formulario = QFormLayout()
        formulario.addRow("Placa", self.txt_placa)
        formulario.addRow(self.lbl_fecha_inicio, self.fecha_inicio)
        formulario.addRow("Medio de pago", self.cmb_medio)

        self.btn_registrar = QPushButton("Registrar pago")
        self.btn_registrar.setEnabled(False)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("secundario")
        botones = QHBoxLayout()
        botones.addWidget(self.btn_registrar)
        botones.addWidget(btn_cerrar)

        layout = QVBoxLayout(self)
        layout.addWidget(titulo)
        fila_placa = QHBoxLayout()
        fila_placa.addWidget(self.txt_placa)
        fila_placa.addWidget(self.btn_consultar)
        layout.addLayout(fila_placa)
        layout.addWidget(self.lbl_estado)
        layout.addWidget(self.lbl_periodo)
        layout.addWidget(self.lbl_total)
        layout.addLayout(formulario)
        layout.addWidget(self.chk_continuidad)
        layout.addWidget(self.lbl_no_continuidad)
        layout.addLayout(botones)

        self.txt_placa.textEdited.connect(self._placa_editada)
        self.btn_consultar.clicked.connect(self._consultar)
        self.txt_placa.returnPressed.connect(self._consultar)
        self.fecha_inicio.dateChanged.connect(self._previsualizar)
        self.chk_continuidad.toggled.connect(self._previsualizar)
        self.btn_registrar.clicked.connect(self._registrar)
        btn_cerrar.clicked.connect(self.accept)

    def _placa_editada(self, texto: str) -> None:
        if texto != texto.upper():
            self.txt_placa.setText(texto.upper())
        self._placa_consultada = ""
        self.btn_registrar.setEnabled(False)
        mostrar_info(self.lbl_estado, "Consulta la placa para ver el estado y el valor.")
        self.lbl_periodo.clear()
        self.lbl_total.clear()

    def _consultar(self) -> None:
        self._placa_consultada = self.txt_placa.text().strip().upper()
        self.btn_registrar.setEnabled(False)
        ok, estado = ejecutar(
            self.lbl_estado,
            lambda: self._servicio.consultar_estado(self._placa_consultada),
        )
        if not ok:
            return
        self._inicial = estado.fecha_inicio is None
        self._requiere_continuidad = estado.estado == "Bloqueado"
        self.chk_continuidad.setChecked(False)
        self.chk_continuidad.setVisible(self._requiere_continuidad)
        self.lbl_no_continuidad.setVisible(self._requiere_continuidad)
        self.fecha_inicio.setVisible(self._inicial)
        self._actualizar_label_formulario()
        self._previsualizar()

    def _actualizar_label_formulario(self) -> None:
        self.lbl_fecha_inicio.setVisible(self._inicial)

    def _previsualizar(self, *_args) -> None:
        if not self._placa_consultada:
            return
        fecha_inicio = (
            date.fromisoformat(self.fecha_inicio.date().toString("yyyy-MM-dd"))
            if self._inicial else None
        )
        ok, vista = ejecutar(
            self.lbl_estado,
            lambda: self._servicio.previsualizar_pago(
                self._placa_consultada, fecha_inicio
            ),
        )
        if not ok:
            self.lbl_periodo.clear()
            self.lbl_total.clear()
            self.btn_registrar.setEnabled(False)
            return

        estado = vista["estado"]
        mostrar_info(
            self.lbl_estado,
            f"Estado: {estado.estado} · Tarifa mensual: {_moneda(estado.tarifa_mensual)}",
        )
        detalle_txt = []
        for detalle in vista["detalles"]:
            concepto = "Prorrateo de gracia" if detalle["concepto"] is ConceptoPago.PRORRATEO else "Mensualidad"
            detalle_txt.append(
                f"{concepto}: {_fecha(detalle['fecha_inicio'])} - "
                f"{_fecha(detalle['fecha_fin'])} · {_moneda(detalle['valor'])}"
            )
        self.lbl_periodo.setText("\n".join(detalle_txt))
        if self._requiere_continuidad:
            self.lbl_periodo.setText(
                "La mensualidad completa se agrega solo si el cliente continúa.\n"
                + self.lbl_periodo.text()
            )
        self.lbl_total.setText(f"Total a registrar: {_moneda(vista['total'])}")
        self.btn_registrar.setEnabled(
            not self._requiere_continuidad or self.chk_continuidad.isChecked()
        )

    def _registrar(self) -> None:
        fecha_inicio = (
            date.fromisoformat(self.fecha_inicio.date().toString("yyyy-MM-dd"))
            if self._inicial else None
        )
        ok, comprobante = ejecutar(
            self.lbl_estado,
            lambda: self._servicio.registrar_pago(
                self._placa_consultada,
                self.cmb_medio.currentData(),
                self._sesion,
                fecha_inicio,
                self.chk_continuidad.isChecked() if self._requiere_continuidad else None,
            ),
        )
        if not ok:
            return
        self.btn_registrar.setEnabled(False)
        mostrar_ok(self.lbl_estado, "Pago registrado correctamente.")
        ComprobantePagoView(comprobante, self).exec()
