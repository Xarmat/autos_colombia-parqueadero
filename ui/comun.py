"""Piezas compartidas por todas las ventanas: estilos y manejo uniforme de errores."""
import logging
from pathlib import Path
from typing import Callable, Optional, Tuple, TypeVar

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator, QValidator
from PySide6.QtWidgets import QLabel, QLineEdit, QPlainTextEdit

from excepciones.errores import ParqueaderoError

T = TypeVar("T")

_RUTA_FLECHA = (Path(__file__).resolve().parent / "flecha_abajo.svg").as_posix()

# Hoja de estilos global (se aplica una sola vez en main.py).
HOJA_ESTILOS = f"""
QDialog {{ background: #000000; }}
QLabel {{ font-size: 14px; color: #f2f2f2; }}
QLabel#titulo {{ font-size: 22px; font-weight: 700; color: #ffffff; margin-bottom: 2px; }}
QLabel#subtitulo {{ font-size: 14px; color: #9ca3af; }}
QLabel#campo_label {{ font-size: 13px; color: #9ca3af; font-weight: 500; }}
QLabel#celda {{ font-size: 28px; font-weight: 700; color: #4ade80; }}

QLineEdit, QComboBox, QPlainTextEdit {{
    font-size: 14px;
    padding: 8px 12px;
    background: #1c1c1e;
    color: #ffffff;
    border: 1px solid #333336;
    border-radius: 8px;
    selection-background-color: #2563eb;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid #2563eb;
}}
QLineEdit:disabled, QComboBox:disabled {{
    background: #141416;
    color: #666666;
    border: 1px solid #27272a;
}}

QComboBox {{
    padding-right: 28px;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
}}
QComboBox::down-arrow {{
    image: url("{_RUTA_FLECHA}");
    width: 10px;
    height: 6px;
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background: #1c1c1e;
    color: #ffffff;
    border: 1px solid #333336;
    border-radius: 6px;
    selection-background-color: #2563eb;
    outline: none;
}}

QPushButton {{
    font-size: 14px;
    font-weight: 500;
    padding: 10px 16px;
    border-radius: 8px;
    background: #2563eb;
    color: #ffffff;
    border: none;
}}
QPushButton:hover {{ background: #3b82f6; }}
QPushButton:pressed {{ background: #1d4ed8; }}
QPushButton:disabled {{ background: #27272a; color: #71717a; }}

QPushButton#btn_entrar {{
    font-size: 15px;
    font-weight: 600;
    padding: 12px;
    border-radius: 8px;
    background: #2563eb;
    color: #ffffff;
    border: none;
}}
QPushButton#btn_entrar:hover {{ background: #3b82f6; }}
QPushButton#btn_entrar:pressed {{ background: #1d4ed8; }}

QPushButton#accion_panel {{
    font-size: 14px;
    font-weight: 500;
    padding: 14px 10px;
    border-radius: 8px;
    background: #2563eb;
    color: #ffffff;
    border: none;
}}
QPushButton#accion_panel:hover {{ background: #3b82f6; }}
QPushButton#accion_panel:pressed {{ background: #1d4ed8; }}

QPushButton#secundario {{
    background: #27272a;
    color: #f4f4f5;
    font-size: 14px;
    font-weight: 500;
    padding: 12px 10px;
    border-radius: 8px;
    border: none;
}}
QPushButton#secundario:hover {{ background: #3f3f46; }}
QPushButton#secundario:pressed {{ background: #1f1f23; }}

QPushButton#segmento_activo {{
    background: #2563eb;
    color: #ffffff;
    font-size: 14px;
    font-weight: 500;
    border-radius: 8px;
    padding: 9px 16px;
    border: none;
}}
QPushButton#segmento_inactivo {{
    background: #27272a;
    color: #9ca3af;
    font-size: 14px;
    font-weight: 500;
    border-radius: 8px;
    padding: 9px 16px;
    border: none;
}}
QPushButton#segmento_inactivo:hover {{
    background: #323236;
    color: #ffffff;
}}

QPushButton#grande {{ font-size: 16px; padding: 14px; }}

QTableWidget {{
    background-color: #0c0c0e;
    color: #ffffff;
    gridline-color: #1f1f23;
    border: 1px solid #27272a;
    border-radius: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid #18181b;
}}
QTableWidget::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}
QHeaderView::section {{
    background-color: #141416;
    color: #9ca3af;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid #27272a;
    font-weight: 600;
    font-size: 13px;
}}
QScrollBar:vertical {{
    background: #141416;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #2a2a2e;
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: #3f3f46;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QFrame#tarjeta_panel {{
    background: #141416;
    border: 1px solid #27272a;
    border-radius: 8px;
}}
"""

