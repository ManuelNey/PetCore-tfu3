-- ============================================
-- PET-CORE — Excepciones de disponibilidad por fecha
-- ============================================
--
-- Migración que agrega ausencias puntuales de veterinarios.
--
-- La tabla `disponibilidad` modela franjas recurrentes por día de la
-- semana y no permite registrar que un veterinario falte en una fecha
-- concreta sin alterar todos los días equivalentes futuros. Esta tabla
-- cubre ese caso: cada fila representa una excepción para una fecha
-- puntual, que se interpreta como resta sobre la disponibilidad
-- recurrente (la aplicación es responsable de aplicar esa resta).
--
-- Se ejecuta después de 01_schema.sql. No modifica el esquema existente.
-- ============================================

BEGIN;

-- La extensión btree_gist ya se crea en 01_schema.sql; se repite de forma
-- idempotente para que esta migración pueda aplicarse de manera aislada.
CREATE EXTENSION IF NOT EXISTS btree_gist;


CREATE TABLE excepcion_disponibilidad (
    id_excepcion BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_veterinario BIGINT NOT NULL,

    -- Fecha puntual afectada por la excepción.
    fecha DATE NOT NULL,

    -- Horas nullables con semántica de "todo o nada":
    --   * ambas NULL  -> ausencia de día completo.
    --   * ambas con valor -> ausencia parcial en la franja [hora_inicio, hora_fin).
    -- Nunca se admite una sola de las dos (ver CHECK horas_completas).
    hora_inicio TIME,
    hora_fin TIME,

    -- Motivo opcional (vacaciones, licencia médica, congreso, etc.).
    motivo VARCHAR(100),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Rango temporal derivado que se usa para detectar solapamientos.
    -- La ausencia de día completo ocupa toda la jornada [00:00, 24:00) de la
    -- fecha, de modo que solapa (&&) con cualquier otra excepción de ese día,
    -- sea parcial o de día completo. La ausencia parcial ocupa solo su franja.
    -- Se materializa (STORED) para poder indexarla con GiST.
    periodo tsrange GENERATED ALWAYS AS (
        CASE
            WHEN hora_inicio IS NULL THEN
                tsrange(fecha::timestamp, (fecha + 1)::timestamp, '[)')
            ELSE
                tsrange(fecha + hora_inicio, fecha + hora_fin, '[)')
        END
    ) STORED,

    FOREIGN KEY (id_veterinario)
        REFERENCES veterinario(id_usuario),

    -- Las dos horas van juntas: ambas nulas (día completo) o ambas presentes.
    CONSTRAINT horas_completas CHECK (
        (hora_inicio IS NULL AND hora_fin IS NULL)
        OR
        (hora_inicio IS NOT NULL AND hora_fin IS NOT NULL)
    ),

    -- En una excepción parcial el fin debe ser posterior al inicio.
    -- Cuando ambas son NULL la comparación da NULL y el CHECK se satisface.
    CHECK (hora_fin > hora_inicio),

    -- Las franjas comienzan y terminan en múltiplos de 15 minutos, igual que
    -- `disponibilidad` y `turno`. Con horas NULL el MOD da NULL y el CHECK pasa.
    CHECK (
        MOD(EXTRACT(MINUTE FROM hora_inicio), 15) = 0
        AND EXTRACT(SECOND FROM hora_inicio) = 0
        AND MOD(EXTRACT(MINUTE FROM hora_fin), 15) = 0
        AND EXTRACT(SECOND FROM hora_fin) = 0
    )
    -- El CHECK anterior es NULL (y por lo tanto se satisface) en la ausencia
    -- de día completo; solo restringe a las excepciones parciales.
    ,

    -- No puede haber dos excepciones solapadas del mismo veterinario en la
    -- misma fecha. Sigue el patrón de `no_superposicion` de la tabla `turno`:
    -- igualdad en el veterinario y solapamiento de rangos temporales. Como el
    -- rango de una ausencia de día completo abarca toda la jornada, esta
    -- restricción también impide agregar cualquier otra excepción en un día
    -- que ya tiene registrada una ausencia total (y viceversa).
    CONSTRAINT no_superposicion_excepcion EXCLUDE USING gist (
        id_veterinario WITH =,
        periodo WITH &&
    )
);


-- Búsqueda de las excepciones de un veterinario en una fecha o rango de fechas.
CREATE INDEX ix_excepcion_vet_fecha
    ON excepcion_disponibilidad(id_veterinario, fecha);


-- El GRANT sobre ALL TABLES de 02_permisos.sql se ejecuta antes que esta
-- migración, por lo que la cuenta de la aplicación no cubre esta tabla nueva.
-- La columna id_excepcion es IDENTITY, así que el INSERT alcanza y no hace
-- falta otorgar USAGE sobre ninguna secuencia.
GRANT SELECT, INSERT, UPDATE, DELETE
    ON excepcion_disponibilidad
    TO petcore_app;

COMMIT;


-- ============================================
-- PRUEBAS (dejar comentadas)
-- ============================================
-- Reemplazar 1 por el id_usuario de un veterinario existente antes de ejecutar.
-- Cada bloque se puede correr por separado; los que deben fallar indican el
-- error esperado.
--
-- -- 1) Ausencia de día completo (ambas horas NULL) -> debe INSERTAR.
-- INSERT INTO excepcion_disponibilidad (id_veterinario, fecha, motivo)
-- VALUES (1, DATE '2026-09-01', 'Licencia médica');
--
-- -- 2) Ausencia parcial en OTRA fecha -> debe INSERTAR.
-- INSERT INTO excepcion_disponibilidad
--     (id_veterinario, fecha, hora_inicio, hora_fin, motivo)
-- VALUES (1, DATE '2026-09-02', TIME '09:00', TIME '12:00', 'Turno médico');
--
-- -- 3) Segunda parcial que solapa con la del 2026-09-02 -> debe FALLAR
-- --    con "conflicting key value violates exclusion constraint
-- --    no_superposicion_excepcion".
-- INSERT INTO excepcion_disponibilidad
--     (id_veterinario, fecha, hora_inicio, hora_fin)
-- VALUES (1, DATE '2026-09-02', TIME '11:00', TIME '13:00');
--
-- -- 4) Parcial en un día que ya tiene ausencia de día completo (2026-09-01)
-- --    -> debe FALLAR por la misma restricción de exclusión, porque el rango
-- --    del día completo abarca toda la jornada.
-- INSERT INTO excepcion_disponibilidad
--     (id_veterinario, fecha, hora_inicio, hora_fin)
-- VALUES (1, DATE '2026-09-01', TIME '15:00', TIME '16:00');
--
-- -- Extra) Horas no múltiplo de 15 -> debe FALLAR por el CHECK de múltiplos.
-- INSERT INTO excepcion_disponibilidad
--     (id_veterinario, fecha, hora_inicio, hora_fin)
-- VALUES (1, DATE '2026-09-03', TIME '09:10', TIME '10:00');
--
-- -- Extra) Una sola hora presente -> debe FALLAR por el CHECK horas_completas.
-- INSERT INTO excepcion_disponibilidad
--     (id_veterinario, fecha, hora_inicio)
-- VALUES (1, DATE '2026-09-04', TIME '09:00');
--
-- -- Limpieza de las pruebas:
-- -- DELETE FROM excepcion_disponibilidad WHERE id_veterinario = 1;
