# Pet-Core — API del proyecto

Endpoints organizados por pantalla del diseño. Base: `/api/v1`

Este documento es el que usa **todo el equipo**. Hay uno aparte con siete endpoints adicionales que necesita la materia Análisis y Diseño de Aplicaciones II; no hace falta leerlo para trabajar acá.

> **Antes de arrancar, en criollo:** un endpoint es una URL a la que el frontend le pega para
> pedir o mandar algo. `GET` = "dame esto" (no cambia nada, solo lee). `POST` = "creá esto
> nuevo" o "ejecutá esta acción". `PATCH` = "modificá una parte de esto que ya existe". `PUT` =
> "reemplazá esto por completo". Cada sección de abajo trae, después de la tabla técnica, un
> bloque **"Qué hacer"** con la idea en palabras simples y los detalles que no hay que olvidar
> al programarlo.

## Prioridades

| | Significado |
|---|---|
| **P1** | Núcleo. Sin esto la app no funciona. |
| **P2** | Completa el alcance definido. |
| **P3** | Puede quedar para el final. |

Los endpoints marcados con **★** son los que la materia usa para su demostración. No cambia nada de cómo se construyen; solo conviene saber que su comportamiento ante errores importa más de lo habitual.

**En criollo:** si tenés que elegir qué hacer primero, andá por P1. Los ★ no son "más difíciles",
son los que un profesor va a mirar de cerca en la demo — así que ahí el manejo de errores tiene
que estar prolijo, no solo el camino feliz.

## Convención de errores

| Código | Cuándo |
|---|---|
| 400 | Datos mal formados |
| 401 | Sin sesión o sesión expirada |
| 403 | Rol sin permiso para la operación |
| 404 | Recurso inexistente o fuera del alcance del rol |
| 409 | Conflicto de estado: horario tomado, plazo vencido, ventana de edición cerrada |
| 422 | Regla de negocio incumplida |
| 423 | Cuenta bloqueada temporalmente |

**En criollo:** son los números que ya conocés de cualquier página que te tiró error. Los que
más se usan acá son 404 (para "esto no existe **o no es tuyo**", nunca se distingue una cosa de
la otra) y 409 (alguien te ganó de mano o se te venció el tiempo). El resto son variantes de
"no podés" (401/403) o "mandaste algo mal" (400/422).

## Campos derivados que calcula el servidor

Estos no están en la base: se calculan al responder. **Nunca los calcula el navegador.**

| Campo | Cómo se obtiene | Dónde aparece |
|---|---|---|
| `estado_visual: "EN_CURSO"` | Turno `CONFIRMADO` y la hora actual cae dentro de su período | Agenda del veterinario y del administrador, lista de pacientes |
| `puede_cancelar` | Falta más de 1 hora para el inicio | Mis turnos |
| `edicion_vence_el` | `fecha_registro + 24 h` | Registrar consulta, historial |
| `edicion_vencida` | Ya pasaron las 24 h | Historial del veterinario |
| `edad` | A partir de `fecha_nacimiento` | Tarjetas de mascota |
| `estado_cuenta: "BLOQUEADO"` | `bloqueado_hasta` en el futuro | Usuarios (admin) |

**En criollo:** son datos que no existen como columna en ninguna tabla, se calculan al vuelo
cada vez que se arma la respuesta. Por ejemplo, `edad` no está guardada en ningún lado: se
calcula restando la fecha de hoy menos `fecha_nacimiento` justo antes de responder. Por qué
importa: si el frontend intentara calcular esto solo (por ejemplo mirar la hora de su propio
reloj para decidir si "puede cancelar"), un usuario podría hacer trampa cambiando la hora de
su compu. Por eso siempre lo calcula el servidor, con su propio reloj.

---

## Inicio de sesión
*Formulario de correo y contraseña. Estados: normal, credenciales inválidas, cuenta bloqueada con cuenta regresiva.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| POST | `/auth/login` | Valida credenciales, devuelve token y rol. Error genérico "Usuario o contraseña incorrectos". Tras 5 fallos → 423. | P1 ★ |
| POST | `/auth/logout` | Cierra la sesión. | P1 |
| GET | `/auth/me` | Usuario actual, rol y permisos efectivos. El frontend arma el menú con esto. | P1 ★ |
| POST | `/auth/registro` | Alta pública. **Siempre crea rol Cliente**, nunca otro. | P2 |

**Respuesta 423 (cuenta bloqueada):**
```json
{
  "error": "CUENTA_BLOQUEADA",
  "mensaje": "Se superaron los 5 intentos permitidos.",
  "bloqueado_hasta": "2026-08-25T08:48:00Z",
  "segundos_restantes": 640
}
```
El contador de la pantalla es informativo: el desbloqueo **lo valida el servidor** en el intento siguiente, no el reloj del navegador.

Sesión: 30 min de inactividad para veterinario y administrador, 1 hora para cliente. Sin segundo factor para ningún rol.

