# Pet-Core — TFU4: Patrones de arquitectura

Este documento reúne, funcionalidad por funcionalidad, **qué patrón de arquitectura se implementó, cómo se
hizo y cómo probarlo**. Cada funcionalidad tiene su propia sección.

Los diagramas UML y la explicación formal de cada patrón van en documentos aparte.

## Índice general

| Funcionalidad | Patrones |
| --- | --- |
| [Reintentos y monitoreo de salud](#reintentos-y-monitoreo-de-salud-retry--health-endpoint-monitoring) | Retry y Health Endpoint Monitoring (disponibilidad) |
| [Cache en listados de referencia](#cache-en-listados-de-referencia-cache-aside) | Cache-Aside (rendimiento) |
| [Exportación del historial a PDF](#exportación-del-historial-a-pdf-asynchronous-request-reply--valet-key) | Asynchronous Request-Reply (rendimiento) y Valet Key (seguridad) |
| [Gateway en Nginx](#gateway-en-nginx-gateway-offloading) | Gateway Offloading (seguridad) |
| [Configuración externa del login](#configuración-externa-del-login-external-configuration-store) | External Configuration Store (modificabilidad) |

---

## Reintentos y monitoreo de salud (Retry + Health Endpoint Monitoring)

Si una conexión falla por algo transitorio (una réplica que se reinicia, Postgres que tarda un instante en
responder), la API no tira el error directo al usuario: reintenta. Y por separado, cada réplica expone un
`/health` que dice si de verdad puede atender pedidos (no solo si el proceso está vivo), para que Docker la
aparte del tráfico si no puede.

- **Retry** (disponibilidad): reintentar antes de fallar.
- **Health Endpoint Monitoring** (disponibilidad): detectar una réplica rota antes de que falle una request real.

### Contenido de esta sección

1. [Cómo funciona](#1-cómo-funciona)
2. [Cómo se hizo](#2-cómo-se-hizo)
3. [Cómo probarlo](#3-cómo-probarlo)
4. [Limitaciones](#4-limitaciones)

### 1. Cómo funciona

**Retry, a dos niveles:**

1. **Nginx** (`nginx/andis.conf`): si una réplica de `server` falla o responde 502/503/504, Nginx reintenta
   contra la otra réplica (`proxy_next_upstream`), sin que el cliente lo note.
2. **Conexión a la base** (`app/database.py`): `abrir_sesion_con_reintentos()` intenta conectarse hasta 3 veces,
   esperando cada vez más entre intentos (*backoff* exponencial: 0.5s, 1s). Si los 3 fallan, recién ahí se
   propaga el error.

**Health Endpoint Monitoring:**

1. `GET /health` abre su propia conexión a Postgres y hace un `SELECT 1`. Si falla, responde **503**; si
   funciona, responde **200**.
2. El servicio `server` en `compose.yaml` tiene un `healthcheck` que llama a `/health` cada 10 segundos. Si
   falla 3 veces seguidas, Docker marca esa réplica como `unhealthy`.

| Endpoint | Quién lo usa | Qué hace |
| --- | --- | --- |
| `GET /health` | Docker (healthcheck) o cualquiera | Chequea la conexión real a la base. 200 u 503. |
| `POST /debug/simular-falla-conexion?veces=N` | Cualquier usuario logueado | Fuerza que las próximas N conexiones fallen, para poder ver el Retry en acción. |
| `GET /debug/ultimo-intento-conexion` | Cualquier usuario logueado | Cuántos intentos usó la última conexión y si funcionó. |

### 2. Cómo se hizo

1. **El Retry de Nginx** está en `nginx/andis.conf`
   (`proxy_next_upstream error timeout http_502 http_504;`). No incluye `http_503` a propósito:
   `/health` devuelve 503 cuando esa réplica no puede hablar con Postgres, y como las dos réplicas comparten
   la misma base, reintentar un 503 contra la otra no sirve de nada y solo duplica la espera.
2. **El Retry de conexión** (`app/database.py`, función `abrir_sesion_con_reintentos`) captura tanto
   `psycopg.OperationalError` como `sqlalchemy.exc.OperationalError`: ante una caída real de la base,
   SQLAlchemy envuelve el error del driver en su propia clase, así que hace falta cubrir las dos.
3. **El `/health` real** (`app/main.py`) abre su propia conexión (`with Session(engine) as session:
   session.execute(text("SELECT 1"))`) y responde 503 si falla. No reutiliza `get_session()` (que sí reintenta
   con backoff) a propósito: un health check tiene que fallar rápido, no demorarse varios segundos
   reintentando y arriesgar el timeout del propio healthcheck.
4. **El healthcheck de Docker** (`compose.yaml`, servicio `server`): como la imagen (`python:3.13-slim`) no
   trae `curl`, se usa Python para pegarle a `/health` desde adentro del contenedor.
5. **Probarlo**: `postman/Re-intentos_Collection.json` (Retry) y `postman/Health_Collection.json` (Health).

### 3. Cómo probarlo

#### Retry

1. Levantar con `scripts/andis-up.ps1` e importar `postman/Re-intentos_Collection.json`.
2. Login, `POST /debug/simular-falla-conexion?veces=2`, y enseguida una operación real (`GET /mascotas`).
3. Con 2 réplicas, el `POST` y el `GET` pueden caer en réplicas distintas (Nginx las reparte round-robin), y
   como el contador de fallas simuladas vive en memoria de cada réplica, puede que no se note el retry. Para
   una demo determinística, escalar a 1 réplica antes:

   ```powershell
   docker compose up -d --scale server=1 server
   ```

   y volver a 2 después con `docker compose up -d --scale server=2 server`.
4. `GET /debug/ultimo-intento-conexion` debe mostrar `"intentos_usados": 3` y `"exitoso": true`.

#### Health Endpoint Monitoring

1. Con la app arriba, `curl http://localhost:8000/health` → 200.
2. `docker compose stop db`.
3. `curl http://localhost:8000/health` → 503.
4. `docker compose ps server` → al cabo de unos segundos (3 intentos × 10s) pasa a `unhealthy`.
5. `docker compose start db` → `/health` vuelve a 200 y la réplica vuelve a `healthy`, sin haber reiniciado
   `server` en ningún momento.

Los pasos manuales (parar/levantar `db`) están también como descripción de cada request en
`postman/Health_Collection.json`, porque Postman no puede ejecutar comandos de Docker.

### 4. Limitaciones

- **El contador de fallas simuladas es por réplica** (vive en memoria de cada proceso de `server`). Con 2
  réplicas detrás de Nginx, simular la falla en una no garantiza que la siguiente request caiga en esa misma
  réplica. No afecta al Retry real (que sí reintenta ante cualquier falla real), solo a la demo con el endpoint
  de simulación.
- **`/health` no reintenta**: es intencional (debe fallar rápido), pero significa que una falla de 1 segundo en
  la base puede marcar `/health` como caído aunque una operación normal (que sí reintenta) se hubiera
  recuperado sola.

---

## Cache en listados de referencia (Cache-Aside)

Pedir la lista de especies o de tipos de atención ejecuta siempre la misma consulta SQL, aunque esos datos casi
no cambien. Con Cache-Aside, la primera vez se consulta Postgres y se guarda el resultado en Redis; las
siguientes veces se responde directo desde Redis, sin volver a tocar la base — hasta que algo la modifica, que
ahí se invalida el cache.

- **Cache-Aside** (rendimiento): evitar repetir una consulta cuyo resultado probablemente no cambió.

### Contenido de esta sección

1. [Cómo funciona](#1-cómo-funciona-1)
2. [Cómo se hizo](#2-cómo-se-hizo-1)
3. [Cómo probarlo](#3-cómo-probarlo-1)
4. [Variables de configuración](#4-variables-de-configuración)
5. [Limitaciones](#5-limitaciones)

### 1. Cómo funciona

1. `GET /especies` o `GET /tipos-atencion` primero preguntan a Redis por la clave correspondiente
   (`especies:activas` o `tipos_atencion:listado`).
2. Si está (**cache hit**), se devuelve ese contenido directo, sin ejecutar ninguna consulta SQL.
3. Si no está (**cache miss**), se consulta Postgres, se guarda el resultado en Redis con un TTL
   (`CACHE_TTL_SECONDS`), y se devuelve.
4. `POST /tipos-atencion` (crear un tipo de atención nuevo) borra la clave `tipos_atencion:listado` de Redis
   después de insertar en Postgres, porque la lista guardada quedó vieja.

| Endpoint | Qué hace con el cache |
| --- | --- |
| `GET /especies` | Cache-aside sobre la clave `especies:activas`. |
| `GET /tipos-atencion` | Cache-aside sobre la clave `tipos_atencion:listado`. |
| `POST /tipos-atencion` | Invalida (borra) `tipos_atencion:listado` al crear un tipo nuevo. |

### 2. Cómo se hizo

1. **El cliente de Redis** (`app/cache.py`): la clase `Cache` envuelve `get`/`set`/`delete` de Redis,
   serializando a JSON. Si Redis no responde, atrapa el error y devuelve `None` (la app sigue funcionando
   contra Postgres directo, solo más lenta, en vez de romperse).
2. **`especies`** (`app/especies/service.py`): `listar_activas()` pregunta al cache antes de ir al repositorio.
3. **`tipos_atencion`** (`app/tipos_atencion/service.py`): igual que especies para `listar()`, y además
   `crear()` invalida la clave después de insertar.
4. **Redis en `compose.yaml`**: nuevo servicio `redis` (imagen `redis:7-alpine`), con `healthcheck` propio.

### 3. Cómo probarlo

1. Importar `postman/Cache_Collection.json` y correr la colección completa (`Run`).
2. La secuencia: login → primer `GET /tipos-atencion` (cache miss, consulta Postgres) → segundo `GET`
   (cache hit, mismo contenido) → `POST` de un tipo nuevo (invalida el cache) → tercer `GET` (cache miss de
   nuevo, ya con el tipo nuevo incluido).
3. Para comprobar a ojo que realmente pasó por Redis: `docker compose exec redis redis-cli get
   tipos_atencion:listado` después del primer `GET` debe mostrar el JSON guardado.
4. Si se quiere forzar un cache miss limpio antes de medir tiempos:
   `docker compose exec redis redis-cli DEL tipos_atencion:listado especies:activas`.

### 4. Variables de configuración

Están en `compose.yaml`, dentro del servicio `server`.

| Variable | Valor | Para qué sirve |
| --- | --- | --- |
| `REDIS_HOST` | `redis` | Nombre del servicio Redis dentro de la red de Docker. |
| `REDIS_PORT` | `6379` | Puerto de Redis. |
| `REDIS_DB` | `0` | Número de base de datos lógica de Redis a usar. |
| `CACHE_TTL_SECONDS` | `300` | Cuánto tiempo vive una clave en el cache antes de vencer sola. |

### 5. Limitaciones

- **`especies` no tiene invalidación propia**: no hay un endpoint para crear/editar especies en el proyecto, así
  que su única forma de refrescarse es el TTL de 5 minutos. `tipos_atencion` sí invalida al crear.
- **Si Redis se cae, la app no se cae con él**: `Cache` atrapa `RedisError` y devuelve `None`/no hace nada,
  así que el servicio sigue funcionando yendo directo a Postgres (más lento, pero no roto).

---

## Exportación del historial a PDF (Asynchronous Request-Reply + Valet Key)

El veterinario pide el historial clínico de una mascota en PDF. Como generarlo puede tardar, la API **no lo
hace esperar**: le responde enseguida y arma el PDF por detrás. Cuando está listo, le da un **enlace
temporal** que sirve para descargar ese PDF, aunque quien lo abra no tenga cuenta.

- **Asynchronous Request-Reply** (rendimiento): responder rápido y trabajar por detrás.
- **Valet Key** (seguridad): un enlace que sirve solo para un archivo y solo por un rato.

### Contenido de esta sección

1. [Cómo funciona](#1-cómo-funciona-2)
2. [Cómo se hizo](#2-cómo-se-hizo-2)
3. [Cómo probarlo](#3-cómo-probarlo-2)
4. [Variables de configuración](#4-variables-de-configuración-1)
5. [Limitaciones](#5-limitaciones-1)

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

---

## Gateway en Nginx (Gateway Offloading)

Nginx es la única puerta de entrada pública (las réplicas de `server` no se exponen directo). Hasta ahora solo
hacía balanceo y retry; se le agregaron responsabilidades que no son lógica de negocio, para que la API no
tenga que implementarlas.

- **Gateway Offloading** (seguridad): sacarle a la API tareas transversales (TLS, headers de seguridad, límite
  de pedidos) y resolverlas en el gateway.

### Contenido de esta sección

1. [Cómo funciona](#1-cómo-funciona-3)
2. [Cómo se hizo](#2-cómo-se-hizo-3)
3. [Cómo probarlo](#3-cómo-probarlo-3)
4. [Limitaciones](#4-limitaciones-1)

### 1. Cómo funciona

1. **Termina TLS**: Nginx escucha también en `8443` con HTTPS (certificado autofirmado generado al construir
   la imagen). Hacia la API el tráfico sigue siendo HTTP normal — la API nunca ve HTTPS.
2. **Agrega headers de seguridad** a toda respuesta: `X-Content-Type-Options: nosniff`,
   `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`. Y oculta qué corre detrás (`proxy_hide_header
   Server`, `server_tokens off`).
3. **Limita los intentos de login por IP**: solo cuenta `POST /auth/login` (`limit_req_zone` con una clave que
   queda vacía para cualquier otra ruta). 30 por minuto, con una ráfaga de hasta 20 antes de empezar a cortar.
   Si se supera, Nginx responde **429** directo, sin que el pedido llegue nunca a la API.

### 2. Cómo se hizo

1. **`nginx/Dockerfile`**: antes el `balanceador` usaba la imagen `nginx:alpine` pelada; ahora se *buildea* una
   imagen propia que instala `openssl` y genera un certificado autofirmado (`server.crt`/`server.key`) para
   `localhost` al construirse.
2. **`nginx/andis.conf`**: agrega el bloque `limit_req_zone` (con el `map` que solo cuenta `POST /auth/login`),
   el `listen 8443 ssl` con el certificado generado, los `add_header` de seguridad, y un `error_page 429` con un
   cuerpo JSON propio (`{"detail":"Demasiados intentos..."}`) en vez de la página de error default de Nginx.
3. **`compose.yaml`**: el servicio `balanceador` pasó de `image: nginx:alpine` a `build: context: ./nginx`, y
   se agregó el puerto `8443:8443`.

### 3. Cómo probarlo

1. Importar `postman/GatewayoffLoading_Collection.json`.
2. Mandar una ráfaga de `POST /auth/login` seguidos (más de 20 en poco tiempo) y verificar que, después de la
   ráfaga permitida, empiezan a responder **429** con el mensaje propio, sin que la API los procese.
3. Pedir cualquier endpoint por `https://localhost:8443/...` (con `-k`/ignorando el certificado, porque es
   autofirmado) y verificar con `curl -I` que la respuesta trae los headers de seguridad.
4. Repetir el mismo pedido por `http://localhost:8000/...` (puerto HTTP) y confirmar que los headers de
   seguridad también están — los agrega Nginx en el único `location`, sin importar el puerto de entrada.

### 4. Limitaciones

- **El certificado es autofirmado**: sirve para demostrar que Nginx termina TLS, pero un navegador real va a
  mostrar advertencia. Para producción haría falta un certificado válido (Let's Encrypt, por ejemplo).
- **El rate limit solo cubre `/auth/login`**, no todo el tráfico — fue una decisión para proteger el punto más
  sensible (fuerza bruta de contraseñas) sin arriesgar falsos positivos en el uso normal de la API.

---

## Configuración externa del login (External Configuration Store)

`LOGIN_MAX_INTENTOS` y `LOGIN_BLOQUEO_MINUTOS` (cuántos intentos fallidos tolerar antes de bloquear una cuenta,
y por cuánto tiempo) ya no son un valor fijo leído una sola vez al arrancar: viven en una tabla de Postgres y
se consultan en cada intento de login. Un administrador puede cambiarlos en caliente, sin reconstruir la
imagen ni reiniciar ningún contenedor.

- **External Configuration Store** (modificabilidad): sacar configuración del proceso y ponerla en un store
  externo que se puede cambiar en runtime.

### Contenido de esta sección

1. [Cómo funciona](#1-cómo-funciona-4)
2. [Cómo se hizo](#2-cómo-se-hizo-4)
3. [Cómo probarlo](#3-cómo-probarlo-4)
4. [Limitaciones](#4-limitaciones-2)

### 1. Cómo funciona

1. La tabla `configuracion` (clave/valor) guarda `LOGIN_MAX_INTENTOS` y `LOGIN_BLOQUEO_MINUTOS`.
2. Cada vez que un login falla, `LoginService` le pregunta a `ConfiguracionService` el valor actual de esas dos
   claves — no usa un valor fijo de `Settings`/variables de entorno para esto.
3. Un administrador puede leer y cambiar esos valores con los endpoints de abajo. El cambio se aplica al
   próximo intento de login, sin reiniciar nada.

| Endpoint | Quién lo usa | Qué hace |
| --- | --- | --- |
| `GET /admin/configuracion` | Administrador | Lista toda la configuración. |
| `GET /admin/configuracion/{clave}` | Administrador | Lee una clave puntual. |
| `PUT /admin/configuracion/{clave}` | Administrador | Cambia el valor de una clave. |

### 2. Cómo se hizo

1. **La tabla** (`db/init/06_configuracion.sql`): se crea con los valores iniciales (`LOGIN_MAX_INTENTOS=5`,
   `LOGIN_BLOQUEO_MINUTOS=15`), los mismos que antes estaban fijos en `compose.yaml`.
2. **El módulo `app/configuracion/`**: `repository.py` lee/escribe la tabla, `service.py` valida el valor
   (tiene que ser un entero dentro de un rango razonable; si no, `ValorInvalidoError`) y expone
   `obtener_entero(clave)` para que otros módulos lo consuman, `controller.py` expone los 3 endpoints de
   arriba, todos restringidos a `requerir_rol("ADMINISTRADOR")`.
3. **`app/Auth/login/service.py`**: antes leía `settings.LOGIN_MAX_INTENTOS`/`settings.LOGIN_BLOQUEO_MINUTOS`
   (fijos desde que arrancaba el proceso). Ahora recibe un `ConfiguracionService` y le pregunta el valor en
   cada intento fallido.
4. **Probarlo**: `postman/Configstore_Collection.json`.

### 3. Cómo probarlo

1. Importar `postman/Configstore_Collection.json` y correr la colección completa.
2. La secuencia: login como administrador → leer `LOGIN_MAX_INTENTOS` (debe ser 5) → registrar una cuenta de
   prueba → 2 logins fallidos (con el límite en 5 todavía no bloquea) → el administrador baja el límite a 3
   con `PUT` → un tercer login fallido ya bloquea la cuenta → intentar con la contraseña correcta y confirmar
   que sigue bloqueada → restaurar el límite a 5.
3. Todo esto pasa **sin reiniciar el contenedor `server` en ningún momento** — es lo que demuestra el patrón.
4. Un cliente (no administrador) que intente `GET /admin/configuracion` debe recibir 403.

### 4. Limitaciones

- **Solo cubre dos valores** (los límites de bloqueo de login). Otros parámetros de la app siguen siendo
  variables de entorno fijas; se eligieron estos dos porque son los que tiene sentido poder ajustar en caliente
  ante un ataque de fuerza bruta real.
- **La tabla también depende de que el volumen de Postgres sea nuevo** (mismo caso que `tarea_exportacion`):
  si la base ya existía antes de este cambio, hay que crear la tabla a mano con
  `Get-Content .\db\init\06_configuracion.sql -Raw | docker exec -i postgres-dev psql -U postgres -d postgres`.
