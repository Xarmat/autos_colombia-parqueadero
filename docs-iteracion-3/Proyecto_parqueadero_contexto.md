# Autos Colombia: contexto completo del proyecto

Documento de contexto para retomar el proyecto en una conversación nueva. Resume el problema, las reglas de negocio, las decisiones de diseño, la estructura del código, el flujo de ejecución, lo que ya está hecho y lo que falta. El README explica la instalación, la ejecución y las funciones principales.

**Estado actual:** iteración 3 (gestión de pagos) en curso. La lógica de pagos está implementada y los incisos 1 a 6 de la actividad están elaborados; queda pendiente el plan de pruebas resumido en Excel (inciso 7). Las iteraciones 1 y 2 están terminadas.

## 1. Qué es

Aplicación de escritorio para gestionar la operación diaria del parqueadero "Autos Colombia", que presta el servicio por **mensualidad**. Es un proyecto académico de la asignatura **Ingeniería de Software** (carrera Ingeniería de Software y Datos). Se entrega por iteraciones; cada una incluye un documento PDF (portada, introducción, entregables y conclusiones) y el código fuente en GitHub.

| Pieza | Tecnología |
|---|---|
| Lógica | Python 3.10 o superior (probado en 3.12) |
| Interfaces | PySide6 (Qt), tema oscuro con fondo negro |
| Base de datos | PostgreSQL, con `psycopg` 3 (SQL directo, sin ORM) |
| Contraseñas | PBKDF2-SHA256 con sal (`hashlib`) |
| Diagramas | se generan como código de Mermaid; el estudiante los visualiza en mermaid.live y, si hace falta, los pasa a draw.io. Los mockups de la iteración 3 se hacen con PlantUML (Salt) |
| Control de versiones | Git y GitHub (un repositorio con una sola subida inicial) |

## 2. Iteraciones de la actividad

1. **Iteración 1 (terminada):** gestión de la entrada y salida de vehículos. Documento y código entregados.
2. **Iteración 2 (terminada):** gestión de usuarios y celdas. La aplicación fue ampliada tras la retroalimentación docente (rol administrativo, solicitudes de corrección, traslado de celdas). Las historias, mockups, pruebas académicas y casos de uso de esa iteración pueden quedar desfasados respecto al código actual; se revisan solo si hace falta.
3. **Iteración 3 (en curso):** gestión de pagos. La lógica ya está implementada en el código. Los incisos 1 a 6 están elaborados en `iteracion_3_EA3(Actividad).md` y sus archivos de apoyo; queda pendiente el inciso 7, el plan de pruebas resumido en Excel.

**Entregables documentales:** cada iteración se entrega como PDF (portada, introducción, entregables y conclusiones). La introducción y las conclusiones se escriben al final, cuando ya están todos los entregables. En la iteración 2 los incisos fueron A a F; en la 3 van del 1 al 7.

## 3. Reglas de negocio

**Dadas por el profesor**

- 3 operarios: 2 de día (uno por puerta) y 1 de noche. 2 puertas, **ambas de entrada y salida**; los operarios registran en simultáneo.
- Se admiten carros, motos, camionetas y similares; se excluyen camiones y vehículos de carga pesada.
- **80 celdas:** 10 de motos (`M01` a `M10`) y 70 de vehículos (`V01` a `V70`).
- Al ingresar: se verifica que el vehículo esté registrado (con su propietario), se le asigna una celda libre del tipo correcto y nunca puede haber más vehículos dentro que celdas.
- **Anti-duplicados:** dos operarios no pueden asignar la misma celda a la vez; la salida libera su celda salvo que esta esté inhabilitada por el administrador.
- **La mensualidad se cobra por vehículo**, no por celda ni por cliente.
- El registro de un vehículo guarda nombre del dueño, placa, color y marca.
- Roles del sistema: **Administrador**, **Operario** y **Cliente**.
- El profesor pidió un reporte (vehículos registrados, celdas disponibles) sin definir formato ni frecuencia: sigue pendiente.

**Decisiones acordadas con el estudiante**

