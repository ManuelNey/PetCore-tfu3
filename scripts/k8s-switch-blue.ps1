Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$namespace = "clinica-veterinaria"

Write-Host "Cambiando la API a Blue..."

minikube kubectl -- set selector service/api "app=clinica-api,version=blue" --namespace=$namespace

if ($LASTEXITCODE -ne 0) {
    throw "No se pudo cambiar la API a Blue."
}

Write-Host "Cambiando el frontend a Blue..."

minikube kubectl -- set selector service/frontend "app=clinica-frontend,version=blue" --namespace=$namespace

if ($LASTEXITCODE -ne 0) {
    throw "No se pudo cambiar el frontend a Blue."
}

$apiVersion = minikube kubectl -- get service api --namespace=$namespace -o "jsonpath={.spec.selector.version}"
$frontendVersion = minikube kubectl -- get service frontend --namespace=$namespace -o "jsonpath={.spec.selector.version}"

Write-Host ""
Write-Host "Rollback terminado."
Write-Host "Version de la API: $apiVersion"
Write-Host "Version del frontend: $frontendVersion"