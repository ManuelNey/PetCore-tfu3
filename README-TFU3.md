# Pet-Core — TFU3: Soluciones de Arquitectura

Este documento va punto por punto de lo que pide la letra de la TFU3, indicando si Pet-Core
ya lo cumple (y por qué) o qué falta construir.

## Índice

1. [Componentes e interfaces](#1-componentes-e-interfaces)
2. [Escalabilidad horizontal o vertical](#2-escalabilidad-horizontal-o-vertical)
3. [Contenedores o máquinas virtuales](#3-contenedores-o-máquinas-virtuales)
4. [ACID o BASE](#4-acid-o-base)
5. [Servicios sin estado](#5-servicios-sin-estado)
6. [Checklist general — qué falta para entregar](#6-checklist-general--qué-falta-para-entregar)

---

## 1. Componentes e interfaces

**Estado: cumplido en el código.** Falta el diagrama UML formal (documento aparte).

Cada carpeta de `app/` es un componente con responsabilidad de negocio propia: `turnos`,
`historial`, `disponibilidad`, `pacientes`, `veterinarios`, `agenda`, `especies`,
`tipos_atencion`. Además hay un componente compartido, `Auth`/`Middleware`, que no es parte
del dominio de negocio sino que resuelve autenticación/autorización para todos los demás
(`requerir_rol`).

- La **interfaz expuesta** de un componente es lo que ofrece su `controller.py` hacia afuera
  (sus endpoints REST).
- La **interfaz consumida** es cuando un componente usa el `service` de otro en vez de tocar
  la base de datos directamente.

### Ejemplo real del código

`app/turnos/controller.py` (línea 64), cuando `Turnos` necesita saber la disponibilidad de
un veterinario, no le pega directo a la tabla de disponibilidad — usa la interfaz pública
del componente `Disponibilidad`:

```python
disponibilidad = DisponibilidadService(DisponibilidadRepository(session)).calcular(...)
```

Bosquejo de esa relación (no es el diagrama completo, solo una porción a modo de ejemplo):

```
┌─────────────┐  consume calcular()    ┌────────────────────┐
│   Turnos    │ ──────────────────────▶│   Disponibilidad    │
│             │                         │                    │
│ expone:     │                         │ expone:            │
│ POST /turnos│                         │ GET /disponibilidad│
│ reservar/   │                         │ calcular()         │
│ cancelar    │                         └────────────────────┘
└─────┬───────┘
      │ requiere rol vía
      ▼
┌──────────────┐
│ Auth /        │  (componente compartido, no de dominio)
│ Middleware    │  expone: requerir_rol(*roles)
└──────────────┘
```

### Pendiente

- [ ] Diagrama UML de componentes completo (todos los módulos, no solo este ejemplo).
- [ ] Confirmar que no hay ningún otro componente accediendo por atrás a la tabla de otro
      (saltándose la interfaz de servicio) — si aparece un caso así, corregirlo o
      documentarlo como deuda conocida.

---

## 2. Escalabilidad horizontal o vertical

**Estado: cumplido en el código.** Reciclado de la rama `andis` original.

- **Escalabilidad horizontal**: agregar más instancias del mismo componente y repartir la
  carga entre ellas (más réplicas, no más recursos por réplica).
- **Escalabilidad vertical**: darle más recursos (CPU/RAM) a la misma instancia.

Pet-Core usa **horizontal**: 2 réplicas del servicio `server` (FastAPI) detrás de un
balanceador nginx, en vez de una única instancia más grande. Tiene sentido para este caso
porque las réplicas son *stateless* (ver punto 5) — no hay coordinación de estado que
complique sumar instancias, y horizontal además da tolerancia a fallas (si una réplica cae,
el balanceador sigue mandando tráfico a la otra).

### Piezas del código

- `nginx/andis.conf`: define el `upstream api_backend` con `server:8000`, y reglas de
  reintento entre réplicas si una falla (`proxy_next_upstream`).
- `compose.yaml`: servicio `balanceador` (nginx:alpine) que escucha en el puerto público
  8000 y reenvía a las réplicas internas de `server`.
- `scripts/andis-up.ps1`: levanta todo con `docker compose up --scale server=2`.
- `app/demo/controller.py` → `GET /demo/instancia`: devuelve `socket.gethostname()`, para
  probar en vivo que requests seguidas responden desde contenedores distintos.

### Pendiente

- [ ] Nada de código — está listo. Solo falta ejecutar la demo en vivo (pegarle varias
      veces a `/demo/instancia` y mostrar hostnames distintos) para el video/presentación.

---

## 3. Contenedores o máquinas virtuales

**Estado: cumplido.** La elección del proyecto es **contenedores** (Docker), desde el
arranque.

- **Contenedores**: comparten el kernel del SO host, son livianos, arrancan en segundos, y
  la imagen empaqueta la app + sus dependencias de forma reproducible (capas de Docker).
- **Máquinas virtuales**: cada una lleva su propio SO completo, son más pesadas, tardan más
  en arrancar, pero dan aislamiento más fuerte (kernel separado).

### Piezas del código

- `Dockerfile`: build de la imagen de FastAPI.
- `compose.yaml`: orquesta `frontend`, `server` (×2 en la demo de escalabilidad),
  `balanceador`, `db`.
- Poder escalar con `docker compose up --scale server=2` en un solo comando es una ventaja
  directa de usar contenedores — con VMs eso sería mucho más manual.

### Impacto de usar la opción no elegida (VMs)

Si tuviéramos que reemplazar los contenedores por VMs, perderíamos la velocidad de arranque
y el escalado con un solo comando (`--scale`); cada réplica de la API pasaría a ser una VM
completa que hay que provisionar, instalar Python/dependencias y arrancar manualmente (o con
un script de infraestructura aparte, tipo `.azcli`), lo que hace mucho más lento y costoso
escalar horizontalmente. También se pierde la garantía de "funciona igual en cualquier
lado" que da la imagen versionada — en VMs hay que asegurarse a mano de que el ambiente sea
idéntico entre instancias.

### Pendiente

- [ ] Nada — está listo.

---

## 4. ACID o BASE

**Estado: el comportamiento ya existe en el código, pero falta una demo que lo muestre en
vivo.**

- **ACID**: prioriza que los datos siempre queden consistentes. Una operación que toca
  varias tablas se aplica completa o no se aplica nada.
- **BASE**: prioriza que el sistema esté siempre disponible, aceptando que por un tiempo
  corto los datos puedan no estar del todo actualizados.

Pet-Core usa **ACID**, gracias a las transacciones de Postgres. El ejemplo real que ya
existe en el código es cuando un veterinario registra una consulta: se guarda la consulta
clínica y se actualiza el estado del turno a la vez, como una sola operación. Si algo falla
en el medio, no queda ni la consulta guardada a medias ni el turno con un estado
inconsistente — o se aplican los dos cambios, o no se aplica ninguno.

### Qué falta

Falta armar una demostración concreta de esto: forzar a propósito que esa operación falle a
mitad de camino, y después mostrar consultando la base que todo quedó exactamente como
estaba antes — ningún cambio a medias. Esa es la forma de probar, en vivo y no solo de
palabra, que el sistema realmente se comporta de manera atómica.

### Pendiente

- [ ] Armar la forma de forzar la falla a propósito (un endpoint o script de demo).
- [ ] Armar el paso que muestre, después de la falla, que la base quedó sin cambios a
      medias.

---

## 5. Servicios sin estado

**Estado: cumplido en general, con un detalle para explicar en la demo.**

Un servicio "sin estado" es uno que no se acuerda de nada entre un pedido y el siguiente:
todo lo que hay que recordar queda guardado en la base, no en la memoria del proceso. Eso es
lo que permite que no importe a cuál réplica te toque atenderte — la respuesta va a ser la
misma siempre.

Pet-Core cumple esto en general: nada del código de negocio guarda datos de un usuario en
memoria mientras atiende otros pedidos. Hay un detalle a tener en cuenta igual: existe una
tarea que corre sola cada tanto y marca como "no asistió" los turnos vencidos. Con una sola
réplica no hay problema, pero con dos réplicas corriendo a la vez (como en la demo de
escalabilidad), esa tarea se dispara en las dos por separado. No genera ningún dato
incorrecto porque repetir esa operación no cambia el resultado, pero es un punto para
mencionar y explicar en la demo en vez de dejarlo pasar.

### Cómo mostrarlo

Con las dos réplicas levantadas, pegarle varias veces seguidas a un mismo pedido y mostrar
que la respuesta es siempre la misma, sin importar cuál de las dos réplicas haya atendido
ese pedido en particular. Eso demuestra que no hay nada guardado "solo en una" de las
réplicas.

### Pendiente

- [ ] Decidir si esa tarea duplicada se deja así y se explica como algo aceptable, o si se
      ajusta para que corra en un solo lugar.
- [ ] Preparar el paso a paso de la demo (a qué pedido pegarle y qué mostrar).

---

## 6. Checklist general — qué falta para entregar

Esto junta todo lo pendiente de las dos partes de la TFU3, para no perder nada de vista.

### Parte 1 — Documento

- [ ] Diagrama UML de componentes completo (todos los módulos, no solo el ejemplo de
      `Turnos`/`Disponibilidad` de este archivo).
- [ ] Redactar la justificación de la partición de primer nivel (por qué se dividió por
      dominio de negocio y no por otro criterio) — la idea ya está charlada, falta pasarla
      en limpio al documento final.
- [ ] Redactar cómo fue el proceso para encontrar los componentes (a partir de los casos de
      uso de TFU1/TFU2).
- [ ] Pasar en limpio al documento final el análisis de contenedores vs. VMs (ya está
      redactado en la sección 3 de este archivo, solo falta trasladarlo).
- [ ] Pasar en limpio al documento final el análisis de ACID vs. BASE (ya está redactado en
      la sección 4 de este archivo, solo falta trasladarlo).

### Parte 2 — Código y demo

- [ ] Código de la app: **listo** (Pet-Core, sin cambios estructurales necesarios).
- [ ] `compose.yaml` para desplegar: **listo**.
- [ ] Script/demo de escalabilidad horizontal: **listo** (`andis-up.ps1` +
      `/demo/instancia`), solo falta ejecutarlo para la presentación.
- [ ] Script/demo de contenedores: **listo**, se muestra con el mismo `compose.yaml`.
- [ ] Script/demo de componentes e interfaces: falta armar cómo se va a mostrar en vivo
      (señalar en Postman el flujo `Turnos` → `Disponibilidad`, por ejemplo).
- [ ] Script/demo de ACID: **falta construir** — forzar una falla a mitad de
      `registrar_consulta` y mostrar que no queda nada a medias (ver sección 4).
- [ ] Script/demo de servicios sin estado: **falta construir** — mostrar que la respuesta no
      depende de a qué réplica te toque (ver sección 5).
- [ ] Decisión sobre la tarea periódica duplicada entre réplicas (ver sección 5): dejarla y
      explicarla, o corregirla.
- [ ] Actualizar el `README.md` principal de la rama (hoy describe la demo de TFU2:
      disponibilidad + seguridad) para que hable de la demo de TFU3.