- El **Administrador** inicia sesión sin seleccionar puerta y administra las cuentas del personal, clientes y vehículos, el estado de las celdas y las solicitudes de los operarios. También resuelve los errores de placa y las correcciones de celda.
- Hay 3 puestos de operario: 2 en turno de día y 1 en turno de noche. El administrador crea y edita cuentas; al reemplazar a alguien, la baja es lógica y se crea la cuenta nueva en la misma operación para no perder la trazabilidad.
- El **Operario** inicia sesión con usuario, contraseña y puerta. Registra entradas, salidas y pagos por placa, y envía solicitudes cuando detecta una equivocación. Si una placa no está registrada, puede crear al cliente y ese vehículo mediante un formulario contextual que registra también el pago inicial; no consulta ni administra otros datos de clientes ni celdas.
- El **Cliente** inicia sesión con su documento y una clave inicial que le da el operario. Consulta sus datos, vehículos, valor mensual y estado de pagos, y puede indicar si continuará o solicitar una baja al administrador. No registra pagos y solo ve lo suyo.
- El **valor mensual** que ve un cliente es la suma de la tarifa de sus vehículos habilitados según el tipo. Las tarifas de ejemplo están centralizadas en `PagoService`: moto 60.000 y vehículo 120.000. Son valores de ejemplo porque el profesor no definió tarifas y no existe una tabla de tarifas en la base actual. La mensualidad, la fecha de vencimiento, el pago y el estado de pago se gestionan por vehículo; el portal conserva el resumen total por cliente (ver las decisiones asumidas de la iteración 3, sección 8).
- Las celdas son fijas: siempre hay 80; no se crean ni eliminan desde la aplicación. El administrador puede inhabilitarlas por daño, indicando un motivo. La ocupación se calcula con movimientos activos; una corrección conserva bloqueada la celda anterior hasta que el administrador confirma el traslado.
- Las bajas son **lógicas** (inhabilitar) y reversibles: nunca se borran datos con historial. Habilitar un cliente habilita también todos sus vehículos.
- Mientras un vehículo está dentro no se puede cambiar su placa ni su tipo ni inhabilitarlo, ni inhabilitar a su cliente.
- Es un trabajo académico: se prefieren soluciones realistas y sencillas antes que sobrediseñar.

## 4. Estructura del código

```
parqueadero/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── Proyecto_parqueadero_contexto.md
├── sql/esquema.sql
├── database/conexion.py
├── models/            enums.py, entidades.py, seguridad.py
├── excepciones/       errores.py
├── repositories/      operario, puerta, vehiculo, celda, celda_estado,
│                      movimiento, novedad, cliente, administrador,
│                      solicitud, pago, solicitud_cliente (*_repository.py)
├── services/          auth, ingreso, salida, ocupacion, novedad,
│                      cliente, celda, administrador, solicitud, pago,
│                      solicitud_cliente (*_service.py),
│                      utilidades.py, contenedor.py
├── ui/                comun.py, login_view, panel_view, ingreso_view, salida_view,
│                      admin_panel_view, personal_view, solicitudes_view,
│                      solicitud_view, cliente_view, celda_view, cliente_portal_view
└── scripts/           inicializar_datos.py, prueba_concurrencia.py
```

**Regla de capas:** `ui` solo habla con `services`; `services` con `repositories` y con `database` (para abrir transacciones); los `repositories` solo ejecutan SQL sobre la conexión que reciben. `models` y `excepciones` los usan todas las capas. Ninguna ventana toca la base de datos.

### Archivos principales

**`main.py`**: crea la aplicación Qt, aplica los estilos y arma los servicios. Repite un ciclo de inicio de sesión y abre `PanelView` (operario), `AdminPanelView` (administrador) o `ClientePortalView` (cliente).

**`database/conexion.py`**: `transaccion()` abre una conexión nueva, la entrega dentro de una transacción (commit si todo sale bien, rollback si falla) y la cierra. Las filas llegan como diccionarios. Traduce los fallos de comunicación a `ErrorBaseDatos`.

**`models/entidades.py`** (dataclasses): incluye `Administrador`, `SesionAdministrador`, `SolicitudCambio`, `EstadoPagoVehiculo`, `DetallePago`, `ComprobantePago` y `SolicitudCliente`, además de `Propietario`, `Vehiculo`, `Celda`, `Puerta`, `Operario`, `Movimiento`, `Novedad`, `Ocupacion` y `Sesion`.

**`excepciones/errores.py`**: todas heredan de `ParqueaderoError` y su mensaje se muestra tal cual al usuario: `ErrorBaseDatos`, `CredencialesInvalidas`, `DatosInvalidos`, `VehiculoNoRegistrado`, `VehiculoYaDentro`, `VehiculoNoEstaDentro`, `SinCupo`, `ClienteYaExiste`, `VehiculoYaExiste`, `ClienteConVehiculoDentro`, `ClienteInhabilitado`, `VehiculoDentro`, `VehiculoInhabilitado` y `CeldaOcupada` (uso interno, para el reintento de ingresos).

