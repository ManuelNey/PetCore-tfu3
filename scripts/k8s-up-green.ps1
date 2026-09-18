Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Confirm-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Step
    )

    if ($LASTEXITCODE -ne 0) {
        throw "Fallo el paso: $Step. Codigo de salida: $LASTEXITCODE"
    }
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$namespace = "clinica-veterinaria"

$requiredFiles = @(
    "k8s\api-green-deployment.yaml",
    "k8s\frontend-green-deployment.yaml",
    "frontend\Dockerfile.k8s"
)

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $relativePath

    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        throw "Falta el archivo requerido: $relativePath"
    }
}

Push-Location -LiteralPath $projectRoot

try {
    Write-Host "[1/7] Comprobando Docker Desktop..."

    docker info --format "{{.ServerVersion}}" | Out-Null
    Confirm-NativeCommand -Step "comprobar Docker Desktop"

    Write-Host "[2/7] Iniciando Minikube..."

    minikube start --driver=docker
    Confirm-NativeCommand -Step "iniciar Minikube"

    Write-Host "[3/7] Comprobando que Blue este desplegado..."

    minikube kubectl -- get deployment/api-blue deployment/frontend-blue statefulset/postgres service/api service/frontend --namespace=$namespace
    Confirm-NativeCommand -Step "comprobar el despliegue Blue"

    Write-Host "Esperando que Blue y PostgreSQL esten preparados..."

    minikube kubectl -- rollout status deployment/api-blue --namespace=$namespace --timeout=180s
    Confirm-NativeCommand -Step "esperar FastAPI Blue"

    minikube kubectl -- rollout status deployment/frontend-blue --namespace=$namespace --timeout=180s
    Confirm-NativeCommand -Step "esperar el frontend Blue"

    minikube kubectl -- rollout status statefulset/postgres --namespace=$namespace --timeout=180s
    Confirm-NativeCommand -Step "esperar PostgreSQL"

    Write-Host "[4/7] Manteniendo el trafico en Blue durante la actualizacion..."

    minikube kubectl -- set selector service/api "app=clinica-api,version=blue" --namespace=$namespace
    Confirm-NativeCommand -Step "dirigir la API a Blue"

    minikube kubectl -- set selector service/frontend "app=clinica-frontend,version=blue" --namespace=$namespace
    Confirm-NativeCommand -Step "dirigir el frontend a Blue"

    Write-Host "[5/7] Construyendo las imagenes Green v2..."

    minikube image build -t clinica-veterinaria:v2 .
    Confirm-NativeCommand -Step "construir FastAPI Green v2"

    minikube image build -t clinica-frontend:v2 -f Dockerfile.k8s frontend
    Confirm-NativeCommand -Step "construir el frontend Green v2"

    Write-Host "[6/7] Creando o actualizando los Deployments Green..."

    minikube kubectl -- apply -f k8s\api-green-deployment.yaml -f k8s\frontend-green-deployment.yaml
    Confirm-NativeCommand -Step "aplicar los Deployments Green"

    minikube kubectl -- rollout restart deployment/api-green --namespace=$namespace
    Confirm-NativeCommand -Step "reiniciar FastAPI Green"

    minikube kubectl -- rollout restart deployment/frontend-green --namespace=$namespace
    Confirm-NativeCommand -Step "reiniciar el frontend Green"

    minikube kubectl -- rollout status deployment/api-green --namespace=$namespace --timeout=180s
    Confirm-NativeCommand -Step "esperar FastAPI Green"

    minikube kubectl -- rollout status deployment/frontend-green --namespace=$namespace --timeout=180s
    Confirm-NativeCommand -Step "esperar el frontend Green"

    Write-Host "[7/7] Estado final..."

    minikube kubectl -- get pods -L version --namespace=$namespace
    Confirm-NativeCommand -Step "consultar los Pods"

    $apiVersion = minikube kubectl -- get service api --namespace=$namespace -o "jsonpath={.spec.selector.version}"
    $frontendVersion = minikube kubectl -- get service frontend --namespace=$namespace -o "jsonpath={.spec.selector.version}"

    Write-Host ""
    Write-Host "Green quedo desplegado, pero el trafico sigue en Blue."
    Write-Host "Version seleccionada por la API: $apiVersion"
    Write-Host "Version seleccionada por el frontend: $frontendVersion"
    Write-Host ""
    Write-Host "Para pasar el trafico a Green ejecuta:"
    Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\k8s-switch-green.ps1"
}
finally {
    Pop-Location
}