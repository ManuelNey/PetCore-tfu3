BEGIN;

CREATE TABLE IF NOT EXISTS configuracion (
    clave VARCHAR(100) PRIMARY KEY,
    valor VARCHAR(255) NOT NULL,
    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_usuario_modificador BIGINT REFERENCES usuario(id_usuario)
);

INSERT INTO configuracion (clave, valor)
VALUES
    ('LOGIN_MAX_INTENTOS', '5'),
    ('LOGIN_BLOQUEO_MINUTOS', '15')
ON CONFLICT (clave) DO NOTHING;

GRANT SELECT, INSERT, UPDATE
    ON configuracion
    TO petcore_app;

COMMIT;