"Olvidé mi contraseña" queda como enlace informativo: indica comunicarse con la clínica. Sin endpoint por ahora.

**Qué hacer:** `login` recibe correo y contraseña, y si coinciden te devuelve un token (una
especie de "pulsera de acceso" que el frontend va a mandar en cada pedido siguiente para
probar quién es) y el rol de esa persona. Si falla 5 veces seguidas, en vez de dejarla seguir
probando, la cuenta se bloquea un rato (`423`) — y el mensaje de error siempre es el mismo
genérico, tanto si el correo no existe como si la contraseña está mal, para no darle pistas a
quien esté intentando adivinar. `auth/me` es lo primero que pregunta el frontend al abrir la
app: "¿quién sos y qué te puedo mostrar?", así arma el menú según el rol. Importante:
`auth/registro` **siempre** da de alta como Cliente — no tiene que existir forma de registrarse
como veterinario o admin por acá, eso lo hace el administrador desde su panel.

---

## Cliente · Mis mascotas
*Grilla de tarjetas. Cada una muestra edad, último peso, próximo turno y cantidad de consultas. Alta, baja lógica y reactivación.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/mascotas` | Mascotas del cliente. Filtro `?estado=ACTIVA`. Incluye los datos de resumen de la tarjeta. | P1 |
| POST | `/mascotas` | Alta. Nombre y especie obligatorios. | P1 |
| GET | `/mascotas/{id}` | Ficha. 404 si no es del cliente. | P1 |
| PATCH | `/mascotas/{id}` | Edita datos. | P2 |
| GET | `/mascotas/{id}/impacto-baja` | Turnos futuros que quedarían agendados. Alimenta el diálogo de confirmación. | P2 |
| POST | `/mascotas/{id}/baja` | Baja lógica. **Los turnos ya reservados no se cancelan.** | P2 |
| POST | `/mascotas/{id}/reactivar` | Vuelve a estado activa. | P2 |
| POST | `/mascotas/{id}/peso` | Registra peso con su fecha. | P3 |
| GET | `/mascotas/{id}/peso` | Histórico de pesos. | P3 |

**Respuesta de `/mascotas`:**
```json
[{
  "id": 1, "nombre": "Luna", "especie": "Canino", "raza": "Border collie",
  "edad": "4 años", "estado": "ACTIVA",
  "ultimo_peso": { "valor": 18.4, "fecha": "2026-07-02" },
  "proximo_turno": { "id": 88, "fecha_hora": "2026-08-25T10:30:00Z", "tipo": "Consulta general" },
  "consultas_registradas": 7
}]
```

La mascota inactiva **conserva su historial completo** y sigue siendo consultable.

**Qué hacer:** el CRUD típico de mascotas, con dos detalles que no son obvios. Primero, la
respuesta de `GET /mascotas` no es solo "nombre y especie": ya viene con todo lo que la
tarjetita necesita mostrar (último peso, próximo turno, cuántas consultas tiene), así el
frontend no tiene que pedir cinco cosas por separado para armar una sola tarjeta. Segundo,
"dar de baja" **no borra nada** — la mascota sigue en la base marcada como inactiva, y su
historial de consultas y pesos sigue existiendo y consultable para siempre. Antes de dar de
baja, `impacto-baja` le avisa al usuario si tiene turnos futuros agendados con esa mascota,
para que no se lleve una sorpresa.

---

## Cliente · Reservar turno
*Cuatro pasos: mascota → tipo de atención → veterinario → horario. La grilla del paso 4 es irregular porque depende de la duración del tipo elegido.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/tipos-atencion` | Solo los `reservable_cliente=true` si el rol es Cliente. Devuelve nombre, descripción y duración. | P1 |
| GET | `/veterinarios` | Activos, con matrícula, para el paso 3. | P1 |
| GET | `/disponibilidad` | **La operación más cara del sistema.** Params: `veterinario`, `fecha`, `tipo_atencion`. | P1 ★ |
| POST | `/turnos` | Confirma la reserva. Estado `CONFIRMADO`, `canal_origen=AUTOGESTION`. | P1 ★ |

**Respuesta de `/disponibilidad`:**
```json
{
  "fecha": "2026-08-25",
  "duracion_requerida": 30,
  "calculado_el": "2026-08-25T10:20:03Z",
  "slots": [
    { "inicio": "08:00", "disponible": true },
    { "inicio": "08:15", "disponible": false, "motivo": "HUECO_INSUFICIENTE" },
    { "inicio": "08:30", "disponible": false, "motivo": "OCUPADO" },
    { "inicio": "12:00", "disponible": false, "motivo": "FUERA_DE_AGENDA" }
  ]
}
```

Los tres motivos son los que la pantalla distingue en la leyenda: *hueco de 15 min no alcanza para 30*, *ocupado*, *no disponible*. `calculado_el` alimenta el "Actualizado hace 3 s".