**Repositorios** (todos reciben la conexión `conn` como primer parámetro):

| Archivo | Métodos |
|---|---|
| `operario_repository.py` | `buscar_por_usuario` |
| `administrador_repository.py` | autenticación y CRUD lógico de administradores y operarios |
| `solicitud_repository.py` | crear, listar y resolver solicitudes |
| `puerta_repository.py` | `listar` |
| `vehiculo_repository.py` | `buscar_por_placa` (trae propietario) |
| `cliente_repository.py` | `buscar_clientes`, `buscar_por_documento`, `buscar_por_id`, `listar_vehiculos_cliente`, `crear_cliente`, `actualizar_cliente`, `cambiar_estado_cliente`, `cambiar_clave_cliente`, `buscar_vehiculo_por_placa`, `crear_vehiculo`, `actualizar_vehiculo`, `cambiar_estado_vehiculo`, `cliente_tiene_vehiculos_dentro`, `vehiculo_esta_dentro` |
| `celda_repository.py` | `asignar_disponible` (bloquea la celda), `contar_libres`, `contar_por_estado` |
| `celda_estado_repository.py` | lista celdas, cambia su estado, corrige y finaliza traslados |
| `movimiento_repository.py` | `crear`, `buscar_activo`, `cerrar`, `listar_activos` |
| `novedad_repository.py` | `crear` |
| `pago_repository.py` | consultar estado y periodos, registrar pago y sus detalles |
| `solicitud_cliente_repository.py` | crear, listar y resolver decisiones de renovación y solicitudes de baja |

**Servicios:**

| Archivo | Métodos |
|---|---|
| `auth_service.py` | `listar_puertas`, `iniciar_sesion` (operario) |
| `administrador_service.py` | CRUD de cuentas administrativas y operarios; respeta dos puestos de día y uno de noche |
| `solicitud_service.py` | crear, consultar y resolver solicitudes de error |
| `ingreso_service.py` | `verificar_ingreso` (paso 1), `registrar_ingreso` (paso 2, con reintentos). Rechaza vehículos no registrados, inhabilitados, ya dentro o sin cupo |
| `salida_service.py` | `consultar_movimiento_activo`, `registrar_salida` |
| `ocupacion_service.py` | `consultar_ocupacion` |
| `novedad_service.py` | `listar_vehiculos_dentro`, `registrar_novedad` |
| `cliente_service.py` | `buscar_clientes`, `listar_vehiculos`, `registrar_cliente`, `actualizar_cliente`, `cambiar_estado_cliente`, `restablecer_clave`, `registrar_vehiculo`, `actualizar_vehiculo`, `cambiar_estado_vehiculo`, `autenticar_cliente`, `obtener_resumen_mensual` |
| `pago_service.py` | calcular vigencias, consultar estado, validar ingresos y registrar pagos/comprobantes por vehículo |
| `solicitud_cliente_service.py` | registrar decisiones, listar y resolver solicitudes de baja |
| `celda_service.py` | listar celdas, bloquear/habilitar, corregir y finalizar traslados |
| `utilidades.py` | `normalizar_placa` |
| `contenedor.py` | `crear_servicios()` y la dataclass `Servicios` que recibe la interfaz |

**Interfaz:** `comun.py` guarda `HOJA_ESTILOS` (tema oscuro), `mostrar_error`, `mostrar_ok`, `mostrar_info`, `limitar_campo`, `limitar_texto` y `ejecutar(etiqueta, funcion)` (ejecuta una acción y muestra cualquier error en la ventana). Las ventanas son diálogos modales:

