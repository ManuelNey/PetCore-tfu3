$ErrorActionPreference = "Stop"

Write-Host "Construyendo y levantando PostgreSQL y dos replicas de la API..."

docker compose up --build -d --scale server=2 db server

if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron levantar PostgreSQL y las replicas de la API."
}

Write-Host "Actualizando el balanceador..."

docker compose up -d --no-deps --force-recreate balanceador

if ($LASTEXITCODE -ne 0) {
    throw "No se pudo iniciar el balanceador."
}

Write-Host ""
Write-Host "API iniciada con dos replicas."
Write-Host "API: http://localhost:8000"
Write-Host "Documentación: http://localhost:8000/docs"
Write-Host ""
Write-Host "Contenedores utilizados por la demo:"
docker compose ps db server balanceador