**Objetivo de rendimiento:** menos de 2 s en condiciones normales, menos de 4 s con 80 usuarios concurrentes.

**Qué hacer:** este es el flujo completo de "quiero sacar un turno". El paso más importante y
más pesado de calcular es `/disponibilidad`: le mandás veterinario + fecha + qué tipo de
atención elegiste, y te devuelve franja por franja si está libre o no, **y por qué no** (el
campo `motivo`). Por eso la grilla de horarios se ve "salteada" cuando elegís una atención
larga — no es un error visual, es información real: un hueco de 15 minutos libres no sirve
para una consulta de 30. Como es la operación más pesada, hay un objetivo de tiempo de
respuesta concreto para no dejar a la persona esperando. `POST /turnos` es el que confirma
todo — y ahí es donde puede pasar el caso del próximo bloque.

---

## Cliente · El horario fue tomado al confirmar
*Pantalla de rechazo cuando otro cliente reservó ese horario segundos antes.*

No es un endpoint nuevo: es la respuesta de error de `POST /turnos`.

```json
HTTP 409
{
  "error": "HORARIO_NO_DISPONIBLE",
  "mensaje": "Otro cliente reservó las 10:30 con la Dra. Álvarez segundos antes de tu confirmación.",
  "seleccion_conservada": {
    "id_mascota": 1, "id_tipo_atencion": 1, "id_veterinario": 2
  },
  "disponibilidad_actualizada": { "calculado_el": "...", "slots": [...] }
}
```

**Importante para quien lo implemente:** la base de datos tiene una restricción que impide dos turnos superpuestos. Cuando se dispara, Postgres devuelve el error `23P01` (`exclusion_violation`). Hay que **capturarlo y traducirlo a este 409**, no dejar que salga como 500.

`seleccion_conservada` es obligatorio: el cliente no pierde lo que ya eligió.

**Qué hacer:** el caso feo pero esperable: dos personas ven el mismo horario libre y las dos
aprietan "confirmar" casi al mismo tiempo. Una gana. A la otra, la base de datos le tira un
error técnico interno (`23P01`) porque tiene una regla que no deja guardar dos turnos que se
pisan. **Ese error técnico no tiene que llegar tal cual al usuario** (sería un 500 feo y sin
sentido para él): hay que atajarlo en el código y devolver este 409 con un mensaje entendible.
Y lo más importante para no romper la experiencia: mandar `seleccion_conservada`, para que la
persona no tenga que volver a elegir mascota, tipo de atención y veterinario desde cero — solo
tiene que elegir otro horario.

---

## Cliente · Mis turnos
*Lista con filtros Próximos / Pasados / Todos. Cancelar y reprogramar hasta 1 hora antes.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/turnos` | Filtros `?periodo=proximos\|pasados\|todos`. | P1 |
| GET | `/turnos/{id}` | Detalle. | P1 |
| POST | `/turnos/{id}/cancelar` | Valida el plazo de 1 h **al ejecutar**, no al mostrar. 409 si venció. | P1 ★ |
| POST | `/turnos/{id}/reprogramar` | Cambia fecha, hora y veterinario. **Operación atómica.** | P1 ★ |

**Respuesta de `/turnos`:**
```json
[{
  "id": 88,
  "fecha_hora_inicio": "2026-08-25T10:45:00Z",
  "duracion_minutos": 30,
  "tipo": "Consulta general",
  "mascota": { "id": 1, "nombre": "Luna", "especie": "Canino", "estado": "ACTIVA" },
  "veterinario": "Dra. M. Álvarez",
  "estado": "CONFIRMADO",
  "puede_cancelar": false,
  "motivo_bloqueo": "Falta menos de 1 hora: llamá a la clínica al 11 4000-1200.",
  "canal_origen": "TELEFONO",
  "id_consulta": null,
  "cancelado_por": null,
  "fecha_cancelacion": null
}]
```

Cuatro campos que la pantalla necesita y conviene no olvidar:

- `puede_cancelar` + `motivo_bloqueo` → habilitan o deshabilitan los botones con su explicación.
- `canal_origen` → muestra "Registrado por la clínica".
- `cancelado_por` + `fecha_cancelacion` → muestra "Cancelado por vos el 04/08".
- `id_consulta` → habilita "Ver en el historial" en los turnos atendidos.

**Sobre la reprogramación:** liberar el horario viejo y tomar el nuevo ocurren en una misma transacción. Si la toma falla, el turno original se conserva intacto y se devuelve el mismo 409 de arriba.

**Qué hacer:** ojo con algo sutil acá. `puede_cancelar` que viene en `GET /turnos` es **solo
para pintar el botón** (mostrarlo habilitado o gris en la pantalla) — no es la validación
real. La validación de verdad pasa recién cuando se aprieta "cancelar" de verdad, en
`POST /turnos/{id}/cancelar`, chequeando la hora en ese instante exacto. Puede pasar que la
pantalla haya estado abierta un rato y para cuando el usuario aprieta el botón ya se pasó la
hora límite — en ese caso, aunque el botón se viera habilitado, el servidor lo va a rebotar con
un 409. Con reprogramar pasa algo parecido a lo del bloque anterior: liberar el horario viejo
y tomar el nuevo tienen que pasar **juntos o ninguno**. Si falla tomar el nuevo horario (por
ejemplo porque alguien se lo llevó), el turno original no se puede quedar "liberado en el
aire": tiene que seguir existiendo tal cual estaba.

---

## Cliente · Historial clínico de mi mascota
*Timeline de consultas, solo lectura, con "Ver N consultas anteriores".*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/mascotas/{id}/historial` | Solo lectura. 404 si la mascota no es del cliente. Params `?limite=` y `?offset=`. | P1 ★ |