| Ventana | Para qué |
|---|---|
| `LoginView` | Selector Administrador, Operario o Cliente. El administrador entra con usuario y clave; el operario también elige puerta |
| `PanelView` | Ingreso, salida y envío de solicitudes; no muestra clientes ni celdas |
| `ClienteIngresoView` (`cliente_ingreso_view.py`) | Alta contextual atómica de cliente y vehículo cuando la placa del ingreso no está registrada |
| `PagoView` (`pago_view.py`) | Registro de pago y comprobante imprimible; solo disponible al operario |
| `SolicitudView` (`solicitud_view.py`) | Reportar un error de entrada/salida, una situación de celda u otro problema |
| `AdminPanelView` | Acceso a cuentas, clientes/vehículos, celdas y solicitudes |
| `PersonalView` (`personal_view.py`) | Crear, editar, reemplazar, desactivar y reactivar cuentas de operarios y administradores |
| `SolicitudesView` (`solicitudes_view.py`) | Revisar, corregir y responder reportes del personal |
| `IngresoView`, `SalidaView` | El operario registra por placa; no ve la celda ni datos del cliente |
| `NovedadView` (`novedad_view.py`) | Código legado de la iteración 1; ya no se ofrece en el panel operativo |
| `ClientesVehiculosView` (`cliente_view.py`) | Administración de clientes y vehículos disponible desde el panel administrativo |
| `SolicitudesClienteView` (`solicitudes_cliente_view.py`) | Revisión administrativa de decisiones de renovación y solicitudes de baja |
| `EstadoCeldasView` (`celda_view.py`) | Cuadrícula administrativa para bloquear/habilitar, corregir celdas y finalizar traslados pendientes |
| `ClientePortalView` (`cliente_portal_view.py`) | Consulta datos, vehículos, valor y estado de pago; muestra avisos y permite enviar decisiones de renovación/baja |

**Scripts:** `inicializar_datos.py` ejecuta `sql/esquema.sql` (crea o actualiza) y carga 2 puertas, 80 celdas, 3 operarios de prueba, una cuenta administrativa inicial (`admin`) y clientes/vehículos de ejemplo. La clave administrativa inicial configurable es `Admin1234!`; no se restablece si la cuenta ya existe. `prueba_concurrencia.py` comprueba la asignación simultánea de celdas.

## 5. Flujo de ejecución

**Ingreso (dos pasos):** el operario verifica una placa y confirma el ingreso. El servicio valida registro y habilitación del vehículo y propietario, evita duplicados y asigna una celda libre habilitada del tipo correcto. Como regla asumida de la iteración 3, también valida el pago del vehículo: al cumplir 15 días de mora se impiden nuevos ingresos hasta registrar el pago, pero no se expulsa un vehículo que ya está dentro. La interfaz operativa no revela información del cliente ni el código de la celda.

**Anti-duplicados (dos defensas):** la celda se bloquea con `FOR UPDATE SKIP LOCKED`; y la base tiene índices únicos parciales (`uq_celda_activa`, `uq_vehiculo_activo`) sobre los movimientos sin fecha de salida. Si aun así chocan, el repositorio lanza `CeldaOcupada` y el servicio reintenta hasta 3 veces.

**Salida (dos pasos):** `consultar_movimiento_activo` y `registrar_salida` (cierra el movimiento; la celda queda libre sola, porque la ocupación se calcula).

**Corregir celda:** solo el administrador puede reasignar un movimiento. `CeldaEstadoRepository.corregir_celda` bloquea y asigna una celda destino habilitada del mismo tipo, guarda origen/destino/motivo/administrador en `correccion_celda` y conserva la anterior bloqueada, sin placa, con estado visual rojo **Traslado pendiente**. El administrador finaliza el traslado cuando el vehículo ya se movió; una salida también libera automáticamente la reserva. Las solicitudes de error de placa se registran en `solicitud_cambio`; el administrador puede corregir entradas y resolver salidas equivocadas cuando la celda del registro erróneo todavía no fue reasignada.

**Clientes y vehículos:** el administrador registra y edita clientes y vehículos; documento y placa son únicos. Las bajas siguen siendo lógicas (`habilitado`) para conservar historial y no se permiten mientras haya vehículos dentro.

**Portal del cliente:** `LoginView` llama a `ClienteService.autenticar_cliente`, que valida documento, clave y que el cliente esté habilitado. `ClientePortalView` muestra solo los datos y vehículos asociados al `Propietario` autenticado y consulta el resumen mensual calculado con las tarifas de ejemplo centralizadas en `PagoService`.

## 6. Base de datos (`sql/esquema.sql`)

