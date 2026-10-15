-- ============================================
-- PET-CORE — Tareas de exportación del historial a PDF
-- ============================================
--
-- Guarda el estado de cada exportación (Asynchronous Request-Reply):
--   PENDIENTE -> se está generando el PDF
--   LISTO     -> el PDF ya se generó (archivo = nombre del PDF)
--   ERROR     -> falló (detalle_error = qué pasó)
--
-- Se guarda en la base de datos (y no en la memoria de la API) porque la API
-- corre en dos copias: así cualquiera puede responder el estado de una tarea
-- que empezó la otra.
--
-- Se puede ejecutar más de una vez sin problemas.
-- ============================================

BEGIN;

CREATE TABLE IF NOT EXISTS tarea_exportacion (
    id_tarea UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    id_mascota BIGINT NOT NULL REFERENCES mascota(id_mascota),
    id_usuario BIGINT NOT NULL REFERENCES usuario(id_usuario),

    estado VARCHAR(10) NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'LISTO', 'ERROR')),

    archivo VARCHAR(255),
    detalle_error TEXT,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- La API necesita permiso para usar esta tabla nueva.
GRANT SELECT, INSERT, UPDATE
    ON tarea_exportacion
    TO petcore_app;

COMMIT;


-- ============================================
-- Si tu base ya existía, Postgres no ejecuta este archivo solo.
-- Para crear la tabla a mano:
--
--   Get-Content .\db\init\05_tarea_exportacion.sql -Raw | docker exec -i postgres-dev psql -U postgres -d postgres
-- ============================================