Mismo endpoint que usa el veterinario; la respuesta cambia según el rol.

**Qué hacer:** el cliente ve el historial de su propia mascota, pero de solo lectura — no
puede tocar nada desde acá. `?limite=` y `?offset=` son para traer de a partes (por ejemplo,
10 consultas por vez) en vez de mandar años de historial de una sola vez. Ojo que este mismo
endpoint (misma URL) lo usa también el veterinario más abajo, con más información en la
respuesta — el rol de quien pregunta decide qué se devuelve.

---

## Veterinario · Agenda diaria
*Línea de tiempo de 8:00 a 18:00 con bloques proporcionales a la duración. Banner cuando la agenda cambió.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/agenda` | Turnos del veterinario. Params `?fecha=` y `?desde=` (timestamp). | P1 |

**Respuesta:**
```json
{
  "fecha": "2026-08-25",
  "consultado_el": "2026-08-25T10:20:00Z",
  "resumen": { "total": 15, "atendidos": 4, "en_curso": 1, "pendientes": 10 },
  "hay_cambios": true,
  "turnos": [{
    "id": 91, "hora_inicio": "10:00", "duracion_minutos": 30,
    "tipo": "Curación posquirúrgica",
    "mascota": { "id": 7, "nombre": "Nube", "especie": "Felino" },
    "propietario": "L. Torres",
    "estado": "CONFIRMADO",
    "estado_visual": "EN_CURSO",
    "agendado_por_administracion": false
  }]
}
```

Con `?desde=<timestamp>` el servidor responde `hay_cambios: true` si hubo altas o cancelaciones desde ese momento. **No hace falta un endpoint aparte**: el banner "La agenda cambió · Actualizar" se resuelve con esta bandera.

Los turnos cancelados no aparecen. `agendado_por_administracion` permite marcar los tipos no reservables, como la cirugía menor de Frida.

**Qué hacer:** la agenda del día del veterinario, tipo calendario, con bloques de distinto
alto según la duración de cada turno. El truco de `?desde=`: en vez de armar un endpoint
aparte tipo "hay novedades", el mismo `/agenda` recibe el timestamp de la última vez que se
consultó y responde `hay_cambios: true` si en el medio se agendó o canceló algo — así el
frontend sabe cuándo mostrar el cartel de "actualizar" sin tener que estar comparando listas
enteras.

---

## Veterinario · Pacientes
*Buscador de cualquier mascota de la clínica. Puerta de entrada a los historiales.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/pacientes` | Params `?q=`, `?alcance=mios\|clinica`, `?especie=`. | P2 |

**Respuesta:**
```json
[{
  "id": 1, "nombre": "Luna", "especie": "Canino", "raza": "Border collie", "edad": "4 a",
  "estado": "ACTIVA",
  "propietario": { "nombre": "Ana Giménez", "telefono": "..." },
  "consultas_registradas": 7,
  "ultima_atencion": { "fecha": "2026-08-12", "veterinario": "Dra. M. Álvarez", "fue_propia": true },
  "turno_hoy": { "hora": "17:30", "estado_visual": "PENDIENTE" }
}]
```

`fue_propia` produce el "por vos" frente a "por Dr. Bianchi" de la columna.

El acceso amplio es intencional: un veterinario puede cubrir a un colega. El control está en que **cada acceso queda registrado**, no en restringirlo.

**Qué hacer:** un buscador de mascotas que le permite a **cualquier** veterinario ver **cualquier**
mascota de la clínica, no solo las que atendió él. Esto es a propósito, no un descuido: en una
urgencia puede necesitar atender a un paciente que nunca vio. Por eso acá **no hay que
restringir el acceso por veterinario** — lo que sí hay que garantizar siempre es que quede
registrado en la auditoría quién miró qué mascota y cuándo.

---

