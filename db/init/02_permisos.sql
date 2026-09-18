-- ============================================
-- PET-CORE — Permisos de la cuenta de aplicación
-- ============================================
--
-- Se ejecuta después de 01_schema.sql.
--
-- La contraseña se obtiene del secreto de Docker montado en
-- /run/secrets/db-password y no queda escrita en el código fuente.
-- ============================================


-- Creación idempotente del rol de aplicación
DO $$
DECLARE
    app_password TEXT;
BEGIN
    app_password :=
        btrim(pg_read_file('/run/secrets/db-password'));

    IF NOT EXISTS (
        SELECT FROM pg_roles
        WHERE rolname = 'petcore_app'
    ) THEN
        EXECUTE format(
            'CREATE ROLE petcore_app LOGIN PASSWORD %L',
            app_password
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE petcore_app LOGIN PASSWORD %L',
            app_password
        );
    END IF;
END
$$;


GRANT USAGE ON SCHEMA public TO petcore_app;

GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public
    TO petcore_app;

GRANT USAGE ON ALL SEQUENCES IN SCHEMA public
    TO petcore_app;



-- ============================================
-- INMUTABILIDAD DE LOS REGISTROS DE AUDITORÍA
-- ============================================
--
-- Los registros de auditoría solo admiten inserción y lectura.
-- Ninguna funcionalidad del sistema puede modificarlos ni eliminarlos,
-- porque la cuenta con la que se conecta la aplicación carece del permiso.
-- El propietario del esquema conserva la capacidad de hacer mantenimiento.

REVOKE UPDATE, DELETE
    ON acceso_historial, auditoria_sistema
    FROM petcore_app;

REVOKE DELETE
    ON consulta_clinica, registro_peso
    FROM petcore_app;


-- ============================================
-- VERIFICACIÓN
-- ============================================
-- Debe devolver solo INSERT y SELECT para ambas tablas:
--
--   SELECT table_name, privilege_type
--     FROM information_schema.table_privileges
--    WHERE grantee = 'petcore_app'
--      AND table_name IN ('acceso_historial', 'auditoria_sistema')
--    ORDER BY table_name, privilege_type;
