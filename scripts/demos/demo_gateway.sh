#!/usr/bin/env bash
# Demo 2: Gateway Offloading
# Correr desde la raiz del repo.

set -u
BASE="http://localhost:8000"
BASE_TLS="https://localhost:8443"

step() {
  echo ""
  echo "=================================================================="
  echo "  $1"
  echo "=================================================================="
  read -p "  (Enter para ejecutar) " _
}

step "1) Rafaga de 35 POST /auth/login seguidos -> el gateway corta con 429 despues del cupo"
for i in $(seq 1 35); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"correo":"x@x.com","contrasena":"mala"}')
  printf "%s " "$code"
done
echo ""

step "2) GET /health por HTTPS (puerto 8443) -> el gateway termina TLS y agrega headers de seguridad"
curl -sk -D - -o /dev/null "$BASE_TLS/health"

step "3) El mismo pedido por HTTP (puerto 8000) -> los mismos headers, Nginx los agrega sin importar el puerto"
curl -s -D - -o /dev/null "$BASE/health"

echo ""
echo "Demo de Gateway Offloading terminada."