| Tabla | Contenido |
|---|---|
| `propietario` | id, nombre, documento (único), teléfono, `clave_hash`, `habilitado` |
| `vehiculo` | placa (llave primaria), propietario, tipo (`MOTO` o `VEHICULO`), marca, color, `habilitado` |
| `celda` | id, código (único), tipo, `habilitada`, motivo de bloqueo |
| `operario` | id, nombre, usuario (único), `clave_hash`, turno, `habilitado` |
| `administrador` | cuentas administrativas con contraseña hasheada y estado lógico |
| `puerta` | id, nombre (único) |
| `movimiento` | una visita completa: vehículo, celda, fecha, puerta y operario de ingreso y de salida (vacíos mientras el vehículo está dentro) |
| `novedad` | ligada a un movimiento, con operario, descripción y fecha |
| `solicitud_cambio` | reportes de placa/celda/otra situación, estado y resolución administrativa |
| `correccion_celda` | celda anterior y nueva, motivo, administrador y estado del traslado |
| `pago` | comprobante por vehículo, fecha, medio, operario y valor total |
| `pago_detalle` | periodos de mensualidad o prorrateo cubiertos por cada comprobante |
| `solicitud_cliente` | decisiones de renovación y solicitudes de baja, con resolución administrativa |

El archivo `esquema.sql` se puede ejecutar varias veces: usa `IF NOT EXISTS` y `ADD COLUMN IF NOT EXISTS`, así que también actualiza una base de la iteración 1 sin perder datos.

## 7. Requerimientos y historias de la iteración 2

**Funcionales implementados:** autenticación diferenciada de administrador, operario y cliente; administración de cuentas de operarios y administradores; gestión de clientes/vehículos solo por el administrador; operación de entrada/salida por placa; solicitudes de operarios y su resolución; consulta, bloqueo y corrección de celdas, con retención de celda anterior durante el traslado. Las historias y pantallas académicas quedan pendientes de actualizar en una fase posterior, según lo acordado.

**No funcionales:** integridad de placas/documentos/celdas, conservación del historial, claves hasheadas, trazabilidad de correcciones y solicitudes, concurrencia segura y separación de funciones por rol.

**Historias de usuario:** HU-U1 registrar cliente; HU-U2 registrar vehículo; HU-U3 consultar clientes; HU-U4 editar cliente; HU-U5 editar vehículo; HU-U6 inhabilitar y habilitar cliente; HU-U7 inhabilitar y habilitar vehículo; HU-U8 iniciar sesión como cliente; HU-U9 consultar mis datos; HU-U10 consultar mis vehículos; HU-U11 consultar valor a pagar; HU-C1 consultar estado de celdas; HU-C2 corregir celda de un vehículo.

**Componentes actuales de la iteración 2:** `AdminPanelView`, `PanelView`, `PersonalView`, `SolicitudesView`, `SolicitudView`, `ClientesVehiculosView`, `EstadoCeldasView`, `ClientePortalView`; servicios de administración, solicitudes, clientes y celdas.

**Componentes incorporados en la iteración 3:** `PagoView` y `ClienteIngresoView`; `PagoService` y `SolicitudClienteService`; `PagoRepository` y `SolicitudClienteRepository`. El flujo de pago también amplía las consultas del portal del cliente y la validación del ingreso. El diagrama acumulado de las tres iteraciones está en [diagrama_componentes_it1_it2_it3.html](./diagrama_componentes_it1_it2_it3.html).

## 8. Iteración 3: gestión de pagos (en curso)

**Incisos del entregable:** 1) requerimientos funcionales y no funcionales de pagos; 2) diagrama de casos de uso en Mermaid (un solo diagrama); 3) historias de usuario; 4) mockups; 5) diagrama de secuencia actualizado con las 3 iteraciones; 6) diagrama de componentes actualizado con las 3 iteraciones; 7) plan de pruebas resumido en Excel. Avance: los incisos 1 a 6 están elaborados en `iteracion_3_EA3(Actividad).md` y sus archivos de apoyo; el inciso 7 sigue pendiente.

**Fuente de los requerimientos:** el texto del profesor (`Requerimientos_gestión_pagos.txt`). Los requerimientos se redactan a partir de ese texto; las decisiones adicionales del estudiante se separan y se identifican como supuestos.

### Reglas de pagos dadas por el profesor

