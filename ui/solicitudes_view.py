"""Revisión y resolución administrativa de reportes enviados por los operarios."""
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from models.entidades import Administrador, SolicitudCambio
from services.solicitud_service import SolicitudService
from ui.comun import ejecutar, limitar_campo, limitar_texto, mostrar_ok


class SolicitudesView(QDialog):
    def __init__(self, administrador: Administrador, servicio: SolicitudService,
                 abrir_celdas, parent=None):
        super().__init__(parent)
        self._administrador = administrador
        self._servicio = servicio
        self._abrir_celdas = abrir_celdas
        self._solicitudes: list[SolicitudCambio] = []
        self.setWindowTitle("Autos Colombia - Solicitudes de operarios")
        self.resize(900, 600)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["N.º", "Operario", "Tipo", "Placa reportada", "Estado", "Fecha"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.txt_detalle = QPlainTextEdit()
        self.txt_detalle.setReadOnly(True)
        self.txt_detalle.setFixedHeight(90)
        self.txt_placa_correcta = QLineEdit()
        self.txt_placa_correcta.setPlaceholderText("Solo para errores de placa en entrada o salida")
        self.txt_placa_correcta.setEnabled(False)
        limitar_campo(self.txt_placa_correcta, 6, tipo="placa")
        self.txt_respuesta = QPlainTextEdit()
        self.txt_respuesta.setPlaceholderText("Describe la corrección aplicada o el motivo del rechazo.")
        self.txt_respuesta.setFixedHeight(90)
        limitar_texto(self.txt_respuesta, 1000)
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)

        self.btn_resolver = QPushButton("Resolver solicitud")
        self.btn_rechazar = QPushButton("Rechazar")
        self.btn_celdas = QPushButton("Abrir administración de celdas")
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_resolver.setEnabled(False)
        self.btn_rechazar.setEnabled(False)
        self.btn_celdas.setEnabled(False)
        self.btn_resolver.setObjectName("btn_entrar")
        self.btn_celdas.setObjectName("secundario")
        self.btn_rechazar.setObjectName("secundario")
        fila = QHBoxLayout()
        for boton in (self.btn_resolver, self.btn_rechazar, self.btn_celdas, self.btn_cerrar):
            fila.addWidget(boton)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reportes recibidos"))
        layout.addWidget(self.tabla, 1)
        layout.addWidget(QLabel("Situación reportada"))
        layout.addWidget(self.txt_detalle)
        layout.addWidget(QLabel("Placa correcta (si aplica)"))
        layout.addWidget(self.txt_placa_correcta)
        layout.addWidget(QLabel("Respuesta / solución"))
        layout.addWidget(self.txt_respuesta)
        layout.addWidget(self.lbl_mensaje)
        layout.addLayout(fila)

        self.tabla.itemSelectionChanged.connect(self._mostrar_detalle)
        self.btn_resolver.clicked.connect(lambda: self._cerrar_solicitud(False))
        self.btn_rechazar.clicked.connect(lambda: self._cerrar_solicitud(True))
        self.btn_celdas.clicked.connect(self._administrar_celdas)
        self.btn_cerrar.clicked.connect(self.accept)
        self._refrescar()

    def _seleccionada(self):
        fila = self.tabla.currentRow()
        return self._solicitudes[fila] if 0 <= fila < len(self._solicitudes) else None

    def _refrescar(self) -> None:
        ok, solicitudes = ejecutar(self.lbl_mensaje, self._servicio.listar)
        if not ok:
            return
        self._solicitudes = solicitudes or []
        self.tabla.setRowCount(len(self._solicitudes))
        for fila, solicitud in enumerate(self._solicitudes):
            valores = (
                str(solicitud.id_solicitud),
                f"{solicitud.nombre_operario} ({solicitud.usuario_operario})",
                solicitud.tipo,
                solicitud.placa_reportada or "—",
                solicitud.estado,
                solicitud.fecha_solicitud.strftime("%d/%m/%Y %H:%M"),
            )
            for columna, valor in enumerate(valores):
                self.tabla.setItem(fila, columna, QTableWidgetItem(valor))
        self._mostrar_detalle()

    def _mostrar_detalle(self) -> None:
        solicitud = self._seleccionada()
        if solicitud is None:
            self.txt_detalle.clear()
            self.txt_placa_correcta.clear()
            self.txt_respuesta.clear()
            self.txt_placa_correcta.setEnabled(False)
            self.btn_resolver.setEnabled(False)
            self.btn_rechazar.setEnabled(False)
            self.btn_celdas.setEnabled(False)
            return
        self.txt_detalle.setPlainText(solicitud.descripcion)
        self.txt_placa_correcta.clear()
        self.txt_respuesta.setPlainText(solicitud.respuesta or "")
        pendiente = solicitud.estado == "PENDIENTE"
        self.txt_placa_correcta.setEnabled(
            pendiente and solicitud.tipo in {"ENTRADA", "SALIDA"}
        )
        self.btn_resolver.setEnabled(pendiente)
        self.btn_rechazar.setEnabled(pendiente)
        self.btn_celdas.setEnabled(pendiente and solicitud.tipo == "CELDA")

    def _cerrar_solicitud(self, rechazar: bool) -> None:
        solicitud = self._seleccionada()
        if solicitud is None:
            return
        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.resolver(
                solicitud.id_solicitud,
                self._administrador.id_administrador,
                self.txt_respuesta.toPlainText(),
                self.txt_placa_correcta.text(),
                rechazar,
            ),
        )
        if ok:
            mostrar_ok(self.lbl_mensaje, "Solicitud actualizada.")
            self._refrescar()

    def _administrar_celdas(self) -> None:
        self._abrir_celdas()
        self._refrescar()
