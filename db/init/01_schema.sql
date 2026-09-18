-- ============================================
-- PET-CORE — Esquema de base de datos
-- Sistema de gestión para clínica veterinaria
-- ============================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS btree_gist;


-- ============================================
-- USUARIOS
-- ============================================

CREATE TABLE usuario (
    id_usuario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    documento VARCHAR(30) NOT NULL UNIQUE,
    correo VARCHAR(254) NOT NULL UNIQUE,
    telefono VARCHAR(30) NOT NULL,
    contrasena_hash TEXT NOT NULL,

    estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVO'
        CHECK (estado IN ('ACTIVO', 'INACTIVO')),

    -- El umbral de bloqueo lo define la aplicación (ver RNF-02).
    -- El esquema solo garantiza que el contador no sea negativo.
    intentos_inicio INTEGER NOT NULL DEFAULT 0
        CHECK (intentos_inicio >= 0),

    bloqueado_hasta TIMESTAMP WITH TIME ZONE
);


-- ============================================
-- ROLES DE USUARIO (especialización)
-- ============================================

CREATE TABLE cliente (
    id_usuario BIGINT PRIMARY KEY,

    FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
);


CREATE TABLE veterinario (
    id_usuario BIGINT PRIMARY KEY,

    matricula_profesional VARCHAR(50) NOT NULL UNIQUE,

    FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
);


CREATE TABLE administrador (
    id_usuario BIGINT PRIMARY KEY,

    FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
);


-- ============================================
-- ESPECIES (catálogo)
-- ============================================

CREATE TABLE especie (
    id_especie BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL UNIQUE,

    estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVO'
        CHECK (estado IN ('ACTIVO', 'INACTIVO'))
);


-- ============================================
-- MASCOTAS
-- ============================================

CREATE TABLE mascota (
    id_mascota BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_cliente BIGINT NOT NULL,

    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(100) NOT NULL,
    raza VARCHAR(100),
    fecha_nacimiento DATE,
    sexo VARCHAR(20)
        CHECK (sexo IN ('MACHO', 'HEMBRA', 'DESCONOCIDO')),
    observaciones TEXT,

    -- Baja lógica: la mascota nunca se elimina si tiene historial
    estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'INACTIVA')),

    FOREIGN KEY (id_cliente)
        REFERENCES cliente(id_usuario)
);


-- ============================================
-- REGISTROS DE PESO (entidad débil)
-- ============================================

CREATE TABLE registro_peso (
    id_mascota BIGINT NOT NULL,

    fecha_registro TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    peso NUMERIC(6,2) NOT NULL,

    PRIMARY KEY (id_mascota, fecha_registro),

    FOREIGN KEY (id_mascota)
        REFERENCES mascota(id_mascota),

    CHECK (peso > 0)
);


-- ============================================
-- DISPONIBILIDAD DE VETERINARIOS
-- ============================================

CREATE TABLE disponibilidad (
    id_disponibilidad BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_veterinario BIGINT NOT NULL,

    -- 1 lunes, 2 martes, ... 7 domingo
    dia_semana SMALLINT NOT NULL
        CHECK (dia_semana BETWEEN 1 AND 7),

    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,

    estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'INACTIVA')),

    FOREIGN KEY (id_veterinario)
        REFERENCES veterinario(id_usuario),

    CHECK (hora_fin > hora_inicio),

    -- Las franjas comienzan y terminan en múltiplos de 15 minutos
    CHECK (
        MOD(EXTRACT(MINUTE FROM hora_inicio), 15) = 0
        AND EXTRACT(SECOND FROM hora_inicio) = 0
        AND MOD(EXTRACT(MINUTE FROM hora_fin), 15) = 0
        AND EXTRACT(SECOND FROM hora_fin) = 0
    ),

    UNIQUE (id_veterinario, dia_semana, hora_inicio, hora_fin)
);


-- ============================================
-- TIPOS DE ATENCIÓN
-- ============================================

CREATE TABLE tipo_atencion (
    id_tipo_atencion BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,

    duracion_minutos INTEGER NOT NULL,

    -- Los tipos no reservables solo puede agendarlos el administrador
    reservable_cliente BOOLEAN NOT NULL DEFAULT TRUE,

    estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVO'
        CHECK (estado IN ('ACTIVO', 'INACTIVO')),

    CHECK (duracion_minutos > 0 AND duracion_minutos % 15 = 0)
);


