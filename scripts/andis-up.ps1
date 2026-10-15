$ErrorActionPreference = "Stop"

Write-Host "Construyendo y levantando PostgreSQL, Redis y dos replicas de la API..."

docker compose up --build -d --scale server=2 db redis server

if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron levantar PostgreSQL, Redis y las replicas de la API."
}

Write-Host "Actualizando el balanceador..."

docker compose up -d --no-deps --force-recreate balanceador

if ($LASTEXITCODE -ne 0) {
    throw "No se pudo iniciar el balanceador."
}

Write-Host ""
Write-Host "API iniciada con dos replicas y cache Redis."
Write-Host "API: http://localhost:8000"
Write-Host "Documentacion: http://localhost:8000/docs"
Write-Host ""

Write-Host "Comprobando Redis..."

docker compose exec -T redis redis-cli ping

if ($LASTEXITCODE -ne 0) {
    throw "Redis no esta respondiendo."
}

Write-Host ""
Write-Host "Contenedores utilizados por la demo:"

docker compose ps db redis server balanceador