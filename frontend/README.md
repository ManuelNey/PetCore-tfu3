# Pet-Core · Frontend

Interfaz web de la Clínica Veterinaria. Es el esqueleto de navegación (v1 / Blue): rutas, layouts por rol y las primeras pantallas mockeadas (Mis mascotas y Reservar turno). Todavía no hay conexión a ningún backend — todo lo que se ve es UI con datos de ejemplo hardcodeados.


## Cómo correrlo

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # build de producción a dist/
npm run lint       # oxlint
```

También se puede levantar con Docker desde la raíz del repo:

```bash
docker compose up frontend
```

## Rol simulado (todavía no hay login real)

No hay backend ni autenticación conectada. El rol de la sesión se simula con una constante en `src/app/rolActual.js`:

```js
export const ROL_ACTUAL = 'cliente' // o 'veterinario'
```

Cambiar ese valor a mano alterna qué ve el header y qué rutas quedan habilitadas (`RoleGuard` redirige si el rol no coincide con la sección).

## Estructura de carpetas

```
src/
  app/
    App.jsx           Router raíz (BrowserRouter + AppRoutes)
    rolActual.js       Constante de rol simulado + nombre de usuario

  layouts/
    AppLayout.jsx           Shell general: Header + <Outlet/>
    ClienteLayout.jsx        Contenedor de las rutas del rol cliente
    VeterinarioLayout.jsx    Contenedor de las rutas del rol veterinario

  components/
    common/              Reutilizables por cualquier pantalla:
      Boton.jsx            Botón primario/secundario (también renderiza <Link>)
      Badge.jsx             Pill de estado (activa/inactiva)
      Tarjeta.jsx            Panel blanco redondeado base
      TarjetaSeleccion.jsx    Fila seleccionable (mascota, tipo de atención, veterinario)
      Stepper.jsx             Indicador de pasos (1, 2, 3...) para flujos de varios pasos
      PaginaPlaceholder.jsx    Título + descripción para pantallas sin implementar
      botones.css              Tokens de .boton/.badge/.tarjeta compartidos
    layout/
      Header.jsx / Header.css   Header fijo, responsive (hamburguesa en mobile)
      NavLink.jsx                Wrapper de NavLink de router con clase "activo"
      RoleGuard.jsx               Redirige si el rol simulado no coincide con la sección

  features/                Una carpeta por dominio, cada una con sus pages/
                            y, si hace falta, components/ y data/ propios.
    auth/pages/             LoginPage, RegistroPage (UI de formulario, sin submit real)
    mascotas/
      pages/ListaMascotasPage.jsx   Grid de mascotas mockeadas + alta mockeada
      components/                   MascotaCard, FormularioMascota
      data/mascotasMock.js           Datos de ejemplo
    turnos/
      pages/
        MisTurnosPage.jsx            Placeholder
        DetalleTurnoPage.jsx         Placeholder
        ReservarTurnoPage.jsx        Flujo de reserva de 4 pasos (mockeado)
      components/                   PasoMascota, PasoTipoAtencion, PasoVeterinario,
                                      PasoHorario, PasoConfirmar
      data/reservaMock.js            Tipos de atención, veterinarios, horarios de ejemplo
    historial/pages/         HistorialMascotaPage (placeholder)
    agenda/pages/             AgendaDiariaPage (placeholder)

  routes/
    index.jsx              Definición central de todas las rutas (única fuente de verdad)
```

## Rutas

| Ruta | Pantalla | Rol | Estado |
|---|---|---|---|
| `/login` | LoginPage | público | UI completa, sin lógica |
| `/registro` | RegistroPage | público | UI completa, sin lógica |
| `/mascotas` | ListaMascotasPage | cliente | Mockeada (listar, agregar) |
| `/turnos` | MisTurnosPage | cliente | Placeholder |
| `/turnos/nuevo` | ReservarTurnoPage | cliente | Mockeada (flujo de 4 pasos) |
| `/turnos/:id` | DetalleTurnoPage | cliente | Placeholder |
| `/turnos/:id/historial` | HistorialMascotaPage | cliente | Placeholder |
| `/agenda` | AgendaDiariaPage | veterinario | Placeholder |
| `/` | — | — | Redirige a `/mascotas` o `/agenda` según `ROL_ACTUAL` |

`RoleGuard` (en `components/layout/`) protege las rutas de cliente y veterinario: si `ROL_ACTUAL` no coincide con la sección, redirige a `/`.

## Datos mockeados

Todos los datos que se ven (mascotas, tipos de atención, veterinarios, horarios) están hardcodeados en archivos `data/*Mock.js` de cada feature, así se puede ir probando la navegación y las pantallas ya mismo. La idea es que, a medida que se implementen los endpoints del backend, se vayan reemplazando estos mocks por los datos reales.

Mis turnos, Detalle de turno, Historial y Agenda diaria todavía son placeholders (solo un título), falta construirlas.

## Convenciones

- Componentes, variables y archivos de dominio en español (`Mascota`, `Turno`, `Veterinario`); lo propio del framework en inglés (`Layout`, `Page`, `Provider`).
- Cada feature tiene sus propios `pages/`, `components/` y `data/`; lo que se reutiliza entre features vive en `components/common/`.
- Sin sobre-ingeniería: nada de servicios, abstracciones de estado global ni preparación para una API que todavía no existe.