-- ============================================
-- TURNOS
-- ============================================

CREATE TABLE turno (
    id_turno BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_mascota BIGINT NOT NULL,
    id_veterinario BIGINT NOT NULL,
    id_tipo_atencion BIGINT NOT NULL,

    -- Quién creó el turno y quién lo modificó por última vez.
    id_usuario_creador BIGINT NOT NULL,
    id_usuario_modificador BIGINT,
    fecha_modificacion TIMESTAMP WITH TIME ZONE,

    fecha_hora_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_hora_fin TIMESTAMP WITH TIME ZONE NOT NULL,

    duracion_minutos INTEGER NOT NULL,

    periodo tstzrange GENERATED ALWAYS AS (
        tstzrange(
            fecha_hora_inicio,
            fecha_hora_fin,
            '[)'
        )
    ) STORED,

    estado VARCHAR(20) NOT NULL DEFAULT 'CONFIRMADO'
        CHECK (estado IN ('CONFIRMADO', 'CANCELADO', 'ATENDIDO', 'NO_ASISTIO')),

    canal_origen VARCHAR(20) NOT NULL
        CHECK (canal_origen IN ('AUTOGESTION', 'TELEFONO', 'PRESENCIAL')),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_mascota)
        REFERENCES mascota(id_mascota),

    FOREIGN KEY (id_veterinario)
        REFERENCES veterinario(id_usuario),

    FOREIGN KEY (id_tipo_atencion)
        REFERENCES tipo_atencion(id_tipo_atencion),

    FOREIGN KEY (id_usuario_creador)
        REFERENCES usuario(id_usuario),

    FOREIGN KEY (id_usuario_modificador)
        REFERENCES usuario(id_usuario),

    CHECK (duracion_minutos > 0 AND duracion_minutos % 15 = 0),
    CHECK (
            fecha_hora_fin =
            fecha_hora_inicio + make_interval(mins => duracion_minutos)
        ),

    -- Los turnos comienzan en múltiplos de 15 minutos
    CHECK (
        MOD(EXTRACT(MINUTE FROM fecha_hora_inicio), 15) = 0
        AND EXTRACT(SECOND FROM fecha_hora_inicio) = 0
    ),

    -- No pueden existir dos turnos superpuestos en la agenda de un mismo
    -- veterinario, cualquiera sea el canal de origen. Los turnos cancelados
    -- y no asistidos liberan el horario.
    CONSTRAINT no_superposicion EXCLUDE USING gist (
        id_veterinario WITH =,
        periodo WITH &&
    ) WHERE (estado IN ('CONFIRMADO', 'ATENDIDO'))
);


-- ============================================
-- CONSULTAS CLÍNICAS
-- ============================================

CREATE TABLE consulta_clinica (
    id_consulta BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_turno BIGINT NOT NULL,
    id_mascota BIGINT NOT NULL,
    id_veterinario BIGINT NOT NULL,

    -- Si no es nulo, esta entrada corrige a una consulta anterior.
    -- La restricción de un único nivel de corrección (una corrección no
    -- puede corregir a otra corrección) se valida en la aplicación.
    id_consulta_original BIGINT,

    fecha_registro TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    motivo TEXT NOT NULL,
    observaciones TEXT,
    diagnostico TEXT NOT NULL,
    tratamiento TEXT,
    recomendaciones TEXT,

    -- Si no es nula, la consulta fue modificada dentro de su ventana de 24 h
    fecha_modificacion TIMESTAMP WITH TIME ZONE,

    FOREIGN KEY (id_turno)
        REFERENCES turno(id_turno),

    FOREIGN KEY (id_mascota)
        REFERENCES mascota(id_mascota),

    FOREIGN KEY (id_veterinario)
        REFERENCES veterinario(id_usuario),

    FOREIGN KEY (id_consulta_original)
        REFERENCES consulta_clinica(id_consulta),

    CHECK (length(trim(motivo)) > 0),

    CHECK (
        id_consulta_original IS NULL
        OR id_consulta_original <> id_consulta
    )
);

-- Un turno origina como máximo una consulta original.
-- Las correcciones no cuentan para este límite.
CREATE UNIQUE INDEX uq_consulta_original_por_turno
    ON consulta_clinica(id_turno)
    WHERE id_consulta_original IS NULL;


-- ============================================
-- ACCESOS AL HISTORIAL CLÍNICO
-- ============================================

