#!/usr/bin/env bash
# Demo 1: Health Endpoint Monitoring
# Correr desde la raiz del repo (donde esta compose.yaml).

set -u
BASE="http://localhost:8000"

step() {
  echo ""
  echo "=================================================================="
  echo "  $1"
  echo "=================================================================="
  read -p "  (Enter para ejecutar) " _
}

step "1) Estado inicial: las dos replicas y la base deben estar healthy"
docker compose ps

step "2) Corto la base de verdad (docker compose stop db)"
docker compose stop db

step "3) GET /health ahora -> debe dar 503, porque chequea la conexion real"
curl -s -w "\nstatus: %{http_code}\n" "$BASE/health"

step "4) Espero a que Docker marque las replicas como unhealthy (3 chequeos de 10s, ~30-40s)"
until [ "$(docker compose ps server | grep -c unhealthy)" -ge 1 ]; do
  sleep 3
done
docker compose ps

step "5) Levanto la base de nuevo (docker compose start db)"
docker compose start db

step "6) Espero a que vuelva a responder OK"
until curl -s "$BASE/health" | grep -q '"status":"ok"'; do
  sleep 2
done
curl -s -w "\nstatus: %{http_code}\n" "$BASE/health"

step "7) Espero a que docker compose ps vuelva a mostrar todo healthy, sin haber reiniciado nada"
until [ "$(docker compose ps server | grep -c unhealthy)" -eq 0 ]; do
  sleep 3
done
docker compose ps

echo ""
echo "Demo de Health Endpoint Monitoring terminada."
