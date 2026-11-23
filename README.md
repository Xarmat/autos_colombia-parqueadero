# Autos Colombia: sistema de información para un parqueadero

Aplicación de escritorio para gestionar la operación diaria del parqueadero "Autos Colombia", que presta el servicio por mensualidad. Permite registrar las entradas y salidas de vehículos desde dos puertas, administrar clientes, vehículos y celdas, consultar el estado de ocupación y consultar los datos asociados a cada cliente. Es un proyecto académico de la asignatura Ingeniería de Software, desarrollado por iteraciones.

## Tecnologías

| Pieza | Tecnología |
|---|---|
| Lenguaje | Python 3.10 o superior |
| Interfaz gráfica | PySide6 (`PySide6>=6.6`) |
| Base de datos | PostgreSQL |
| Conector PostgreSQL | `psycopg[binary]>=3.1` |

No existe configuración de frontend web ni de paquetes de Node.js en este proyecto.

## Cómo ejecutarlo

1. Instala Python 3.10 o superior y PostgreSQL.
2. Desde la carpeta del proyecto, crea un entorno virtual:

   ```bash
   python -m venv .venv
   ```

3. Actívalo:

   ```bash
   source .venv/bin/activate
   ```

   En Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. Instala las dependencias reales del proyecto:

   ```bash
   pip install -r requirements.txt
   ```

5. Crea la base de datos vacía `parqueadero` desde PostgreSQL o con:

   ```bash
   createdb parqueadero
   ```

6. Configura las variables de conexión si los datos locales no coinciden con los valores predeterminados del programa.

   ```bash
   export PARQ_DB_HOST=127.0.0.1
   export PARQ_DB_PORT=5432
   export PARQ_DB_NAME=parqueadero
   export PARQ_DB_USER=parq_app
   export PARQ_DB_PASSWORD=Parq_app123
   ```

   En Windows PowerShell:

   ```powershell
   $env:PARQ_DB_HOST="127.0.0.1"
   $env:PARQ_DB_PORT="5432"
   $env:PARQ_DB_NAME="parqueadero"
   $env:PARQ_DB_USER="parq_app"
   $env:PARQ_DB_PASSWORD="Parq_app123"
   ```

7. Crea las tablas y carga los datos iniciales:

   ```bash
   python -m scripts.inicializar_datos
   ```

   El script ejecuta `sql/esquema.sql` y puede repetirse. Crea o actualiza las columnas necesarias, deja dos puertas, 80 celdas (10 de motos y 70 de vehículos) y carga usuarios y vehículos de prueba.

8. Ejecuta la aplicación:

   ```bash
   python main.py
   ```

El programa no carga automáticamente un archivo `.env`. La aplicación lee las variables con `os.getenv`, usando los valores predeterminados anteriores. El archivo `.env.example` es una referencia alternativa que usa `postgres` como usuario y contraseña; sus valores no se aplican sin exportarlos antes de ejecutar el programa.

Si no se usa el usuario predeterminado `parq_app`, se pueden definir las variables anteriores en la terminal. PostgreSQL debe ser accesible desde `PARQ_DB_HOST` y `PARQ_DB_PORT`.

## Variables de entorno

| Variable | Valor predeterminado en el código | Uso |
|---|---|---|
| `PARQ_DB_HOST` | `127.0.0.1` | Host de PostgreSQL |
| `PARQ_DB_PORT` | `5432` | Puerto de PostgreSQL |
| `PARQ_DB_NAME` | `parqueadero` | Nombre de la base de datos |
| `PARQ_DB_USER` | `parq_app` | Usuario de conexión |
| `PARQ_DB_PASSWORD` | `Parq_app123` | Contraseña de conexión |

El timeout de conexión configurado en el código es de 5 segundos.

## Datos de prueba

| Rol | Identificación | Clave |
|---|---|---|
| Operario | `dia1`, `dia2` o `noche1` | `1234` |
| Cliente | documento `1000000001`, `1000000002` o `1000000003` | `123456` |

Los operarios deben seleccionar una puerta al iniciar sesión.

Vehículos y propietarios cargados:

| Placa | Tipo | Propietario |
|---|---|---|
| `ABC123` | Vehículo | documento `1000000001` |
| `XYZ789` | Vehículo | documento `1000000001` |
| `DEF456` | Vehículo | documento `1000000003` |
| `MOT12A` | Moto | documento `1000000002` |

## Estructura real del proyecto

```text
parqueadero/
├── main.py                 # punto de entrada de la aplicación Qt
├── requirements.txt        # PySide6 y psycopg
├── .env.example            # referencia de variables de PostgreSQL
├── sql/
│   └── esquema.sql         # tablas, índices y columnas de iteraciones
├── database/
│   └── conexion.py         # conexiones y manejo de transacciones
├── models/
│   ├── entidades.py        # sesiones y entidades del dominio
│   ├── enums.py            # tipos y estados
│   └── seguridad.py        # generación y comprobación de claves
├── excepciones/
│   └── errores.py          # errores controlados para la interfaz
├── repositories/           # consultas SQL de PostgreSQL
├── services/               # reglas de negocio y casos de uso
├── ui/                     # ventanas PySide6 y estilos
└── scripts/
    ├── inicializar_datos.py     # crea o actualiza el esquema y los datos iniciales
    └── prueba_concurrencia.py   # prueba el control de celdas simultáneas
```

Las capas se comunican en un solo sentido:

```text
ui -> services -> repositories -> PostgreSQL
```

Las ventanas no ejecutan SQL directamente. Las operaciones usan transacciones en `database/conexion.py`, y los errores de conexión o comunicación con la base se traducen a errores controlados para la interfaz.

## Qué puede hacer cada rol

**Operario:** inicia sesión con su usuario, contraseña y puerta. Puede registrar ingresos y salidas, registrar novedades, consultar ocupación y el estado de las 80 celdas, corregir la celda de un vehículo, registrar o editar clientes y vehículos, consultar sus datos y habilitar o inhabilitar clientes y vehículos.

**Cliente:** inicia sesión con su documento y contraseña. Puede consultar sus datos personales, sus vehículos y el valor mensual asociado a su cuenta. El portal es de solo consulta.

## Flujo de un ingreso

```text
main.py
  -> LoginView
  -> PanelView
  -> IngresoView
  -> IngresoService.verificar_ingreso
  -> IngresoService.registrar_ingreso
  -> CeldaRepository.asignar_disponible
  -> MovimientoRepository.crear
```

Al verificar un ingreso se revisa que el vehículo exista, esté habilitado y no tenga ya un movimiento abierto. Después se comprueba la disponibilidad de una celda compatible.

## Control de duplicados

Dos operarios pueden registrar ingresos al mismo tiempo desde las dos puertas. El sistema bloquea la asignación de una celda disponible y la base de datos conserva índices únicos como segunda defensa:

- una celda solo puede tener un movimiento abierto;
- un vehículo solo puede tener un movimiento abierto.

Para ejecutar la prueba de concurrencia:

```bash
python -m scripts.prueba_concurrencia
```

La prueba crea temporalmente 70 vehículos y 13 motos, intenta ingresarlos simultáneamente desde las dos puertas y limpia sus datos al terminar. Se espera que ingresen 70 vehículos y 10 motos (80 ingresos) y que las 3 motos sobrantes sean rechazadas por falta de cupo.

## Comandos útiles

```bash
# Crear o actualizar el esquema y cargar datos de prueba
python -m scripts.inicializar_datos

# Ejecutar la aplicación
python main.py

# Verificar asignación simultánea de celdas
python -m scripts.prueba_concurrencia
```
