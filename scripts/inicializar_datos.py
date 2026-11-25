"""Crea las tablas y carga los datos iniciales. Se puede ejecutar varias veces.

Uso (desde la carpeta del proyecto):
    python -m scripts.inicializar_datos

Carga: 2 puertas, 80 celdas (10 de motos y 70 de vehículos), 3 operarios de prueba
(clave 1234) y algunos propietarios y vehículos de ejemplo.
"""
from pathlib import Path
from datetime import date, timedelta
import os

from dateutil.relativedelta import relativedelta

from database.conexion import transaccion
from models.seguridad import generar_hash

RUTA_ESQUEMA = Path(__file__).resolve().parent.parent / "sql" / "esquema.sql"

OPERARIOS = [  # (nombre, usuario, turno)
    ("Operario Día 1", "dia1", "DIA"),
    ("Operario Día 2", "dia2", "DIA"),
    ("Operario Noche", "noche1", "NOCHE"),
]
PROPIETARIOS = [  # (nombre, documento, teléfono)
    ("Laura Gómez", "1000000001", "3001112233"),
    ("Carlos Ruiz", "1000000002", "3004445566"),
    ("Marta Pérez", "1000000003", "3007778899"),
]
VEHICULOS = [  # (placa, tipo, marca, color, documento del propietario)
    ("ABC123", "VEHICULO", "Mazda", "Rojo", "1000000001"),
    ("XYZ789", "VEHICULO", "Renault", "Gris", "1000000001"),  # un dueño con 2 vehículos
    ("MOT12A", "MOTO", "Yamaha", "Negro", "1000000002"),
    ("DEF456", "VEHICULO", "Chevrolet", "Azul", "1000000003"),
]

TARIFAS_EJEMPLO = {"MOTO": 60_000, "VEHICULO": 120_000}


def _periodo_mensual(inicio: date, dia_ancla: int) -> date:
    """Calcula el cierre de un mes conservando el día ancla."""
    siguiente = inicio + relativedelta(months=1, day=dia_ancla)
    return siguiente - timedelta(days=1)


def _cargar_pagos_ejemplo(conn) -> None:
    """Carga periodos para demostrar mensualidad futura, al día y en mora."""
    hoy = date.today()
    comienzos = {
        "ABC123": hoy - timedelta(days=10),
        "XYZ789": hoy + timedelta(days=3),
        "MOT12A": hoy - relativedelta(months=1) - timedelta(days=5),
        "DEF456": hoy - relativedelta(months=1) - timedelta(days=16),
    }
    operario = conn.execute(
        "SELECT id_operario FROM operario WHERE usuario='dia1'"
    ).fetchone()
    if operario is None:
        raise RuntimeError("No se encontró el operario de ejemplo dia1.")

    for placa, inicio in comienzos.items():
        existe = conn.execute(
            "SELECT 1 FROM pago_detalle WHERE placa=%s AND concepto='MENSUALIDAD' LIMIT 1",
            (placa,),
        ).fetchone()
        if existe:
            continue
        vehiculo = conn.execute(
            "SELECT tipo FROM vehiculo WHERE placa=%s",
            (placa,),
        ).fetchone()
        if vehiculo is None:
            continue
        fin = _periodo_mensual(inicio, inicio.day)
        tarifa = TARIFAS_EJEMPLO[vehiculo["tipo"]]
        pago = conn.execute(
            "INSERT INTO pago (placa, medio_pago, id_operario, valor_total) "
            "VALUES (%s, 'EFECTIVO', %s, %s) RETURNING id_pago",
            (placa, operario["id_operario"], tarifa),
        ).fetchone()
        conn.execute(
            "INSERT INTO pago_detalle "
            "(id_pago, placa, concepto, fecha_inicio, fecha_fin, dia_ancla, valor) "
            "VALUES (%s, %s, 'MENSUALIDAD', %s, %s, %s, %s)",
            (pago["id_pago"], placa, inicio, fin, inicio.day, tarifa),
        )


def main() -> None:
    nombre_admin = os.getenv("PARQ_ADMIN_NAME", "Administrador").strip()
    usuario_admin = os.getenv("PARQ_ADMIN_USER", "admin").strip()
    clave_admin = os.getenv("PARQ_ADMIN_PASSWORD", "Admin1234!")
    if not nombre_admin or len(nombre_admin) > 30:
        raise ValueError("PARQ_ADMIN_NAME debe tener entre 1 y 30 caracteres.")
    if not usuario_admin or len(usuario_admin) > 14 or not usuario_admin.isalnum():
        raise ValueError("PARQ_ADMIN_USER debe tener entre 1 y 14 letras o números.")
    if not 6 <= len(clave_admin) <= 10:
        raise ValueError("PARQ_ADMIN_PASSWORD debe tener entre 6 y 10 caracteres.")

    with transaccion() as conn:
        # 1. Tablas e índices
        conn.execute(RUTA_ESQUEMA.read_text(encoding="utf-8"))

        with conn.cursor() as cur:
            # 2. Puertas
            cur.executemany(
                "INSERT INTO puerta (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING",
                [("Puerta 1",), ("Puerta 2",)])

            # 3. Celdas: M01-M10 para motos y V01-V70 para vehículos
            celdas = [(f"M{i:02d}", "MOTO") for i in range(1, 11)]
            celdas += [(f"V{i:02d}", "VEHICULO") for i in range(1, 71)]
            cur.executemany(
                "INSERT INTO celda (codigo, tipo) VALUES (%s, %s) ON CONFLICT (codigo) DO NOTHING",
                celdas)

            # 4. Operarios de prueba (la clave se guarda con hash, nunca en claro)
            cur.executemany(
                "INSERT INTO operario (nombre, usuario, clave_hash, turno) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (usuario) DO NOTHING",
                [(n, u, generar_hash("1234"), t) for n, u, t in OPERARIOS])

            # Cuenta administrativa de arranque; no se sobreescribe al repetir el script.
            cur.execute(
                "INSERT INTO administrador (nombre, usuario, clave_hash) "
                "VALUES (%s, %s, %s) ON CONFLICT (usuario) DO NOTHING",
                (
                    nombre_admin,
                    usuario_admin,
                    generar_hash(clave_admin),
                ),
            )

            # 5. Propietarios y vehículos de ejemplo (clave inicial: 123456)
            cur.executemany(
                "INSERT INTO propietario (nombre, documento, telefono, clave_hash, habilitado) "
                "VALUES (%s, %s, %s, %s, true) "
                "ON CONFLICT (documento) DO UPDATE SET clave_hash = EXCLUDED.clave_hash "
                "WHERE propietario.clave_hash IS NULL OR propietario.clave_hash = ''",
                [(n, d, t, generar_hash("123456")) for n, d, t in PROPIETARIOS],
            )
            cur.executemany(
                "INSERT INTO vehiculo (placa, tipo, marca, color, id_propietario) "
                "SELECT %s, %s, %s, %s, id_propietario FROM propietario WHERE documento = %s "
                "ON CONFLICT (placa) DO NOTHING",
                VEHICULOS)
        _cargar_pagos_ejemplo(conn)
    print("Base de datos lista: esquema, 2 puertas, 80 celdas y datos de prueba con pagos.")


if __name__ == "__main__":
    main()