_ESTILO_ERROR = "color: #ef4444; font-size: 13px; font-weight: 500;"
_ESTILO_OK = "color: #4ade80; font-size: 13px; font-weight: 500;"
_ESTILO_NEUTRO = "color: #9ca3af; font-size: 13px;"

def mostrar_error(etiqueta: QLabel, texto: str) -> None:
    """Pinta un mensaje de error (rojo) en la etiqueta de mensajes de la ventana."""
    etiqueta.setStyleSheet(_ESTILO_ERROR)
    etiqueta.setText(texto)


def mostrar_ok(etiqueta: QLabel, texto: str) -> None:
    """Pinta un mensaje de éxito (verde)."""
    etiqueta.setStyleSheet(_ESTILO_OK)
    etiqueta.setText(texto)


def limitar_campo(
    campo: QLineEdit,
    max_len: int,
    tipo: Optional[str] = None,
    validator: Optional[QValidator] = None,
) -> None:
    """Aplica longitud máxima y validación por tipo o validador personalizado."""
    campo.setMaxLength(max_len)
    if validator is not None:
        campo.setValidator(validator)
    elif tipo == "digitos":
        campo.setValidator(QRegularExpressionValidator(QRegularExpression(rf"^\d{{0,{max_len}}}$")))
    elif tipo == "alfanumerico":
        campo.setValidator(QRegularExpressionValidator(QRegularExpression(rf"^[a-zA-Z0-9]{{0,{max_len}}}$")))
    elif tipo == "texto":
        # Permite letras con acentos, ñ y espacios
        campo.setValidator(QRegularExpressionValidator(QRegularExpression(rf"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{{0,{max_len}}}$")))
    elif tipo == "placa":
        campo.setValidator(QRegularExpressionValidator(QRegularExpression(rf"^[a-zA-Z0-9]{{0,{max_len}}}$")))


def limitar_texto(editor: QPlainTextEdit, max_len: int) -> None:
    """Impide que un QPlainTextEdit supere la longitud máxima."""
    def _verificar():
        texto = editor.toPlainText()
        if len(texto) > max_len:
            cursor = editor.textCursor()
            pos = cursor.position()
            editor.setPlainText(texto[:max_len])
            cursor.setPosition(min(pos, max_len))
            editor.setTextCursor(cursor)
    editor.textChanged.connect(_verificar)



def mostrar_info(etiqueta: QLabel, texto: str) -> None:
    """Pinta un mensaje informativo (gris)."""
    etiqueta.setStyleSheet(_ESTILO_NEUTRO)
    etiqueta.setText(texto)


def ejecutar(etiqueta: QLabel, funcion: Callable[[], T]) -> Tuple[bool, T]:
    """Ejecuta una acción de negocio y muestra cualquier error en `etiqueta`.

    Devuelve (True, resultado) si funcionó o (False, None) si falló. Así las ventanas
    no repiten try/except: los errores controlados se muestran tal cual y los
    inesperados se registran en el log con un mensaje genérico para el operario.
    """
    try:
        return True, funcion()
    except ParqueaderoError as error:
        mostrar_error(etiqueta, str(error))
    except Exception:  # noqa: BLE001 - último recurso para que la ventana no se cierre
        logging.exception("Error inesperado")
        mostrar_error(etiqueta, "Ocurrió un error inesperado. Avisa al administrador.")
    return False, None
