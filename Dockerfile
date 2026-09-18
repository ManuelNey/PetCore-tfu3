FROM python:3.13-slim
# Usamos Python 3.13 porque es la version requerida en pyproject.toml

WORKDIR /app
# Establece /app como carpets de trabajo adentro del contenedor
# es el equivalente a ejecutar: cd /app

# Instala uv dentro de la imagen
# Se instala uv antes que FastAPI
RUN pip install --no-cache-dir uv==0.12.5


COPY pyproject.toml uv.lock ./
# Copia esos 2 archivos a la imagen

RUN uv sync --locked
#Instala FastAPI y demás librerías dentro de la imagen

COPY app ./app
# El primer app es la carpeta de windows, mientras que el segundo es el destino de la imagen

EXPOSE 8000
# La app escucha en el puerto 8000


CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "8000"]
# Inicia FastAPI cuando se ejecuta el contenedor
# uv+run ejecuta el entorno de uv
# fastapi run inicia FastAPI
# app/main.py es donde está el código
# --port 8000 hace que el servidor escuche en el puerto 8000