# Pet-Core — Endpoints adicionales para la TFU2

Complemento del documento principal de la API. Acá están **solo los siete endpoints que no forman parte del producto** y que existen para demostrar las tácticas de arquitectura de la Unidad Temática 2.

Todo lo demás que la TFU2 necesita ya está en el documento del proyecto: son endpoints normales de la aplicación cuyo comportamiento sirve como demostración.

---

## Las cuatro tácticas y dónde se ven

| Táctica | Atributo | Se demuestra con |
|---|---|---|
| Control de cordura | Protección | `GET /mascotas/{id}/historial` + endpoint de corrupción |
| Rollback | Protección | `POST /turnos/{id}/consulta` + endpoint de fallo |
| Binding en configuración | Facilidad de modificación | `GET /admin/config/roles` |
| Polimorfismo | Facilidad de modificación | `GET` y `POST /admin/config/notificaciones` |

El rollback se presenta como **táctica adicional**: no forma parte de la combinación elegida, pero refuerza el mismo atributo desde el enfoque opuesto. El control de cordura detecta una inconsistencia ya producida; el rollback impide que se produzca.

---

## 1 · Configuración (3 endpoints)

Sostienen las dos tácticas de diferir el binding.

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/admin/config/roles` | Roles y permisos tal como fueron leídos del archivo al arrancar. |
| GET | `/admin/config/notificaciones` | Canal activo y canales disponibles. |
| POST | `/admin/config/notificaciones/canal` | Cambia el canal activo en ejecución. Body: `{"canal": "SMS"}`. |

**Respuesta de `/admin/config/roles`:**
```json
{
  "origen": "config/roles.yaml",
  "cargado_el": "2026-08-25T08:00:00Z",
  "roles": {
    "CLIENTE": {
      "sesion_minutos": 60,
      "permisos": ["mascota:leer:propio", "turno:crear", "historial:leer:propio"]
    },
    "VETERINARIO": {
      "sesion_minutos": 30,
      "permisos": ["historial:leer:todo", "consulta:crear", "agenda:leer:propio"]
    },
    "ADMINISTRADOR": {
      "sesion_minutos": 30,
      "permisos": ["usuario:gestionar", "turno:leer:todo", "auditoria:leer"]
    }
  }
}
```

**Lo que hay que hacer notar en la demo:** el rol ADMINISTRADOR no tiene ningún permiso que empiece con `historial:` ni con `consulta:`. Esa ausencia es lo que hace cumplir la restricción de acceso al contenido clínico, y está declarada en un archivo de texto, no en el código.

**Respuesta de `/admin/config/notificaciones`:**
```json
{
  "canal_activo": "CONSOLA",
  "canales_disponibles": [
    { "nombre": "CONSOLA", "descripcion": "Escribe en el log del servidor" },
    { "nombre": "EMAIL", "descripcion": "Envía por correo electrónico" },
    { "nombre": "SMS", "descripcion": "Envía por mensaje de texto" }
  ],
  "origen": "config/notificaciones.yaml"
}
```

---

## 2 · Demostración (2 endpoints)

**Solo existen si `MODO_DEMO=true`.** En cualquier otro ambiente devuelven 404. Esa condición es, de paso, otro ejemplo de binding en configuración.

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/debug/corromper-historial/{id_mascota}` | Introduce una inconsistencia deliberada. Body: `{"tipo": "correccion_faltante"}`. |
| POST | `/debug/fallar-registro/{id_turno}` | Provoca un error a mitad de la transacción de registro de consulta. |

### Corromper historial

Un tipo de corrupción por cada verificación del control de cordura:

| Tipo | Qué rompe | Verificación que dispara |
|---|---|---|
| `correccion_faltante` | Marca una consulta como corregida sin insertar la corrección | Toda consulta corregida trae su corrección |
| `motivo_vacio` | Deja el motivo en blanco | El motivo está presente y no vacío |
| `fecha_futura` | Pone una fecha de registro posterior a hoy | Ninguna fecha es futura |
| `conteo_desigual` | Hace que la cantidad recuperada no coincida con la registrada | El conteo coincide |
| `correccion_huerfana` | Deja una corrección apuntando a una consulta inexistente | Toda corrección apunta a una original existente |

Después de llamarlo, `GET /mascotas/{id}/historial` debe responder con `consistente: false`, la advertencia correspondiente y las consultas no recuperadas ocupando su lugar en la lista con `recuperada: false`.

**La API no devuelve el historial como válido.** Ese es el punto: no se trata de que el dato esté completo siempre, sino de que el sistema nunca presente como completo algo que no lo es.

### Fallar registro

Ejecuta `POST /turnos/{id}/consulta` pero lanza una excepción **después** de escribir la consulta y **antes** de actualizar el estado del turno.

Resultado esperado: la transacción se revierte. Al consultar después, la consulta no existe y el turno sigue en `CONFIRMADO`. No queda nada a medias.

---

## 3 · Salud (2 endpoints)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health/reservas` | Verifica que las funcionalidades de reserva respondan. |
| GET | `/health/clinico` | Verifica que las funcionalidades clínicas respondan. |

Cada uno hace una consulta mínima sobre las tablas de su módulo y responde `{"estado": "ok"}` o falla.