## Veterinario · Historial clínico completo
*Timeline con correcciones vinculadas a su consulta original y banner de advertencia si el historial no se recuperó completo.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/mascotas/{id}/historial` | Historial completo de cualquier mascota. Param `?tipo=` para filtrar. Registra el acceso en auditoría. | P1 ★ |

**Respuesta:**
```json
{
  "mascota": { "id": 1, "nombre": "Luna", "peso_actual": 18.4, "propietario": "Ana Giménez" },
  "consistente": false,
  "recuperadas": 7,
  "esperadas": 9,
  "ultimo_intento": "2026-08-25T10:21:00Z",
  "advertencias": [
    "No se pudieron recuperar 2 de 9 consultas."
  ],
  "consultas": [
    {
      "id": null,
      "recuperada": false,
      "mensaje": "Consulta no recuperada. Existe en el registro pero no se pudo leer su contenido."
    },
    {
      "id": 41, "recuperada": true,
      "fecha": "2026-08-12", "tipo": "Consulta general",
      "veterinario": "Dra. M. Álvarez",
      "motivo": "...", "observaciones": "...", "diagnostico": "...",
      "tratamiento": "...", "recomendaciones": "...",
      "modificada_el": null,
      "edicion_vencida": true,
      "corregida": false,
      "correcciones": []
    },
    {
      "id": 33, "recuperada": true,
      "fecha": "2026-06-22", "tipo": "Vacunación",
      "veterinario": "Dra. S. Duarte",
      "tratamiento": "Vacuna polivalente lote A-2291",
      "corregida": true,
      "corregida_el": "2026-06-24",
      "correcciones": [{
        "id": 55, "fecha": "2026-06-24", "veterinario": "Dra. S. Duarte",
        "motivo_correccion": "Error de transcripción del lote.",
        "tratamiento": "Vacuna polivalente lote A-2319",
        "vigente": true
      }]
    }
  ]
}
```

**Reglas de presentación:**

- Consultas de más reciente a más antigua.
- Una consulta corregida **nunca** se devuelve sin sus correcciones. Van anidadas.
- Las consultas no recuperadas **ocupan su lugar en la lista** con `recuperada: false`. No se omiten en silencio: el hueco tiene que verse.
- Si `consistente` es `false`, la UI muestra el banner y **no presenta el historial como válido**.
- `modificada_el` → badge "Modificada el ‹fecha›". `edicion_vencida` → "Cerrada · edición vencida".

**Qué hacer:** el mismo endpoint de historial de más arriba, pero cuando lo pide un
veterinario devuelve todo el detalle clínico. La parte más importante de implementar bien es
la idea de "nunca mentir por omisión": si por algún motivo no se pudieron traer todas las
consultas que deberían existir (`recuperadas` menor a `esperadas`), **no hay que devolver el
historial como si estuviera completo** — hay que devolverlo igual, pero marcando
`consistente: false` y dejando un hueco visible donde falta algo (`recuperada: false`), en vez
de simplemente omitir esa consulta sin avisar. Es mejor mostrar "esto puede estar incompleto"
que mostrar algo incompleto disfrazado de completo.

---

## Veterinario · Registrar consulta
*Autor y fecha los asigna el sistema. Cuenta regresiva de la ventana de 24 h.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| POST | `/turnos/{id}/consulta` | Registra la atención y pasa el turno a `ATENDIDO`. **Las dos cosas en una transacción.** | P1 ★ |
| PATCH | `/consultas/{id}` | Solo el autor, dentro de 24 h. Se valida al confirmar, no al abrir. 409 si venció. | P1 ★ |
| POST | `/consultas/{id}/correccion` | Cualquier veterinario, sin límite de tiempo. Requiere `motivo_correccion`. | P1 |

**Campos:** `motivo` y `diagnostico` obligatorios. `observaciones`, `tratamiento` y `recomendaciones` opcionales.

Autor y fecha **los pone el servidor**, no vienen del cliente. Son solo lectura en el formulario.

**Respuesta de `POST /turnos/{id}/consulta`:**
```json
{
  "id_consulta": 92,
  "fecha_registro": "2026-08-25T10:35:00Z",
  "edicion_vence_el": "2026-08-26T10:35:00Z",
  "turno_estado": "ATENDIDO"
}
```
`edicion_vence_el` alimenta la cuenta regresiva.

**Sobre las correcciones:** una corrección siempre apunta a una **consulta original**, nunca a otra corrección. Si hay que corregir una corrección, se agrega otra entrada que también apunta a la original. Esa regla se valida en la aplicación.

**Qué hacer:** cuando el veterinario atiende y carga la consulta, tienen que pasar dos cosas
**a la vez o ninguna**: se guarda la consulta clínica y el turno pasa a `ATENDIDO`. Si el
servidor se cayera justo en el medio, no puede quedar guardada la consulta con el turno
todavía "pendiente" (ni viceversa) — de ahí lo de "en una transacción". Después de creada, el
propio autor la puede corregir libremente solo durante 24 horas (`PATCH`); pasado ese plazo, ya
no se edita el original, se agrega una corrección nueva enganchada a esa consulta, y esa sí la
puede hacer cualquier veterinario sin límite de tiempo (por si otro colega nota un error más
adelante). Regla importante para no romper la trazabilidad: una corrección **siempre** apunta
a la consulta original, nunca a otra corrección — si hay que corregir dos veces, las dos
correcciones cuelgan de la misma consulta original, no una de la otra.

---

## Administrador · Agenda de la clínica
*Las 3 agendas en paralelo. Panel lateral para crear un turno en nombre de un cliente que llamó.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/admin/agenda` | Las 3 agendas. Param `?fecha=`. Resumen con total de turnos. **Sin contenido clínico.** | P2 |
| POST | `/admin/turnos` | Crea turno en nombre de un cliente. Puede usar tipos **no reservables**. `canal_origen=TELEFONO` o `PRESENCIAL`. | P2 |
| POST | `/admin/turnos/{id}/cancelar` | **Sin restricción horaria**, a diferencia del cliente. | P2 |
| POST | `/admin/turnos/{id}/reprogramar` | Sin restricción horaria. Atómico igual. | P2 |

