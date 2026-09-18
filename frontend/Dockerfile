FROM node:22-alpine
# Imagen liviana de Node para correr Vite en modo desarrollo

WORKDIR /app
# Establece /app como carpeta de trabajo adentro del contenedor

COPY package.json package-lock.json ./
# Copia los manifiestos de dependencias primero para aprovechar la cache de Docker

RUN npm ci
# Instala las dependencias exactas del lockfile

COPY . .
# Copia el resto del código del frontend a la imagen

EXPOSE 5173
# Vite escucha en el puerto 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
# Inicia el servidor de desarrollo de Vite
# --host 0.0.0.0 permite acceder desde fuera del contenedor
