import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database import FALLAR_PROXIMAS_CONEXIONES, ULTIMO_INTENTO_CONEXION
from app.Middleware.middleware import JWTMiddleware, obtener_usuario_actual
from app.turnos.tareas_programadas import ejecutar_tarea_periodica
from app.Auth.login.controller import router as login_router
from app.Auth.me.controller import router as me_router
from app.Auth.Register.clients.controller import router as register_client_router
from app.Mascotas.controller import router as mascotas_router
from app.tipos_atencion.controller import (
    router as tipos_atencion_router,
)
from app.veterinarios.controller import router as veterinarios_router
from app.turnos.controller import router as turnos_router
from app.especies.controller import router as especies_router
from app.disponibilidad.controller import router as disponibilidad_router
from app.agenda.controller import router as agenda_router
from app.historial.controller import router as historial_router
from app.pacientes.controller import router as pacientes_router
from app.demo.controller import router as demo_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Marca turnos vencidos como NO_ASISTIO en segundo plano mientras la API esté activa.
    tarea = asyncio.create_task(ejecutar_tarea_periodica())

    yield

    tarea.cancel()


app = FastAPI(
    title="Pet-Core API",
    lifespan=lifespan,
)

# Permite que el frontend (Vite, en desarrollo) llame a la API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(JWTMiddleware)

app.include_router(login_router)
app.include_router(register_client_router)
app.include_router(me_router)
app.include_router(tipos_atencion_router)
app.include_router(mascotas_router)
app.include_router(veterinarios_router)
app.include_router(turnos_router)
app.include_router(especies_router)
app.include_router(disponibilidad_router)
app.include_router(agenda_router)
app.include_router(historial_router)
app.include_router(pacientes_router)
app.include_router(demo_router)

@app.get("/")
def hello():
    return "Hello, Docker!"

#Verifica que la API esté funcionando correctamente.
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# Solo para demostrar los reintentos de conexión a la base (ver app/database.py).
@app.post("/debug/simular-falla-conexion")
def simular_falla_conexion(
    veces: int = 2,
    _usuario: dict = Depends(obtener_usuario_actual),
) -> dict:
    FALLAR_PROXIMAS_CONEXIONES["cantidad"] = veces
    return {"mensaje": f"Las próximas {veces} conexiones van a fallar"}

# Datos del último intento de conexión a la base (ver app/database.py).
@app.get("/debug/ultimo-intento-conexion")
def ultimo_intento_conexion(
    _usuario: dict = Depends(obtener_usuario_actual),
) -> dict:
    return ULTIMO_INTENTO_CONEXION
