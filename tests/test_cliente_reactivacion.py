import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from models.entidades import Propietario
from services.cliente_service import ClienteService


class RepositorioClienteFalso:
    def __init__(self):
        self.cliente = Propietario(
            id_propietario=9,
            nombre="Nombre anterior",
            documento="1000000001",
            telefono="3001234567",
            habilitado=False,
            clave_hash="hash-anterior",
            fecha_nuevo_registro=datetime(2024, 1, 1),
        )
        self.reactivado = None

    def buscar_por_documento(self, conn, documento):
        return self.cliente

    def reactivar_cliente(self, conn, id_propietario):
        self.reactivado = id_propietario

    def buscar_por_id(self, conn, id_propietario):
        self.cliente.habilitado = True
        self.cliente.fecha_nuevo_registro = datetime(2026, 4, 20)
        return self.cliente


class ClienteReactivacionTests(unittest.TestCase):
    def test_registro_con_documento_inactivo_reactiva_y_conserva_datos(self):
        repo = RepositorioClienteFalso()
        servicio = ClienteService(repo, pago_service=object())

        @contextmanager
        def transaccion_falsa():
            yield object()

        with patch("services.cliente_service.transaccion", transaccion_falsa):
            cliente = servicio.registrar_cliente(
                "Nombre escrito de nuevo",
                "1000000001",
                "3119999999",
                "clave999",
            )

        self.assertEqual(repo.reactivado, 9)
        self.assertEqual(cliente.id_propietario, 9)
        self.assertEqual(cliente.nombre, "Nombre anterior")
        self.assertEqual(cliente.telefono, "3001234567")
        self.assertEqual(cliente.clave_hash, "hash-anterior")
        self.assertTrue(cliente.habilitado)


if __name__ == "__main__":
    unittest.main()
