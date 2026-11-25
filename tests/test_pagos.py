import unittest
from datetime import date, datetime
from unittest.mock import MagicMock

from excepciones.errores import DatosInvalidos, PagoPendiente
from models.entidades import Operario, Puerta, Sesion
from models.enums import ConceptoPago, MedioPago, TipoVehiculo, Turno
from repositories.pago_repository import PagoRepository
from services.pago_service import PagoService


class RepositorioPagosFalso:
    def __init__(self, detalles=None):
        self.detalles = detalles or []
        self.vehiculo = {
            "placa": "ABC123",
            "tipo": "VEHICULO",
            "vehiculo_habilitado": True,
            "id_propietario": 1,
            "nombre_cliente": "Cliente",
            "cliente_habilitado": True,
            "fecha_habilitacion": datetime(2026, 1, 1),
            "fecha_nuevo_registro": datetime(2026, 1, 1),
        }
        self.registro = None

    def buscar_vehiculo(self, conn, placa, bloquear=False):
        return self.vehiculo

    def listar_detalles(self, conn, placa):
        return self.detalles

    def obtener_ultima_solicitud_renovacion(self, conn, placa):
        return None

    def registrar(
        self, conn, placa, id_operario, medio, valor_total, detalles, fecha_activacion
    ):
        self.registro = (
            conn, placa, id_operario, medio, valor_total, detalles, fecha_activacion
        )
        return {
            "id_pago": 7,
            "fecha_pago": datetime(2026, 4, 20, 10, 0),
            "medio_pago": medio.value,
            "valor_total": valor_total,
            "nombre_cliente": "Cliente",
            "tipo_vehiculo": "VEHICULO",
            "usuario_operario": "dia1",
        }


def mensualidad(inicio, fin, ancla=5):
    return {
        "concepto": "MENSUALIDAD",
        "fecha_inicio": inicio,
        "fecha_fin": fin,
        "dia_ancla": ancla,
        "valor": 120_000,
        "fecha_pago": datetime(2026, 1, 1),
    }