- **Pago por adelantado** al registrar o contratar el servicio (usuarios nuevos). El cliente le dice al operario qué día empieza su mensualidad; no se pregunta la fecha de cierre (si inicia el 5, termina el 4 del mes siguiente).
- **El operario registra el pago.** Medios: efectivo, código QR o recibo bancario que el cliente presenta.
- **Comprobante** para el cliente: fecha del pago, vigencia del pago, fecha de la mensualidad (inicio y fin, que no necesariamente coincide con la del pago), usuario y valor pagado.
- **La mensualidad es fija:** se habilita desde su fecha de inicio, no desde la del pago, y pagar antes de que venza no hace perder días. Se pide una librería de gestión de fechas.
- **Mensualidad vencida sin pago:** el cliente queda con la etiqueta "pago pendiente" y ve un aviso (texto con fondo rojo) cada vez que accede. Si paga después, se acepta, la mensualidad se reactiva desde la fecha original (sin contar los días sin pago) y se retira la etiqueta.
- **Baja a voluntad:** baja lógica (usuario y datos desactivados). Si el cliente vuelve, se reactiva su usuario anterior y solo se actualiza la fecha de nuevo registro.

### Desarrollo de los incisos

Los incisos 1, 2 y 3 (requerimientos, casos de uso e historias de usuario) están desarrollados en `iteracion_3_EA3(Actividad).md`; este documento queda solo como contexto. El código Mermaid del diagrama de casos de uso está dentro de ese documento. Los mockups del inciso 4 se trabajan con PlantUML (Salt), no como imágenes generadas.

### Decisiones y supuestos

- **Se mantiene el cobro por vehículo**, según la regla existente del proyecto. Cada vehículo tiene su propia mensualidad, pago, fecha de vencimiento y estado de pago; el portal muestra al cliente la suma mensual de las tarifas de sus vehículos habilitados.
- Se adopta como supuesto conservar el **día ancla** de inicio para fechas 29–31 en los ciclos ordinarios y en pagos antes de completar la mora. Si un mes no tiene ese día, se usa su último día válido y el periodo anterior cierra el día previo. Por ejemplo, al iniciar el 31 de enero, el siguiente periodo comienza el 28 o 29 de febrero y el primero cierra el 27 o 28; el ancla 31 se conserva para el siguiente cálculo. No hay huecos entre periodos.
- El estado de pago pendiente corresponde al **vehículo**, no al cliente completo. El portal puede mostrar el aviso al cliente indicando qué vehículos están pendientes.
- Siete días antes del vencimiento, el cliente ve la tarifa de la mensualidad siguiente como una opción, sin cobro automático. Puede indicar que desea continuar o solicitar la baja; la solicitud se remite al administrador y el operario registra el pago si el cliente continúa.
- Se asume un **plazo de 15 días calendario** después del vencimiento. El día siguiente cuenta como día 1; desde el día 15 se impiden nuevos ingresos de ese vehículo. Un vehículo que ya está dentro puede salir y no se expulsa. Para reanudar después del bloqueo, si el cliente continúa, se cobra el prorrateo de los primeros 15 días de gracia y una mensualidad completa por adelantado desde la fecha del pago. En el ejemplo de un periodo que vence el 4 de abril y un pago el 20 de abril, el prorrateo cubre del 5 al 19 de abril y la nueva mensualidad va del 20 de abril al 19 de mayo; la fecha del pago reinicia el día ancla. El prorrateo usa la tarifa mensual dividida por los días reales del ciclo y multiplicada por los días cobrables; no se cobra una mensualidad futura automáticamente ni se agregan multas.
- Para un recibo bancario, el operario revisa el documento que presenta el cliente y registra el medio; no se contempla integración ni verificación automática con el banco.
- El administrador puede consultar el estado de pago por vehículo desde la gestión existente de clientes y vehículos; el registro de pagos sigue siendo exclusivo del operario.
- El comprobante incluye los campos pedidos por el profesor y puede incluir otros datos útiles. Se propone incluir la placa para distinguir el vehículo al que corresponde.
- La compatibilidad de los clientes de ejemplo con la nueva lógica de pagos es una consideración técnica del proyecto, no un requisito no funcional solicitado explícitamente por el profesor.
- La **baja** la hace el administrador (es quien inhabilita clientes hoy). La **reactivación** puede hacerla el operario (formulario contextual) o el administrador.
- **Clientes de ejemplo:** `inicializar_datos.py` debe cargarlos con un pago inicial y su mensualidad. Conviene dejar un par con la mensualidad vencida para poder mostrar el aviso de pago pendiente.
- **Reactivación y código actual:** hoy un documento repetido lanza `ClienteYaExiste`; RF-PAG-14 exige reactivar al cliente dado de baja en lugar de fallar. Es un cambio en `ClienteService.registrar_cliente` y su repositorio.
- **Tarifas reales:** la sección de pendientes original las ligaba a esta iteración, pero el profesor no las menciona. Quedan fuera de los requerimientos y siguen constantes (moto 60.000, vehículo 120.000) hasta decidir.