Los bloques muestran hora, mascota y tipo. **Nunca motivo, diagnóstico ni tratamiento.**

El panel lateral usa `GET /admin/clientes?q=` para el buscador, y después `GET /tipos-atencion` (sin filtrar por reservable) y `GET /disponibilidad`.

**Qué hacer:** es la versión "mostrador" de la agenda: el admin ve las 3 agendas de los
veterinarios juntas para poder ofrecer un hueco libre en cualquiera de ellos, pero solo ve
hora, mascota y tipo de atención — nunca diagnóstico ni nada clínico. Puede cargar un turno
en nombre de un cliente que llamó por teléfono, incluso con tipos de atención que un cliente
no podría reservarse solo. A diferencia del cliente, no tiene la restricción de 1 hora para
cancelar o reprogramar.

---

## Administrador · Clientes
*Listado con búsqueda y filtros. Desde acá se llega a la ficha de cada mascota.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/admin/clientes` | Params `?q=`, `?filtro=todos\|con_turnos_futuros\|con_inasistencias`, `?pagina=`. | P2 |
| GET | `/admin/clientes/{id}` | Ficha con datos de contacto, estado de cuenta y sus mascotas. | P2 |
| PATCH | `/admin/usuarios/{id}` | Edita datos de contacto. | P3 |

**Respuesta de la ficha:**
```json
{
  "id": 12, "nombre": "Diego Ferrer",
  "correo": "d.ferrer@correo.com", "telefono": "...",
  "cliente_desde": "2023-03-01",
  "turnos_totales": 9,
  "estado_cuenta": "BLOQUEADO",
  "bloqueado_hasta": "2026-08-25T08:48:00Z",
  "mascotas": [ { "id": 5, "nombre": "Frida", "especie": "Canino", "raza": "Boxer", "edad": "6 a" } ]
}
```

El listado incluye contacto y turnos, **nunca información clínica**.

**Qué hacer:** listado y ficha de clientes para uso administrativo — datos de contacto,
estado de la cuenta (activo, bloqueado por intentos fallidos, etc.) y sus mascotas. Nada
clínico entra acá, ni siquiera de forma resumida.

---

## Administrador · Ficha de mascota
*Datos administrativos y turnos. El contenido clínico aparece como estado vacío explícito.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/admin/mascotas/{id}` | Datos de la mascota y **metadatos** de sus turnos. | P2 |

**Respuesta:**
```json
{
  "id": 5, "nombre": "Frida", "especie": "Canino", "raza": "Boxer",
  "estado": "ACTIVA",
  "ultima_atencion": "2026-07-02",
  "veterinaria_habitual": "Dra. Álvarez",
  "historial_clinico": {
    "acceso": false,
    "titulo": "No tenés acceso a la información clínica",
    "mensaje": "Motivo, observaciones, diagnóstico, tratamiento y recomendaciones no están disponibles para el rol de administración.",
    "campos_visibles": ["fecha", "hora", "duracion", "tipo_atencion", "veterinario", "estado"]
  },
  "turnos": [
    { "fecha": "2026-08-25", "duracion": 45, "tipo": "Cirugía menor",
      "veterinario": "Dra. Álvarez", "estado": "CONFIRMADO" }
  ]
}
```

**Regla dura:** el contenido clínico **no se filtra en el frontend**. El servidor directamente no lo envía, ni siquiera oculto en el JSON. La restricción es intencional, no una carga pendiente — y el bloque `historial_clinico` lo dice explícitamente para que la pantalla lo comunique así.

**Qué hacer:** el admin puede ver que un turno existió y de qué tipo era, pero nunca el
diagnóstico. Esto es clave para quien lo programe: **no es que el frontend lo oculte
visualmente** — la respuesta del servidor directamente no incluye ese contenido, viene
reemplazado por un bloque `historial_clinico` que explica por qué no está disponible. Si
alguien mirara la respuesta cruda con las herramientas de desarrollador del navegador,
tampoco lo vería ahí.

---

