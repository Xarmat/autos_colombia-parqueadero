"""Revisión administrativa de decisiones de renovación y solicitudes de baja."""
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from models.entidades import Administrador, SolicitudCliente
from models.enums import TipoSolicitudCliente
from services.solicitud_cliente_service import SolicitudClienteService
from ui.comun import ejecutar, mostrar_error, mostrar_ok


class SolicitudesClienteView(QDialog):
    def __init__(
        self,
        administrador: Administrador,
        servicio: SolicitudClienteService,
        parent=None,
    ):
        super().__init__(parent)
        self._administrador = administrador
        self._servicio = servicio
        self._solicitudes: list[SolicitudCliente] = []

        self.setWindowTitle("Solicitudes de clientes")
        self.resize(760, 420)

        titulo = QLabel("Solicitudes de clientes")
        titulo.setObjectName("titulo")
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Documento", "Cliente", "Vehículo", "Decisión", "Fecha"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(False)

        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setWordWrap(True)
        self.btn_atender = QPushButton("Atender solicitud")
        self.btn_rechazar = QPushButton("Rechazar solicitud")
        self.btn_rechazar.setObjectName("secundario")
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("secundario")
        botones = QHBoxLayout()
        botones.addWidget(self.btn_atender)
        botones.addWidget(self.btn_rechazar)
        botones.addStretch()
        botones.addWidget(btn_cerrar)

        layout = QVBoxLayout(self)
        layout.addWidget(titulo)
        layout.addWidget(self.tabla)
        layout.addWidget(self.lbl_mensaje)
        layout.addLayout(botones)

        self.btn_atender.clicked.connect(lambda: self._resolver(True))
        self.btn_rechazar.clicked.connect(lambda: self._resolver(False))
        btn_cerrar.clicked.connect(self.accept)
        self._cargar()

    def _cargar(self) -> None:
        ok, solicitudes = ejecutar(
            self.lbl_mensaje, self._servicio.listar_pendientes
        )
        if not ok:
            return
        self._solicitudes = solicitudes
        self.tabla.setRowCount(len(self._solicitudes))
        for fila, solicitud in enumerate(self._solicitudes):
            decision = (
                f"Solicita continuar · {solicitud.placa}"
                if solicitud.tipo is TipoSolicitudCliente.CONTINUAR
                else "Solicita baja de la cuenta"
            )
            fecha = solicitud.fecha_solicitud.strftime("%d/%m/%Y %H:%M")
            valores = (
                solicitud.documento,
                solicitud.nombre_cliente,
                solicitud.placa or "-",
                decision,
                fecha,
            )
            for columna, valor in enumerate(valores):
                self.tabla.setItem(fila, columna, QTableWidgetItem(valor))
        self.btn_atender.setEnabled(bool(self._solicitudes))
        self.btn_rechazar.setEnabled(bool(self._solicitudes))

    def _resolver(self, aceptar: bool) -> None:
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self._solicitudes):
            mostrar_error(self.lbl_mensaje, "Selecciona una solicitud.")
            return
        solicitud = self._solicitudes[fila]
        ok, _ = ejecutar(
            self.lbl_mensaje,
            lambda: self._servicio.resolver(
                solicitud.id_solicitud,
                self._administrador.id_administrador,
                aceptar,
            ),
        )
        if ok:
            accion = "Solicitud atendida." if aceptar else "Solicitud rechazada."
            mostrar_ok(self.lbl_mensaje, accion)
            self._cargar()
