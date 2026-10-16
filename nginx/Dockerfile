FROM nginx:alpine

# Certificado autofirmado SOLO para desarrollo local. Se genera al construir la
# imagen, así no hay que crear ni guardar ninguna clave en el repositorio.
RUN apk add --no-cache openssl \
 && mkdir -p /etc/nginx/certs \
 && openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
      -keyout /etc/nginx/certs/server.key \
      -out /etc/nginx/certs/server.crt \
      -subj "/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"