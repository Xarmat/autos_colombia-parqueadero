-- Esquema físico de "Autos Colombia" (PostgreSQL) - Iteración 1.
-- Se puede ejecutar varias veces: todo usa IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS propietario (
  id_propietario SERIAL PRIMARY KEY,
  nombre    VARCHAR(100) NOT NULL,
  documento VARCHAR(20)  NOT NULL UNIQUE,
  telefono  VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS vehiculo (
  placa          VARCHAR(10) PRIMARY KEY,
  id_propietario INT NOT NULL REFERENCES propietario,
  tipo   VARCHAR(10) NOT NULL CHECK (tipo IN ('MOTO','VEHICULO')),
  marca  VARCHAR(50) NOT NULL,
  color  VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS celda (
  id_celda SERIAL PRIMARY KEY,
  codigo   VARCHAR(10) NOT NULL UNIQUE,
  tipo     VARCHAR(10) NOT NULL CHECK (tipo IN ('MOTO','VEHICULO'))
);

CREATE TABLE IF NOT EXISTS operario (
  id_operario SERIAL PRIMARY KEY,
  nombre     VARCHAR(100) NOT NULL,
  usuario    VARCHAR(30)  NOT NULL UNIQUE,
  clave_hash VARCHAR(255) NOT NULL,
  turno      VARCHAR(10)  NOT NULL CHECK (turno IN ('DIA','NOCHE')),
  habilitado BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS administrador (
  id_administrador SERIAL PRIMARY KEY,
  nombre           VARCHAR(100) NOT NULL,
  usuario           VARCHAR(30) NOT NULL UNIQUE,
  clave_hash        VARCHAR(255) NOT NULL,
  habilitado        BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS puerta (
  id_puerta SERIAL PRIMARY KEY,
  nombre    VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS movimiento (
  id_movimiento       SERIAL PRIMARY KEY,
  placa               VARCHAR(10) NOT NULL REFERENCES vehiculo,
  id_celda            INT NOT NULL REFERENCES celda,
  fecha_ingreso       TIMESTAMP NOT NULL DEFAULT now(),
  id_puerta_ingreso   INT NOT NULL REFERENCES puerta,
  id_operario_ingreso INT NOT NULL REFERENCES operario,
  fecha_salida        TIMESTAMP,
  id_puerta_salida    INT REFERENCES puerta,
  id_operario_salida  INT REFERENCES operario,
  CHECK (fecha_salida IS NULL OR fecha_salida >= fecha_ingreso)
);

-- Anti-duplicados: una celda y un vehículo solo pueden tener UN movimiento abierto
-- (sin fecha de salida). Es la última barrera si dos puertas chocan al mismo tiempo.
CREATE UNIQUE INDEX IF NOT EXISTS uq_celda_activa    ON movimiento (id_celda) WHERE fecha_salida IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_vehiculo_activo ON movimiento (placa)    WHERE fecha_salida IS NULL;

CREATE TABLE IF NOT EXISTS novedad (
  id_novedad    SERIAL PRIMARY KEY,
  id_movimiento INT NOT NULL REFERENCES movimiento,
  id_operario   INT NOT NULL REFERENCES operario,
  descripcion   TEXT NOT NULL,
  fecha_hora    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS correccion_celda (
  id_correccion       SERIAL PRIMARY KEY,
  id_movimiento       INT NOT NULL REFERENCES movimiento,
  id_celda_anterior   INT NOT NULL REFERENCES celda,
  id_celda_nueva      INT NOT NULL REFERENCES celda,
  id_administrador    INT NOT NULL REFERENCES administrador,
  motivo              TEXT NOT NULL,
  estado              VARCHAR(12) NOT NULL DEFAULT 'PENDIENTE'
                      CHECK (estado IN ('PENDIENTE', 'COMPLETADA')),
  fecha_solicitud     TIMESTAMP NOT NULL DEFAULT now(),
  fecha_completada    TIMESTAMP,
  CHECK (id_celda_anterior <> id_celda_nueva)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_celda_correccion_pendiente
  ON correccion_celda (id_celda_anterior) WHERE estado = 'PENDIENTE';

CREATE TABLE IF NOT EXISTS solicitud_cambio (
  id_solicitud       SERIAL PRIMARY KEY,
  id_operario        INT NOT NULL REFERENCES operario,
  id_movimiento      INT REFERENCES movimiento,
  placa_reportada    VARCHAR(10),
  tipo               VARCHAR(12) NOT NULL CHECK (tipo IN ('ENTRADA', 'SALIDA', 'CELDA', 'OTRA')),
  descripcion        TEXT NOT NULL,
  estado             VARCHAR(12) NOT NULL DEFAULT 'PENDIENTE'
                     CHECK (estado IN ('PENDIENTE', 'RESUELTA', 'RECHAZADA')),
  respuesta          TEXT,
  placa_corregida    VARCHAR(10),
  id_administrador   INT REFERENCES administrador,
  fecha_solicitud    TIMESTAMP NOT NULL DEFAULT now(),
  fecha_resolucion   TIMESTAMP
);

ALTER TABLE solicitud_cambio
  DROP CONSTRAINT IF EXISTS solicitud_cambio_tipo_check;
UPDATE solicitud_cambio SET tipo='ENTRADA' WHERE tipo='PLACA';
ALTER TABLE solicitud_cambio
  ADD CONSTRAINT solicitud_cambio_tipo_check
  CHECK (tipo IN ('ENTRADA', 'SALIDA', 'CELDA', 'OTRA'));

-- Migraciones repetibles para bases creadas en iteraciones anteriores.
ALTER TABLE operario ADD COLUMN IF NOT EXISTS habilitado BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE celda ADD COLUMN IF NOT EXISTS habilitada BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE celda ADD COLUMN IF NOT EXISTS motivo_bloqueo TEXT;

-- Columnas de gestión de clientes y vehículos (Iteración 2)
ALTER TABLE propietario ADD COLUMN IF NOT EXISTS clave_hash VARCHAR(255) DEFAULT '';
ALTER TABLE propietario ADD COLUMN IF NOT EXISTS habilitado BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE propietario ADD COLUMN IF NOT EXISTS fecha_nuevo_registro TIMESTAMP NOT NULL DEFAULT now();
ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS habilitado BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS fecha_habilitacion TIMESTAMP NOT NULL DEFAULT now();

-- Pagos y coberturas por vehículo. Un pago puede incluir el prorrateo y el
-- primer mes de reactivación, por eso los conceptos se guardan por separado.
CREATE TABLE IF NOT EXISTS pago (
  id_pago       SERIAL PRIMARY KEY,
  placa         VARCHAR(10) NOT NULL REFERENCES vehiculo,
  fecha_pago    TIMESTAMP NOT NULL DEFAULT now(),
  medio_pago    VARCHAR(20) NOT NULL
                CHECK (medio_pago IN ('EFECTIVO', 'QR', 'RECIBO_BANCARIO')),
  id_operario   INT NOT NULL REFERENCES operario,
  valor_total   NUMERIC(12, 0) NOT NULL CHECK (valor_total > 0)
);

CREATE TABLE IF NOT EXISTS pago_detalle (
  id_detalle    SERIAL PRIMARY KEY,
  id_pago       INT NOT NULL REFERENCES pago,
  placa         VARCHAR(10) NOT NULL REFERENCES vehiculo,
  concepto      VARCHAR(12) NOT NULL
                CHECK (concepto IN ('MENSUALIDAD', 'PRORRATEO')),
  fecha_inicio  DATE NOT NULL,
  fecha_fin     DATE NOT NULL,
  dia_ancla     SMALLINT,
  fecha_activacion TIMESTAMP NOT NULL DEFAULT now(),
  valor         NUMERIC(12, 0) NOT NULL CHECK (valor > 0),
  CHECK (fecha_fin >= fecha_inicio),
  CHECK ((concepto = 'MENSUALIDAD' AND dia_ancla BETWEEN 1 AND 31)
      OR (concepto = 'PRORRATEO' AND dia_ancla IS NULL))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pago_detalle_periodo
  ON pago_detalle (placa, concepto, fecha_inicio, fecha_fin, fecha_activacion);
CREATE INDEX IF NOT EXISTS ix_pago_detalle_placa_fin
  ON pago_detalle (placa, fecha_fin DESC);

CREATE TABLE IF NOT EXISTS solicitud_cliente (
  id_solicitud       SERIAL PRIMARY KEY,
  id_propietario     INT NOT NULL REFERENCES propietario,
  placa              VARCHAR(10) REFERENCES vehiculo,
  tipo               VARCHAR(12) NOT NULL CHECK (tipo IN ('CONTINUAR', 'BAJA')),
  estado             VARCHAR(12) NOT NULL DEFAULT 'PENDIENTE'
                     CHECK (estado IN ('PENDIENTE', 'ATENDIDA', 'RECHAZADA')),
  id_administrador   INT REFERENCES administrador,
  respuesta          TEXT,
  fecha_solicitud    TIMESTAMP NOT NULL DEFAULT now(),
  fecha_resolucion   TIMESTAMP,
  CHECK ((tipo = 'CONTINUAR' AND placa IS NOT NULL)
      OR (tipo = 'BAJA'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_solicitud_cliente_pendiente
  ON solicitud_cliente (id_propietario, tipo, COALESCE(placa, ''))
  WHERE estado = 'PENDIENTE';
