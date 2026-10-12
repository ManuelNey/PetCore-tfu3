# Pet-Core — TFU4: Patrones de arquitectura

Este documento reúne, funcionalidad por funcionalidad, **qué patrón de arquitectura se implementó, cómo se
hizo y cómo probarlo**. Cada funcionalidad tiene su propia sección.

Los diagramas UML y la explicación formal de cada patrón van en documentos aparte.

## Índice general

| Funcionalidad | Patrones |
| --- | --- |
| [Exportación del historial a PDF](#exportación-del-historial-a-pdf-asynchronous-request-reply--valet-key) | Asynchronous Request-Reply (rendimiento) y Valet Key (seguridad) |

> Las demás funcionalidades se agregan acá como nuevas secciones (`##`) y una fila más en la tabla de arriba.

---

## Exportación del historial a PDF (Asynchronous Request-Reply + Valet Key)

El veterinario pide el historial clínico de una mascota en PDF. Como generarlo puede tardar, la API **no lo
hace esperar**: le responde enseguida y arma el PDF por detrás. Cuando está listo, le da un **enlace
temporal** que sirve para descargar ese PDF, aunque quien lo abra no tenga cuenta.

- **Asynchronous Request-Reply** (rendimiento): responder rápido y trabajar por detrás.
- **Valet Key** (seguridad): un enlace que sirve solo para un archivo y solo por un rato.

### Contenido de esta sección

1. [Cómo funciona](#1-cómo-funciona)
2. [Cómo se hizo](#2-cómo-se-hizo)
3. [Cómo probarlo](#3-cómo-probarlo)
4. [Variables de configuración](#4-variables-de-configuración)
5. [Limitaciones](#5-limitaciones)

### 1. Cómo funciona

1. El veterinario hace `POST /historial/{id_mascota}/exportar`.
2. La API crea una **tarea** con estado `PENDIENTE` y responde enseguida **202 Accepted** con el `id_tarea`.
3. Por detrás, la API genera el PDF. Cuando termina, la tarea pasa a `LISTO` (o a `ERROR` si algo falló).
4. Mientras tanto, el veterinario consulta `GET /historial/exportar/{id_tarea}` cada tanto para ver el estado.
5. Cuando está `LISTO`, esa respuesta trae un `enlace_descarga` con un token temporal (el **Valet Key**).
6. Quien tenga el enlace abre `GET /historial/exportar/{id_tarea}/descargar?token=...` y recibe el PDF.
   No hace falta iniciar sesión.

| Endpoint | Quién lo usa | Qué hace |
| --- | --- | --- |
| `POST /historial/{id_mascota}/exportar` | Veterinario (con login) | Crea la tarea y responde 202. |
| `GET /historial/exportar/{id_tarea}` | Veterinario (con login) | Dice si está `PENDIENTE`, `LISTO` o `ERROR`. Si está `LISTO`, trae el enlace. |
| `GET /historial/exportar/{id_tarea}/descargar?token=...` | Cualquiera con el enlace | Entrega el PDF si el token sirve. |

### 2. Cómo se hizo

1. **Una tabla para las tareas** (`db/init/05_tarea_exportacion.sql`): guarda el estado de cada exportación.
   Está en la base de datos (y no en la memoria de la API) porque la API corre en dos copias a la vez: así
   cualquiera de las dos puede responder el estado de una tarea que empezó la otra.
2. **Generar el PDF** (`app/historial/pdf.py`): arma el documento con los datos del historial de la mascota,
   que ya existían en el proyecto.
3. **Los endpoints** (`app/historial/controller.py`): el `POST` crea la tarea y deja el PDF para después. El `GET` de
   estado lee la tarea de la tabla.
4. **El trabajo por detrás** (`app/historial/exportacion_service.py`): la función
   `generar_en_segundo_plano` genera el PDF, lo guarda en una carpeta y marca la tarea como `LISTO` o `ERROR`.
5. **El Valet Key** (`app/historial/valet_key.py`): es un código (*token*) firmado, parecido al del login, que
   dice para qué archivo sirve y cuándo vence. Se crea cuando la tarea está `LISTO`.
6. **La descarga**: el endpoint `/descargar` no pide el login. Solo revisa el token: que no esté
   modificado, que no haya vencido y que sea de **esa** tarea. Si no, responde `401` o `403`.
7. **Probarlo** (`postman/Exportacion_ValetKey_Collection.json`): una colección de Postman con las pruebas.

### 3. Cómo probarlo

#### 3.1 Levantar la aplicación

Con Docker Desktop abierto, en PowerShell, dentro de la carpeta del proyecto (si no tenés
`db/password.txt` y `db/jwt-secret.txt`, seguí *Preparación local* del `README.md`):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

Para probar también que el enlace **vence**, definí antes una duración corta (10 segundos) y volvé a levantar:

```powershell
$env:VALET_KEY_SEGUNDOS = 10
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

Cuando termines, volvé a la duración normal (10 minutos):

```powershell
Remove-Item Env:VALET_KEY_SEGUNDOS
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

#### 3.2 Comprobar que existe la tabla nueva

Postgres solo crea las tablas de `db/init` cuando la base es nueva. Si tu base ya existía, puede faltar la
tabla `tarea_exportacion`. Para saberlo:

```powershell
docker exec postgres-dev psql -U postgres -d postgres -tA -c "SELECT to_regclass('public.tarea_exportacion')"
```

- Si imprime `tarea_exportacion`: **ya la tenés**, seguí con el paso 3.3.
- Si imprime una línea vacía: **no la tenés**. Creala con:

```powershell
Get-Content .\db\init\05_tarea_exportacion.sql -Raw | docker exec -i postgres-dev psql -U postgres -d postgres
```

Debe imprimir `BEGIN`, `CREATE TABLE`, `GRANT` y `COMMIT`. Si la tabla ya existía, avisa
`already exists, skipping` y termina igual en `COMMIT`: no pasa nada. Lo que sí es un problema es un `ERROR`.

#### 3.3 Probar con Postman

1. Importá `postman/Exportacion_ValetKey_Collection.json`.
2. Abrí la colección y apretá **Run collection**.
3. Los scripts guardan solos el login, el `id_tarea` y el token: no hay que copiar nada.

Qué prueba cada request y qué debe dar:

| Request | Qué hace | Debe dar |
| --- | --- | --- |
| A0 | Inicia sesión como veterinario | 200 |
| A1 | Pide la exportación | **202**, estado `PENDIENTE`, y rápido |
| A2 | Hace otra consulta mientras se genera el PDF | 200 (la API sigue funcionando) |
| A3 | Consulta el estado (se repite sola) | `PENDIENTE` y después `LISTO` con el enlace |
| B1 | Descarga el PDF con el enlace, **sin login** | 200 y un PDF |
| B2 | Crea una segunda exportación (tarea B) | 202 |
| B3 | Usa el token de la tarea A en la tarea B | 403 |
| B4 | Usa un token modificado | 401 |
| B5 | Espera 11 segundos y usa el enlace vencido | 401 (solo si usaste `VALET_KEY_SEGUNDOS = 10`) |

Con la duración normal (10 minutos), B5 da 200 en vez de 401: es lo esperado, no es un error.

> A2 usa `GET /demo/instancia` y no `GET /mascotas`, porque el rol veterinario no puede usar `/mascotas`.

#### Problemas comunes

- **El login da error 500:** la API no puede conectarse a la base. Pasa si `db/password.txt` no es la contraseña
  con la que se creó la base. Poné en `db/password.txt` la contraseña original y volvé a levantar.
- **"El enlace de descarga venció":** si levantaste con `VALET_KEY_SEGUNDOS = 10`, el enlace dura solo 10
  segundos. Pedí el estado otra vez para recibir un enlace nuevo y abrilo enseguida (o volvé a la duración normal).

### 4. Variables de configuración

Están en `compose.yaml`, dentro del servicio `server`.

| Variable | Valor | Para qué sirve |
| --- | --- | --- |
| `EXPORTACIONES_DIR` | `/app/exportaciones` | Carpeta donde se guardan los PDF. |
| `EXPORTACION_RETARDO_SEGUNDOS` | `5` | Pausa **artificial** antes de generar el PDF, solo para poder ver el estado `PENDIENTE` en la demo. En un uso real debe ser `0`. |
| `VALET_KEY_SEGUNDOS` | `600` | Cuántos segundos dura el enlace (600 = 10 minutos). |

### 5. Limitaciones

- **Las tareas pendientes no se guardan:** si la API se reinicia justo mientras prepara un PDF, esa tarea queda
  `PENDIENTE` para siempre. Para algo más serio habría que usar una cola de trabajos.
- **El token va dentro del enlace:** puede quedar anotado en los registros del servidor. Hay que tratar el
  enlace como una contraseña temporal.
- **El enlace se puede usar varias veces** mientras no venza. Por eso conviene que dure poco.