Permiten medir por separado los dos objetivos de disponibilidad de la UT1: 99,5 % en reservas medido 24/7, y 99,9 % en el módulo clínico medido de lunes a viernes de 8:00 a 18:00.

No son imprescindibles para la demo de tácticas. Se incluyen porque cuestan poco y respaldan los requerimientos de disponibilidad.

---

## Endpoints del proyecto que la demo utiliza

Estos **ya están en el documento principal**. Se listan para saber cuáles tienen que estar terminados antes de grabar el video.

| Endpoint | Qué demuestra |
|---|---|
| `POST /auth/login` y `GET /auth/me` | Permisos leídos de configuración |
| `GET /mascotas/{id}/historial` | Control de cordura, con sus cinco verificaciones |
| `POST /turnos/{id}/consulta` | Rollback: consulta y estado del turno en una transacción |
| `PATCH /consultas/{id}` | Dispara la notificación por el canal activo |
| `POST /turnos/{id}/reprogramar` | Rollback en operación atómica |
| `GET /notificaciones` | Muestra que la notificación llegó |
| `POST /turnos` | Restricción de no superposición bajo concurrencia |

---

## Las cinco verificaciones del control de cordura

Se ejecutan antes de devolver cualquier historial. Están en `GET /mascotas/{id}/historial`, no en un endpoint aparte.

1. La cantidad de consultas recuperadas coincide con la registrada para esa mascota.
2. Toda consulta marcada como corregida tiene presente la entrada que la corrige.
3. Toda corrección apunta a una consulta original que existe.
4. El motivo está presente y no es cadena vacía.
5. Ninguna fecha de registro es posterior a la fecha actual.

Si alguna falla, la respuesta lleva `consistente: false` y el detalle en `advertencias`.

---

## Guion de la demostración

Cinco minutos, cuatro escenarios. Conviene guionarlo antes de grabar: son unos setenta segundos por táctica contando la introducción.

**1. Control de cordura** *(~70 s)*
```
GET  /mascotas/1/historial              → consistente: true, 9 de 9
POST /debug/corromper-historial/1
     {"tipo": "correccion_faltante"}
GET  /mascotas/1/historial              → consistente: false
                                          "No se pudieron recuperar 2 de 9"
```
Mostrar que la respuesta **no** entrega el historial como válido y que la consulta faltante ocupa su lugar con `recuperada: false`.

**2. Rollback** *(~70 s)*
```
GET  /mascotas/1/historial              → 3 consultas
GET  /turnos/5                          → estado CONFIRMADO
POST /debug/fallar-registro/5           → error controlado
GET  /mascotas/1/historial              → siguen 3 consultas
GET  /turnos/5                          → sigue CONFIRMADO
```
Señalar que la escritura de la consulta y el cambio de estado del turno ocurren en la misma transacción: no hay estado intermedio observable.

**3. Binding en configuración** *(~70 s)*
```
GET  /admin/config/roles                → 3 roles
[descomentar RECEPCIONISTA en config/roles.yaml]
[docker compose restart api]
GET  /admin/config/roles                → 4 roles
POST /auth/login  (recepcionista)
GET  /admin/agenda                      → 200, opera con sus permisos
GET  /mascotas/1/historial              → 403, no tiene ese permiso
```
Mostrar que **ningún archivo de código fue modificado**: solo el YAML.

**4. Polimorfismo** *(~70 s)*
```
GET   /admin/config/notificaciones      → canal activo: CONSOLA
PATCH /consultas/41                     → notificación por consola
POST  /admin/config/notificaciones/canal
      {"canal": "EMAIL"}
PATCH /consultas/42                     → notificación por email
GET   /notificaciones                   → ambas registradas, distinto canal
```
Señalar que el módulo de historial clínico es idéntico entre una y otra: invoca la abstracción y desconoce el canal.

---

## Dos escenarios que conviene agregar si sobra tiempo

**Configuración inválida.** Arrancar con un `roles.yaml` mal escrito —por ejemplo, otorgándole al administrador un permiso `historial:leer:todo`— y mostrar que la aplicación **rechaza el inicio** en lugar de arrancar con permisos rotos.

Es el escenario que demuestra que pensaron el **costo** de la táctica: mover los permisos a un archivo de texto los saca del alcance del compilador, y la validación al arrancar es lo que compensa esa pérdida.

**Costo del control de cordura.** Medir el tiempo de respuesta del historial con y sin las verificaciones activas. Da un dato concreto en lugar de la afirmación genérica de que "toda táctica tiene un costo".

---

## Cuatro cosas para no olvidar en el video

**No mostrar código fuente durante el escenario 3.** El punto es justamente que no hay que tocarlo. Mostrar el YAML y la terminal alcanza.

**Los endpoints `/debug/*` conviene implementarlos temprano.** Sin ellos no hay forma de verificar que las tácticas funcionan, ni de ensayar la demo.

**Cada táctica tiene un costo declarado en el documento de la Parte 1.** Mencionarlo al pasar en cada escenario suma: la unidad cierra insistiendo en que ninguna táctica es gratis.

**El rollback va presentado como adicional**, no como parte de la combinación exigida. Así queda claro que la combinación elegida está completa por sí sola y que esto se agregó por decisión propia.
