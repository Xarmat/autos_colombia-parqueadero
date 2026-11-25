# Autos Colombia

Aplicación de escritorio para administrar la operación del parqueadero Autos Colombia. Desarrollada en Python, PySide6 y PostgreSQL.

## Estado

Las iteraciones 1 y 2 y la gestión de pagos de la iteración 3 están implementadas en la aplicación.

## Funcionalidades

- **Operario:** registra entradas y salidas por placa desde una de las dos puertas y reporta errores.
- **Administrador:** gestiona personal, clientes, vehículos, celdas y solicitudes.
- **Operario:** registra pagos adelantados por vehículo y entrega comprobantes.
- **Administrador:** consulta el estado de pago por vehículo y atiende solicitudes de baja de clientes.
- **Cliente:** consulta sus datos, vehículos, valor mensual y estado de pago; puede informar si continuará o solicitar la baja.
- El sistema controla la ocupación de 80 celdas, conserva el historial de bajas y protege las asignaciones simultáneas.

## Requisitos

- Python 3.10 o superior
- PostgreSQL
- Dependencias de Python indicadas en `requirements.txt`

## Instalación y ejecución

Desde la carpeta del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
createdb parqueadero
python -m scripts.inicializar_datos
python main.py
```

En Windows, activa el entorno con:

```powershell
.venv\Scripts\Activate.ps1
```

El usuario de PostgreSQL predeterminado es `parq_app`; debe existir y tener permisos sobre la base `parqueadero`. Si tus credenciales difieren, configura `PARQ_DB_HOST`, `PARQ_DB_PORT`, `PARQ_DB_NAME`, `PARQ_DB_USER` y `PARQ_DB_PASSWORD` en el entorno antes de inicializar. También puedes definir `PARQ_ADMIN_NAME`, `PARQ_ADMIN_USER` y `PARQ_ADMIN_PASSWORD` para la cuenta administrativa inicial. `.env.example` sirve como referencia; el programa no carga ese archivo automáticamente.

## Cuentas de prueba

El inicializador carga estas cuentas para uso local:

| Rol | Usuario o documento | Clave |
|---|---|---|
| Administrador | `admin` | `Admin1234!` |
| Operario | `dia1`, `dia2` o `noche1` | `1234` |
| Cliente | `1000000001`, `1000000002` o `1000000003` | `123456` |

El operario selecciona una puerta al iniciar sesión.

## Gestión de pagos

Cada vehículo tiene su propio periodo mensual y su historial de pagos. Al registrar un cliente y vehículo desde el flujo contextual del operario se exige el pago inicial y se conserva la operación completa en una sola transacción. Si el administrador crea un cliente o agrega un vehículo sin pago, el ingreso queda bloqueado hasta que el operario registre el pago adelantado.

Los medios disponibles son efectivo, código QR y recibo bancario presentado al operario. Para este último no hay integración con el banco: el operario revisa el soporte y confirma el registro. El comprobante muestra la fecha y medio de pago, el vehículo, el usuario que lo registró, el valor y las coberturas de mensualidad/prorrateo; desde el diálogo se puede imprimir.

Tarifas de ejemplo actuales: moto $60.000 y vehículo $120.000 mensuales. El profesor no definió tarifas, así que estos valores se conservan como supuesto y están centralizados en `services/pago_service.py`. Los ciclos ordinarios conservan el día ancla para fechas 29–31. Si pasan 15 días calendario desde el vencimiento, se bloquean nuevos ingresos; al reactivar, el sistema cobra el prorrateo de los primeros 15 días de gracia y una mensualidad completa desde la fecha del pago, que pasa a ser el nuevo día ancla. Estos comportamientos son supuestos del proyecto, no condiciones indicadas directamente por el profesor.

El cliente ve un aviso rojo cuando tiene pagos pendientes. Siete días antes del vencimiento puede indicar si continuará o enviar una solicitud de baja al administrador; no se realizan cobros automáticos. La baja aprobada desactiva lógicamente la cuenta y sus vehículos, sin borrar historial. Al volver a registrarse con el mismo documento se reactiva la cuenta existente; los periodos anteriores no se modifican y el nuevo servicio requiere pago adelantado.

El inicializador prepara pagos de ejemplo: una mensualidad próxima, una vigente y dos vehículos en mora para probar el aviso y el bloqueo.

