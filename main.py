"""Punto de entrada de la aplicación de escritorio de Autos Colombia.

Flujo: crea Qt y los servicios; luego dirige a cada usuario al panel de su rol.
"""
import logging
import sys

from PySide6.QtWidgets import QApplication

from services.contenedor import crear_servicios
from ui.admin_panel_view import AdminPanelView
from ui.cliente_portal_view import ClientePortalView
from ui.comun import HOJA_ESTILOS
from ui.login_view import LoginView
from ui.panel_view import PanelView


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    app = QApplication(sys.argv)
    app.setStyleSheet(HOJA_ESTILOS)
    servicios = crear_servicios()

    while True:
        login = LoginView(servicios.auth, servicios.cliente)
        # exec() abre la ventana y espera: devuelve 1 si se aceptó y 0 si se cerró con la X
        if not login.exec():
            break

        if login.rol_autenticado == "cliente":
            portal = ClientePortalView(
                login.cliente, servicios.cliente, servicios.solicitudes_cliente
            )
            if not portal.exec():  # 0 = cerró con la X; 1 = "Cerrar sesión" -> otro login
                break
        elif login.rol_autenticado == "administrador":
            panel = AdminPanelView(login.administrador, servicios)
            if not panel.exec():
                break
        else:
            panel = PanelView(login.sesion, servicios)
            if not panel.exec():  # 0 = cerró con la X -> salir; 1 = "Cerrar sesión" -> otro login
                break
    return 0


if __name__ == "__main__":
    sys.exit(main())