class PagoRepositoryTests(unittest.TestCase):
    def test_registra_detalles_usando_el_cursor_de_psycopg(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor
        filas = [
            {"id_pago": 7, "fecha_pago": datetime(2026, 11, 24), "medio_pago": "EFECTIVO"},
            {"nombre_cliente": "Cliente", "tipo": "VEHICULO"},
            {"usuario": "dia1"},
        ]
        resultados = [MagicMock() for _ in filas]
        for resultado, fila in zip(resultados, filas):
            resultado.fetchone.return_value = fila
        conn.execute.side_effect = resultados

        PagoRepository().registrar(
            conn,
            "ABC123",
            1,
            MedioPago.EFECTIVO,
            120_000,
            [{
                "concepto": ConceptoPago.MENSUALIDAD,
                "fecha_inicio": date(2026, 12, 5),
                "fecha_fin": date(2027, 1, 4),
                "dia_ancla": 5,
                "valor": 120_000,
            }],
            datetime(2026, 11, 24),
        )

        cursor.executemany.assert_called_once()
        self.assertEqual(
            cursor.executemany.call_args.args[1],
            [(7, "ABC123", "MENSUALIDAD", date(2026, 12, 5),
              date(2027, 1, 4), 5, datetime(2026, 11, 24), 120_000)],
        )


class PagoServiceTests(unittest.TestCase):
    def test_periodo_mensual_conserva_ancla_en_fin_de_mes(self):
        primer_inicio, primer_fin = PagoService._periodo_mensual(
            date(2024, 1, 31), 31
        )
        siguiente_inicio = date(2024, 2, 29)
        siguiente_inicio, siguiente_fin = PagoService._periodo_mensual(
            siguiente_inicio, 31
        )

        self.assertEqual((primer_inicio, primer_fin), (date(2024, 1, 31), date(2024, 2, 28)))
        self.assertEqual((siguiente_inicio, siguiente_fin), (date(2024, 2, 29), date(2024, 3, 30)))

    def test_pago_dia_14_de_mora_cubre_periodo_desde_fecha_original(self):
        repo = RepositorioPagosFalso([
            mensualidad(date(2026, 3, 5), date(2026, 4, 4))
        ])
        servicio = PagoService(repo, reloj=lambda: date(2026, 4, 18))

        detalles = servicio._calcular_detalles(
            TipoVehiculo.VEHICULO, repo.detalles, date(2026, 4, 18), None
        )

        self.assertEqual(len(detalles), 1)
        self.assertEqual(detalles[0]["fecha_inicio"], date(2026, 4, 5))
        self.assertEqual(detalles[0]["fecha_fin"], date(2026, 5, 4))
        self.assertEqual(detalles[0]["concepto"], ConceptoPago.MENSUALIDAD)

    def test_pago_dia_15_cobra_gracia_y_reinicia_ancla_en_fecha_de_pago(self):
        repo = RepositorioPagosFalso([
            mensualidad(date(2026, 3, 5), date(2026, 4, 4))
        ])
        servicio = PagoService(repo, reloj=lambda: date(2026, 4, 20))

        detalles = servicio._calcular_detalles(
            TipoVehiculo.VEHICULO, repo.detalles, date(2026, 4, 20), None
        )

        self.assertEqual(detalles[0]["concepto"], ConceptoPago.PRORRATEO)
        self.assertEqual(detalles[0]["fecha_inicio"], date(2026, 4, 5))
        self.assertEqual(detalles[0]["fecha_fin"], date(2026, 4, 19))
        self.assertEqual(detalles[0]["valor"], 58_065)
        self.assertEqual(detalles[1]["fecha_inicio"], date(2026, 4, 20))
        self.assertEqual(detalles[1]["fecha_fin"], date(2026, 5, 19))
        self.assertEqual(detalles[1]["dia_ancla"], 20)

    def test_estado_no_cambia_a_proximo_si_hay_ciclo_actual_y_futuro_pagado(self):
        repo = RepositorioPagosFalso([
            mensualidad(date(2026, 3, 5), date(2026, 4, 4)),
            mensualidad(date(2026, 4, 5), date(2026, 5, 4)),
        ])
        servicio = PagoService(repo, reloj=lambda: date(2026, 3, 28))

        estado = servicio.consultar_estado_en_transaccion(None, "ABC123")

        self.assertEqual(estado.estado, "Al día")
        self.assertEqual(estado.fecha_inicio, date(2026, 3, 5))
        self.assertEqual(estado.fecha_vencimiento, date(2026, 4, 4))
        self.assertEqual(estado.fecha_cubierta_hasta, date(2026, 5, 4))
        self.assertFalse(estado.bloqueado_ingreso)
        self.assertFalse(estado.renovacion_disponible)

    def test_renovacion_se_ofrece_siete_dias_antes_del_vencimiento(self):
        repo = RepositorioPagosFalso([
            mensualidad(date(2026, 4, 5), date(2026, 5, 4))
        ])
        servicio = PagoService(repo, reloj=lambda: date(2026, 4, 27))

        estado = servicio.consultar_estado_en_transaccion(None, "ABC123")

        self.assertTrue(estado.renovacion_disponible)

    def test_ingreso_se_bloquea_desde_el_dia_15_de_mora(self):
        repo = RepositorioPagosFalso([
            mensualidad(date(2026, 3, 5), date(2026, 4, 4))
        ])
        servicio = PagoService(repo, reloj=lambda: date(2026, 4, 19))

        with self.assertRaises(PagoPendiente):
            servicio.validar_ingreso(None, "ABC123")

    def test_reactivacion_descarta_coberturas_pagas_anteriores(self):
        repo = RepositorioPagosFalso([
            mensualidad(date(2026, 3, 5), date(2026, 4, 4))
        ])
        repo.vehiculo["fecha_habilitacion"] = datetime(2026, 4, 10)
        repo.vehiculo["fecha_nuevo_registro"] = datetime(2026, 4, 10)
        servicio = PagoService(repo, reloj=lambda: date(2026, 4, 20))

        estado = servicio.consultar_estado_en_transaccion(None, "ABC123")

        self.assertEqual(estado.estado, "Pago pendiente")
        self.assertIsNone(estado.fecha_inicio)

    def test_pago_requiere_sesion_de_operario(self):
        servicio = PagoService(RepositorioPagosFalso(), reloj=lambda: date(2026, 4, 20))

        with self.assertRaises(DatosInvalidos):
            servicio.registrar_pago_en_transaccion(
                None, "ABC123", MedioPago.EFECTIVO, object()
            )

    def test_registra_comprobante_con_el_operario_autenticado(self):
        repo = RepositorioPagosFalso()
        servicio = PagoService(repo, reloj=lambda: date(2026, 4, 20))
        operario = Operario(1, "Operario Día 1", "dia1", "hash", Turno.DIA)
        sesion = Sesion(operario, Puerta(1, "Puerta 1"))

        comprobante = servicio.registrar_pago_en_transaccion(
            object(), "ABC123", MedioPago.EFECTIVO, sesion, date(2026, 4, 20)
        )

        self.assertEqual(repo.registro[2], 1)
        self.assertEqual(comprobante.usuario_operario, "dia1")
        self.assertEqual(comprobante.placa, "ABC123")
        self.assertEqual(comprobante.valor_total, 120_000)


if __name__ == "__main__":
    unittest.main()