### Dudas abiertas para el profesor

- El texto del profesor no define un aviso de renovación siete días antes ni un prorrateo de mora. Se adoptan como decisiones del proyecto: ofrecer la mensualidad siguiente sin cobrarla automáticamente; permitir al cliente indicar si continúa o solicitar la baja al administrador; y cobrar el prorrateo del periodo de gracia al reactivar el ingreso, además de la siguiente mensualidad adelantada si continúa.
- En el pago atrasado durante los primeros 14 días de mora, el ciclo se mantiene desde su fecha original: si el periodo terminó el 4 de abril y el operario registra el pago el 10, la nueva mensualidad se cuenta del 5 de abril al 4 de mayo. Desde el día 15 se aplica la excepción descrita en SUP-PAG-04: prorrateo del 5 al 19 y nuevo ciclo mensual desde la fecha efectiva del pago, si el cliente continúa.

## 9. Estado y pendientes

**Hecho:** iteración 1; iteración 2 (rol administrativo, gestión de cuentas, restricción del panel operativo, solicitudes de error, administración de celdas y reserva de origen/destino en correcciones); incisos 1 a 6 de la iteración 3, incluidos los diagramas de secuencia y componentes en `iteracion_3_EA3(Actividad).md` y sus archivos de apoyo.

**Pendiente**

- Iteración 3, inciso 7: diligenciar el plan de pruebas resumido de gestión de pagos en Excel.
- La lógica de pagos del código quedó implementada: registros por vehículo, vigencias con librería de fechas, estado de pago, aviso en el portal, baja/reactivación y pagos iniciales para los clientes de ejemplo.
- Subir los cambios de la iteración 2 al repositorio de GitHub.
- Definir el reporte de vehículos registrados y celdas disponibles que mencionó el profesor.
- Revisar contra el código actual las historias, pantallas, pruebas y casos de uso de la iteración 2.
- Los diagramas de clases y paquetes de la iteración 1 no incluyen los componentes nuevos de la iteración 2 ni los de pagos.

## 10. Convenciones de código

- Nombres de clases, funciones y variables en español y `snake_case`; comentarios y docstrings que explican el flujo de cada bloque.
- Una conexión nueva por operación, abierta con `transaccion()`; los repositorios nunca abren conexiones.
- Los errores de negocio son subclases de `ParqueaderoError`; la interfaz los muestra con `ejecutar()`.
- Los estilos están centralizados en `ui/comun.py`; no hay estilos sueltos en las ventanas.
- Cuidado con Qt: un `QComboBox` guarda el valor de un enumerado como texto, así que se guarda `TipoVehiculo.X.value` y se reconvierte con `TipoVehiculo(...)`.

## 11. Cómo se trabaja con el estudiante

- Las actividades se desarrollan por partes (de 3 en 3 incisos); la introducción y las conclusiones del documento se escriben al final.
- Los diagramas se generan como código de Mermaid; los mockups se dibujan con el tema oscuro de la app. El código de Mermaid se entrega en un bloque de texto plano (no con la etiqueta `mermaid`, para que el chat no lo renderice y se pueda copiar) y también como archivo `.mmd`.
- Para cambios de código se indica **en qué archivo y en qué parte modificar**, sin regenerar archivos completos; los archivos nuevos cortos se entregan completos, y si el cambio abarca casi todo un archivo se entrega entero.
- Textos del documento: voz de estudiante-investigador, reflexiva, crítica y directa; oraciones cortas alternadas con otras más largas; sin aperturas vacías ni muletillas de IA (asimismo, cabe destacar, por consiguiente, es importante mencionar, en el vasto panorama de, sin lugar a dudas); negaciones-pivote ("no solo... sino también") solo de forma ocasional; transiciones que salen del argumento; matices y dudas razonables en lugar de certeza absoluta; lenguaje cotidiano y preciso, con ejemplos concretos; subtítulos o viñetas solo cuando aporten orden real; sin inventar datos. Las historias de usuario son breves, pero con el mismo estilo.
- Se prefiere explicar las decisiones con su razón: el estudiante hace preguntas conceptuales y revisa con atención lo que se le entrega.