CREATE TABLE acceso_historial (
    id_acceso BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_usuario BIGINT NOT NULL,
    id_mascota BIGINT NOT NULL,

    fecha_hora TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Se guarda como texto para incorporar nuevos roles sin cambiar el esquema.
    rol_utilizado VARCHAR(20) NOT NULL,

    operacion VARCHAR(20) NOT NULL
        CHECK (operacion IN ('LECTURA', 'CREACION', 'MODIFICACION')),

    resultado VARCHAR(15) NOT NULL
        CHECK (resultado IN ('PERMITIDO', 'RECHAZADO')),

    motivo_rechazo TEXT,

    FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario),

    FOREIGN KEY (id_mascota)
        REFERENCES mascota(id_mascota)
);


-- ============================================
-- NOTIFICACIONES
-- ============================================

CREATE TABLE notificacion (
    id_notificacion BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_cliente BIGINT NOT NULL,

    id_turno BIGINT,
    id_consulta BIGINT,

    tipo VARCHAR(30) NOT NULL
        CHECK (tipo IN (
            'RECORDATORIO_TURNO',
            'MODIFICACION_CONSULTA',
            'CORRECCION_CONSULTA'
        )),

    -- Se guarda como texto para agregar canales sin cambiar el esquema.
    canal VARCHAR(30) NOT NULL,

    fecha_programada TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_envio TIMESTAMP WITH TIME ZONE,

    estado VARCHAR(15) NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'ENVIADA', 'FALLIDA')),

    detalle_error TEXT,

    FOREIGN KEY (id_cliente)
        REFERENCES cliente(id_usuario),

    FOREIGN KEY (id_turno)
        REFERENCES turno(id_turno),

    FOREIGN KEY (id_consulta)
        REFERENCES consulta_clinica(id_consulta),

    -- Una notificación refiere a un turno o a una consulta, nunca a ambos
    CHECK (
        (id_turno IS NOT NULL AND id_consulta IS NULL)
        OR
        (id_turno IS NULL AND id_consulta IS NOT NULL)
    )
);

-- Un turno recibe un solo recordatorio aunque el proceso se ejecute varias veces.
CREATE UNIQUE INDEX uq_notificacion_turno
    ON notificacion(id_turno, tipo)
    WHERE id_turno IS NOT NULL;


-- ============================================
-- AUDITORÍA GENERAL DEL SISTEMA
-- ============================================

CREATE TABLE auditoria_sistema (
    id_auditoria BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Nulo si se intentó iniciar sesión con un correo inexistente
    id_usuario_actor BIGINT,

    correo_ingresado VARCHAR(254),

    -- Usuario sobre el que se ejecutó la acción, cuando aplica
    id_usuario_afectado BIGINT,

    accion VARCHAR(50) NOT NULL,

    resultado VARCHAR(15) NOT NULL
        CHECK (resultado IN ('EXITOSO', 'FALLIDO', 'BLOQUEADO', 'RECHAZADO')),

    fecha_hora TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    detalle TEXT,

    FOREIGN KEY (id_usuario_actor)
        REFERENCES usuario(id_usuario),

    FOREIGN KEY (id_usuario_afectado)
        REFERENCES usuario(id_usuario)
);


-- ============================================
-- ÍNDICES DE APOYO
-- ============================================

-- Cálculo de disponibilidad y agenda del veterinario
CREATE INDEX ix_turno_vet_fecha
    ON turno(id_veterinario, fecha_hora_inicio)
    WHERE estado IN ('CONFIRMADO', 'ATENDIDO');

-- Historial clínico de una mascota, ordenado de más reciente a más antiguo
CREATE INDEX ix_consulta_mascota
    ON consulta_clinica(id_mascota, fecha_registro DESC);

-- Correcciones asociadas a una consulta
CREATE INDEX ix_consulta_original
    ON consulta_clinica(id_consulta_original)
    WHERE id_consulta_original IS NOT NULL;

-- Consulta del registro de accesos, por mascota y por usuario
CREATE INDEX ix_acceso_mascota
    ON acceso_historial(id_mascota, fecha_hora DESC);

CREATE INDEX ix_acceso_usuario
    ON acceso_historial(id_usuario, fecha_hora DESC);

-- Notificaciones pendientes de envío
CREATE INDEX ix_notificacion_pendiente
    ON notificacion(fecha_programada)
    WHERE estado = 'PENDIENTE';

COMMIT;
