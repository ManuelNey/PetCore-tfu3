# Pet-Core - Demostración de tácticas de arquitectura

Este proyecto utiliza una API REST desarrollada con FastAPI para demostrar tácticas de disponibilidad y seguridad. La demostración de disponibilidad combina replicación de la API, balanceo mediante Nginx y reintentos cuando una réplica no responde.

## Índice

- [Requisitos](#requisitos)
- [Preparación local](#preparación-local)
- [Levantar la aplicación](#levantar-la-aplicación)
- [Estructura](#estructura)
- [Importar las peticiones en Postman](#importar-las-peticiones-en-postman)
- [Demostración de seguridad con Postman](#demostración-de-seguridad-con-postman)
- [Demostración automática de autenticación](#demostración-automática-de-autenticación)
- [Demostración automática de autorización](#demostración-automática-de-autorización)
- [Demostración de replicación con Postman](#demostración-de-replicación-con-postman)
- [Demostración de reintentos con Postman](#demostración-de-reintentos-con-postman)
- [Demostración automática de replicación](#demostración-automática-de-replicación)
- [Demostración automática de reintentos](#demostración-automática-de-reintentos)
- [Detener la aplicación](#detener-la-aplicación)
- [Datos de prueba](#datos-de-prueba)

## Requisitos

Comprobar que Git y Docker Desktop estén instalados:

```powershell
git --version
docker --version
docker compose version
docker info
```

Docker Desktop debe estar abierto. No es necesario instalar PostgreSQL, FastAPI ni Nginx manualmente.

## Preparación local

Abrir PowerShell en la carpeta del proyecto:

```powershell
cd "C:\ruta\Proyecto_Clínica_Veterinaria"
```

Crear la contraseña local de PostgreSQL:

```powershell
New-Item -ItemType Directory -Force db
Set-Content -Path db/password.txt -Value "CAMBIAR_POR_UNA_CONTRASENA"
```

Crear una clave aleatoria para los tokens JWT utilizando PowerShell:

```powershell
$bytes = New-Object byte[] 32
$generador = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$generador.GetBytes($bytes)
$generador.Dispose()
$jwtSecret = ([BitConverter]::ToString($bytes)).Replace("-", "").ToLower()
Set-Content -Path db/jwt-secret.txt -Value $jwtSecret -NoNewline
```

`db/password.txt` y `db/jwt-secret.txt` contienen información sensible, no se guardan en Git y cada integrante debe crear los suyos.

## Levantar la aplicación

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

El script construye las imágenes y levanta PostgreSQL, el frontend, Nginx y dos réplicas de FastAPI.

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs

Comprobar los contenedores:

```powershell
docker compose ps
```

Deben aparecer dos contenedores pertenecientes al servicio `server`.

## Estructura

```text
Postman
   |
   v
Nginx :8000
   |------> FastAPI replica 1 :8000
   |------> FastAPI replica 2 :8000
                       |
                       v
                  PostgreSQL
```

Nginx distribuye las solicitudes entre las réplicas. Si una conexión falla, intenta enviar la solicitud a la otra disponible.

El endpoint de demostración es:

```http
GET /demo/instancia
```

Ejemplo de respuesta:

```json
{
  "instancia": "dc0948ef34a5"
}
```

El valor es el hostname asignado por Docker al contenedor que respondió. Cada réplica tiene uno diferente.

## Importar las peticiones en Postman

1. Abrir Postman y seleccionar **Import**.
2. Seleccionar `postman/Seguridad_Collection.json`, `postman/Replicacion_Collection.json` y `postman/Re-intentos_Collection.json`.
3. Abrir la colección que se quiera utilizar.
4. Las colecciones utilizan direcciones explícitas con `http://localhost:8000`; no requieren configurar un Environment ni una variable `base_url`.
5. Después de cada petición de inicio de sesión, copiar manualmente el valor de `access_token` y pegarlo en **Authorization > Bearer Token** de las peticiones siguientes indicadas por la colección.

El endpoint de demostración requiere un token válido, pero acepta cualquier rol autenticado. Manejar el JWT manualmente permite ver con claridad qué dato devuelve el login y qué dato se envía después en el encabezado `Authorization`.

## Demostración de seguridad con Postman

La colección `postman/Seguridad_Collection.json` demuestra dos tácticas de la categoría **resistir ataques**:

- **Autenticar actores:** comprobar la identidad mediante correo, contraseña y un token JWT.
- **Autorizar actores:** permitir o rechazar operaciones según el rol incluido en el JWT.

Conviene ejecutar esta demostración antes de replicación y reintentos, porque las demás colecciones también utilizan el login y los tokens.

### Preparación

Levantar el ambiente:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

Importar `postman/Seguridad_Collection.json`. Las peticiones están numeradas y deben ejecutarse en orden.

### Táctica 1: autenticar actores

1. Ejecutar **1 - Acceder a mascotas sin iniciar sesion**.

La petición intenta acceder a `GET /mascotas` sin enviar un token. La respuesta esperada es:

```text
401 Unauthorized
```

Esto demuestra que conocer la dirección del endpoint no alcanza para utilizarlo.

2. Ejecutar **2 - Iniciar sesion como cliente**.

La API valida las credenciales y responde `200 OK` junto con un JWT. Copiar el valor de `access_token` de la respuesta y pegarlo manualmente en **Authorization > Bearer Token** de las peticiones 3 y 4.

3. Ejecutar **3 - Cliente consulta sus mascotas**.

Postman envía el JWT pegado manualmente como Bearer Token. La respuesta esperada es `200 OK` y contiene las mascotas reales del cliente. El mismo endpoint que rechazó la primera petición ahora permite el acceso porque la identidad fue autenticada.

### Táctica 2: autorizar actores

4. Ejecutar **4 - Cliente intenta acceder a la agenda veterinaria**.

El cliente posee un JWT válido, pero intenta acceder a `GET /agenda`, que requiere el rol `VETERINARIO`. La respuesta esperada es:

```text
403 Forbidden
```

`401` significa que no se pudo autenticar al usuario. `403` significa que el usuario sí fue autenticado, pero su rol no tiene permiso para ejecutar esa operación.

5. Ejecutar **5 - Iniciar sesion como veterinario**.

Postman utiliza `bruno.vet@petcore.com` y debe recibir `200 OK`. Copiar su `access_token` y pegarlo manualmente en **Authorization > Bearer Token** de la petición 6.

6. Ejecutar **6 - Veterinario accede a su agenda**.

La petición utiliza el token del veterinario para llamar a `GET /agenda`. La respuesta esperada es `200 OK`, porque el usuario tiene el rol requerido.

La evidencia de esta demo es visual: comprobar los códigos `401`, `200`, `403` y `200` que aparecen en Postman.

## Demostración automática de autenticación

El script `scripts/demo-autenticacion.ps1` reproduce automáticamente la primera táctica de seguridad sobre el endpoint real `GET /mascotas`:

1. intenta acceder a `GET /mascotas` sin token;
2. comprueba que la API responda `401 Unauthorized`;
3. inicia sesión como cliente;
4. repite la solicitud enviando el JWT;
5. comprueba que la API responda `200 OK`.

Ejecutar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo-autenticacion.ps1
```

La salida esperada es:

```text
Estado sin token: 401
Estado con token: 200
Demostracion de autenticacion exitosa.
```

## Demostración automática de autorización

El script `scripts/demo-autorizacion.ps1` reproduce automáticamente la segunda táctica de seguridad:

1. inicia sesión como cliente;
2. intenta acceder a `GET /agenda`;
3. comprueba que la API responda `403 Forbidden`;
4. inicia sesión como veterinario;
5. accede nuevamente a `GET /agenda`;
6. comprueba que la API responda `200 OK`.

Ejecutar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo-autorizacion.ps1
```

La salida esperada es:

```text
Estado para el cliente: 403
Estado para el veterinario: 200
Demostracion de autorizacion exitosa.
```

## Demostración de replicación con Postman

### 1. Comprobar el balanceo

Levantar la aplicación:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

Ejecutar primero **1 - Iniciar sesion como cliente**, copiar el `access_token` y pegarlo manualmente como Bearer Token en las peticiones 2 y 3. Luego ejecutar varias veces:

```http
GET http://localhost:8000/demo/instancia
```

Las respuestas deben alternar entre dos identificadores porque existen dos contenedores ejecutando la misma API. Nginx utiliza de forma predeterminada un balanceo llamado *round-robin*: envía la primera solicitud a una réplica, la siguiente a la otra y luego vuelve a comenzar. El endpoint devuelve el hostname del contenedor que atendió cada solicitud, por eso se observan dos valores diferentes aunque ambos contenedores ejecuten el mismo código.

Por ejemplo:

```text
Solicitud 1 -> replica 1 -> dc0948ef34a5
Solicitud 2 -> replica 2 -> bdd5ee22fea7
Solicitud 3 -> replica 1 -> dc0948ef34a5
Solicitud 4 -> replica 2 -> bdd5ee22fea7
```

En **Headers** se pueden observar:

```text
X-Upstream-Addr
X-Upstream-Status
```

`X-Upstream-Addr` identifica el servidor interno utilizado y `X-Upstream-Status` muestra el resultado obtenido desde la API.

### 2. Provocar la falla de una réplica

Mostrar los nombres de los contenedores:

```powershell
docker compose ps
```

Detener una réplica, sustituyendo el nombre del ejemplo si fuera diferente:

```powershell
docker stop proyecto_clnica_veterinaria-server-1
docker compose ps -a
```

Una réplica debe aparecer como `Exited` y la otra como `Up`.

### 3. Comprobar la continuidad y los reintentos

Sin recuperar la réplica detenida, volver a ejecutar varias veces en Postman:

```http
GET http://localhost:8000/demo/instancia
```

Las solicitudes deben continuar respondiendo con `200 OK` desde la réplica activa. Además de `2 - Identificar instancia`, ejecutar `3 - Consultar mascotas`: este endpoint real de Pet-Core también debe responder `200 OK` mientras quede una réplica disponible. Cuando Nginx intenta primero acceder a la que acaba de fallar, los encabezados pueden mostrar:

```text
X-Upstream-Status: 502, 200
```

Esto indica que el primer intento falló y el siguiente fue atendido por la otra réplica. Si Nginx ya marcó temporalmente la réplica como no disponible, puede aparecer directamente `200`.

La evidencia conjunta es:

- Docker muestra una réplica detenida;
- Postman continúa recibiendo `200 OK`;
- el cuerpo de `demo/instancia` identifica la réplica activa;
- `GET /mascotas` confirma que una funcionalidad real continúa disponible;
- los encabezados muestran el servidor utilizado y, cuando ocurre, el reintento.

### 4. Recuperar las dos réplicas

```powershell
docker compose up -d --scale server=2 server
docker compose up -d --no-deps --force-recreate balanceador
docker compose ps
```

## Demostración de reintentos con Postman

Esta demostración utiliza la colección **Pet-Core Re-intentos**, guardada en `postman/Re-intentos_Collection.json`.

Las peticiones están numeradas en el orden en que deben ejecutarse:

1. **Iniciar sesion** autentica al cliente; copiar manualmente su `access_token` y pegarlo como Bearer Token en las peticiones 2, 3 y 4.
2. **Simular fallas de conexion** configura dos fallas mediante `POST /debug/simular-falla-conexion?veces=2`.
3. **Ejecutar operacion con reintentos** llama a `GET /mascotas`, que accede a la base de datos y activa la lógica de reintentos.
4. **Consultar ultimo intento** llama a `GET /debug/ultimo-intento-conexion` para observar la información registrada durante la prueba.

### Paso a paso

1. Levantar el ambiente:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

2. Para esta demostración, dejar temporalmente una sola réplica y actualizar Nginx:

```powershell
docker compose up -d --scale server=1 server
docker compose up -d --no-deps --force-recreate balanceador
```

Se utiliza una sola réplica porque el estado de la falla simulada se guarda en la memoria del contenedor. Así, todas las peticiones de la demostración llegan al mismo proceso.

3. Importar `postman/Re-intentos_Collection.json` en Postman.
4. Ejecutar **1 - Iniciar sesion** y comprobar que responda `200 OK`. Copiar el `access_token` de la respuesta y pegarlo manualmente como Bearer Token en las peticiones 2, 3 y 4.
5. Ejecutar **2 - Simular fallas de conexion**. Debe responder un mensaje indicando que las próximas dos conexiones van a fallar.
6. Ejecutar **3 - Ejecutar operacion con reintentos**. Los intentos ocurren de esta manera:

```text
Intento 1 -> falla -> espera 0,5 segundos
Intento 2 -> falla -> espera 1 segundo
Intento 3 -> conexión exitosa
```

La solicitud debe terminar con `200 OK`: aunque hubo dos fallas transitorias, el tercer intento permitió completar la operación.

7. Ejecutar **4 - Consultar ultimo intento**. La respuesta esperada es similar a:

```json
{
  "intentos_usados": 3,
  "duracion_segundos": 1.5,
  "exitoso": true
}
```

El tiempo puede variar levemente. Las evidencias principales son `intentos_usados: 3` y `exitoso: true`.

8. Opcionalmente, mostrar los mensajes de reintento registrados por la API:

```powershell
docker compose logs server --tail=50
```

Las tres peticiones posteriores al login deben enviar el mismo JWT pegado manualmente en **Authorization > Bearer Token**.

Los endpoints `debug` validan el usuario actual y deben responder `401 Unauthorized` cuando no reciben un token válido.

Al terminar, recuperar las dos réplicas utilizadas por la demostración de replicación:

```powershell
docker compose up -d --scale server=2 server
docker compose up -d --no-deps --force-recreate balanceador
```

## Demostración automática de replicación

La consigna solicita scripts para iniciar la aplicación y demostrar las tácticas:

| Script | Uso |
| --- | --- |
| `scripts/andis-up.ps1` | Construye y levanta el ambiente con dos réplicas. |
| `scripts/demo-replicacion.ps1` | Provoca una falla, comprueba la continuidad y recupera la réplica. |

Ejecutar la demostración automática:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo-replicacion.ps1
```

## Demostración automática de reintentos

El script `scripts/demo-reintentos.ps1` reproduce automáticamente la demostración de la colección **Pet-Core Re-intentos**.

El script:

1. deja temporalmente una sola réplica de FastAPI;
2. inicia sesión y obtiene un JWT;
3. configura dos fallas de conexión simuladas;
4. ejecuta `GET /mascotas`;
5. comprueba que la operación se recuperó en el tercer intento;
6. muestra la cantidad de intentos, la duración y el resultado;
7. restaura las dos réplicas aunque la demostración falle.

Primero levantar el ambiente:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```

Ejecutar la demostración:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo-reintentos.ps1
```

Una ejecución correcta debe mostrar aproximadamente:

```text
Intentos usados: 3
Duracion: 1.5 segundos
Exitoso: True
Demostracion de reintentos exitosa.
```

El tiempo puede cambiar levemente, pero el resultado debe ser exitoso y utilizar tres intentos.

## Detener la aplicación

```powershell
docker compose down
```

Este comando conserva el volumen de PostgreSQL. `docker compose down --volumes` elimina también los datos.

## Datos de prueba

La primera vez que se crea el volumen de PostgreSQL, `db/init/` carga el esquema y los datos de prueba. La contraseña de estos usuarios es `Password123!`:

| Correo | Rol |
| --- | --- |
| `ana.cliente@petcore.com` | Cliente |
| `bruno.vet@petcore.com` | Veterinario |
| `carla.admin@petcore.com` | Administrador |

Para reconstruir la base desde cero:

```powershell
docker compose down --volumes
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\andis-up.ps1
```