## Administrador · Tipos de turno
*Tabla con duración, turnos futuros afectados y el interruptor "reservable por el cliente".*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/admin/tipos-atencion` | Todos, con conteo de turnos futuros de cada uno. | P2 |
| POST | `/admin/tipos-atencion` | Alta. Duración múltiplo de 15 minutos. | P2 |
| GET | `/admin/tipos-atencion/{id}/impacto` | Param `?duracion=`. Turnos futuros que se verían afectados por el cambio. | P2 |
| PATCH | `/admin/tipos-atencion/{id}` | Cambia duración o el interruptor. Requiere `confirmado: true` si hay impacto. | P2 |
| POST | `/admin/tipos-atencion/{id}/baja` | Baja lógica. No se elimina si tiene turnos asociados. | P3 |

**Respuesta de `/impacto`:**
```json
{ "duracion_actual": 30, "duracion_propuesta": 20, "turnos_afectados": 28 }
```

Produce el mensaje *"Reducir de 30 a 20 min afecta a 28 turnos ya reservados"*.

**Importante:** cambiar la duración de un tipo **no altera los turnos ya reservados**. Cada turno guarda su propia duración desde que fue creado.

**Qué hacer:** el admin mantiene el catálogo de tipos de atención (consulta general, vacuna,
cirugía...) y decide cuáles puede reservar un cliente solo y cuáles solo por teléfono o
presencial. Antes de cambiar la duración de un tipo, `/impacto` le avisa cuántos turnos ya
agendados quedarían "desalineados" con la nueva duración — pero ojo, esos turnos **no se
tocan**: cada turno ya guardó su propia duración en el momento en que se creó, así que
cambiar el tipo de atención a futuro no mueve nada de lo ya reservado.

---

## Administrador · Usuarios y veterinarios
*Tabla con filtros por rol y estado. Diálogo de advertencia con confirmación escrita.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/admin/usuarios` | Params `?rol=`, `?estado=`, `?q=`, `?pagina=`. Incluye último acceso. | P2 |
| POST | `/admin/veterinarios` | Alta con matrícula profesional (única). | P2 |
| GET | `/admin/usuarios/{id}/impacto-baja` | Turnos futuros que quedarían afectados, con mascota y propietario. | P2 |
| POST | `/admin/usuarios/{id}/deshabilitar` | Requiere `confirmado: true`. **Nada se cancela ni se reasigna automáticamente.** | P2 |
| POST | `/admin/usuarios/{id}/habilitar` | Reactiva la cuenta. | P2 |
| GET | `/admin/disponibilidad/{id_vet}` | Franjas horarias del veterinario. | P3 |
| PUT | `/admin/disponibilidad/{id_vet}` | Modifica franjas. Devuelve impacto si quedan turnos fuera. | P3 |

**Tres estados distintos** que la tabla diferencia:

| Estado | Origen | Se resuelve |
|---|---|---|
| `ACTIVO` | normal | — |
| `BLOQUEADO` | 5 intentos fallidos | Automático, a los 15 min |
| `INACTIVO` | deshabilitado por el administrador | Solo manualmente |

**Respuesta de `/impacto-baja`:**
```json
{
  "turnos_afectados": 4,
  "turnos": [
    { "fecha": "2026-08-26", "hora": "09:00", "mascota": "Luna", "propietario": "A. Giménez" }
  ],
  "advertencia": "No podrá iniciar sesión ni registrar consultas. Sus 4 turnos futuros no se cancelan automáticamente."
}
```

Al deshabilitar, los registros previos se conservan: las consultas escritas por ese veterinario siguen en los historiales **con su autoría original**.

**Qué hacer:** ojo con no confundir los tres estados de una cuenta: `BLOQUEADO` es automático
y temporal (5 intentos fallidos de login, se destraba solo a los 15 minutos), mientras que
`INACTIVO` es una decisión manual del admin y no se destraba solo. Antes de deshabilitar a
alguien, `impacto-baja` muestra qué turnos futuros lo tienen agendado, para armar el cartel de
advertencia. Y algo importante para no romper nada: **deshabilitar a un veterinario no cancela
ni reasigna sus turnos automáticamente**, eso el admin lo tiene que hacer aparte a mano si
quiere. Tampoco se le borra nada de lo que ya hizo: sus consultas pasadas siguen figurando en
los historiales con su nombre.

---

## Administrador · Registro de accesos
*Tabla paginada con filtros por rol y operación. Mezcla accesos a historial y eventos del sistema en orden cronológico.*

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/admin/auditoria` | **Unificado.** Params `?q=`, `?rol=`, `?operacion=`, `?desde=`, `?hasta=`, `?pagina=`. | P1 |

**Este endpoint consulta las dos tablas de log** (`acceso_historial` y `auditoria_sistema`) y devuelve un único listado ordenado por fecha. La pantalla mezcla eventos de ambos tipos:

```json
{
  "pagina": 1, "total_paginas": 39, "total": 967,
  "eventos": [
    { "fecha_hora": "...", "usuario": "Marcela Álvarez", "rol": "VETERINARIO",
      "mascota": "Nube", "operacion": "Registró consulta", "resultado": "PERMITIDO" },
    { "fecha_hora": "...", "usuario": "Ana Giménez", "rol": "CLIENTE",
      "mascota": "Luna", "operacion": "Intento de reserva rechazado · horario ocupado",
      "resultado": "RECHAZADO" },
    { "fecha_hora": "...", "usuario": "d.ferrer@correo.com", "rol": "CLIENTE",
      "mascota": null, "operacion": "Cuenta bloqueada · 5 intentos fallidos",
      "resultado": "BLOQUEADO" }
  ]
}
```

`mascota` puede ser `null`: los eventos de sistema (login, bloqueo, alta de usuario) no tienen una asociada.

**El registro guarda qué se hizo, nunca qué decía.** No expone contenido clínico bajo ninguna circunstancia. Y los registros **no se pueden modificar ni eliminar**: la base tiene los permisos revocados para la cuenta de la aplicación.

La consulta de esta pantalla también queda registrada.

**Qué hacer:** es la "cámara de seguridad" del sistema, y viene de combinar dos tablas de
auditoría distintas (`acceso_historial` para lo clínico, `auditoria_sistema` para logins, altas
y bajas) en un único listado ordenado por fecha, para que el admin no tenga que mirar dos
pantallas separadas. Guarda **qué acción se hizo**, nunca el contenido (por ejemplo dice
"registró consulta", no el diagnóstico en sí). Y algo que conviene tener presente desde el
diseño de la base: estos registros no se pueden borrar ni editar ni siquiera con acceso de
administrador de base de datos por accidente — el usuario con el que se conecta la aplicación
no tiene ese permiso. Hasta el hecho de mirar esta pantalla queda anotado acá mismo.

---

## Transversales

| Método | Endpoint | Descripción | Prio |
|---|---|---|---|
| GET | `/health` | Estado del servicio. | P1 |
| GET | `/notificaciones` | Notificaciones del cliente autenticado. | P1 |

**Qué hacer:** `/health` es un endpoint típico de "¿estás vivo?" para monitoreo automático, sin
lógica de negocio. `/notificaciones` trae los avisos del cliente (recordatorio de turno, aviso
de que se corrigió una consulta, etc.).

---

## Resumen

**50 endpoints únicos.** (`GET /mascotas/{id}/historial` figura dos veces, en la pantalla del cliente y en la del veterinario, pero es el mismo con respuesta según rol.)

| Prioridad | Cantidad |
|---|---|
| P1 | 22 |
| P2 | 22 |
| P3 | 6 |

Por método: 25 GET, 20 POST, 4 PATCH, 1 PUT. Ningún DELETE — coherente con la decisión de baja lógica en todo el sistema.

**En criollo:** que no haya ningún `DELETE` no es casualidad ni un olvido — es la misma idea de
"baja lógica" repetida en todo el sistema: nada se borra de la base nunca, todo se marca como
inactivo o cancelado. Así se conserva el historial completo pase lo que pase.

## Orden de trabajo sugerido, pero ni idea la verdad

**1 — que la app camine**
Login y sesión · mascotas · tipos de atención · veterinarios · disponibilidad · reservar turno · mis turnos · agenda del veterinario

**2 — el módulo clínico**
Historial de cliente y veterinario · registrar consulta · modificar dentro de 24 h · correcciones · pacientes · notificaciones · auditoría

**3 — administración**
Agenda de la clínica · turnos por teléfono · clientes y fichas · tipos de atención · usuarios · diálogos de impacto

**4 — si sobra tiempo**
Peso histórico · disponibilidad configurable · edición de contacto

---

## Cosas importantes para todo

**1. Ninguna regla de negocio se valida en el frontend.** Plazo de 1 hora, ventana de 24 horas, permisos, disponibilidad de horarios: todo se verifica en el servidor **en el momento de ejecutar la operación**, no al mostrar la pantalla. La pantalla que vio el usuario puede haber quedado vieja.

**2. El servidor no envía lo que el rol no puede ver.** No alcanza con ocultarlo en la interfaz.

**3. Toda lectura o escritura de historial clínico genera un registro de auditoría**, incluidos los accesos rechazados por falta de permisos.

**4. Nada se elimina.** Mascotas, usuarios, veterinarios y tipos de atención admiten solo baja lógica. Las consultas clínicas son inmutables pasadas las 24 horas.

**En criollo, resumiendo todo el documento:** no confíes nunca en lo que dice la pantalla ni en
lo que mandó el frontend — cada endpoint tiene que volver a chequear todo por su cuenta, como
si el pedido pudiera venir de cualquier lado (porque puede). Si un rol no debería ver algo, ese
algo directamente no se manda, no se esconde nomás con CSS. Y todo lo que toca el historial
clínico deja rastro, siempre, incluso cuando falla.
