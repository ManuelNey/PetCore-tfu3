Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Este script construye exclusivamente la version Blue v1.
$currentBranch = git branch --show-current

if ($LASTEXITCODE -ne 0) {
    throw "No se pudo comprobar la rama actual de Git."
}

if ($currentBranch -ne "blue") {
    throw "Este script debe ejecutarse desde la rama blue. Rama actual: $currentBranch. Para Green utiliza scripts\k8s-up-green.ps1."
}

# Detiene el script cuando un programa externo devuelve un error
function Confirm-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Step
    )

    if ($LASTEXITCODE -ne 0) {
        throw "Fallo el paso: $Step. Codigo de salida: $LASTEXITCODE"
    }
}

# Permite ejecutar el script desde cualquier carpeta
$projectRoot = Split-Path -Parent $PSScriptRoot
$passwordFile = Join-Path $projectRoot "db\password.txt"
$jwtSecretFile = Join-Path $projectRoot "db\jwt-secret.txt"

# Archivos necesarios para construir y levantar el proyecto.
$requiredFiles = @(
    "k8s\namespace.yaml",
    "k8s\postgres-service.yaml",
    "k8s\postgres-statefulset.yaml",
    "k8s\api-blue-deployment.yaml",
    "k8s\api-service.yaml",
    "k8s\frontend-blue-deployment.yaml",
    "k8s\frontend-service.yaml",
    "frontend\Dockerfile.k8s",
    "frontend\nginx.conf",
    "frontend\.dockerignore",
    "frontend\package.json",
    "frontend\package-lock.json",
    "db\init\01_schema.sql",
    "db\init\02_permisos.sql",
    "db\init\03_excepcion_disponibilidad.sql",
    "db\init\04_datos_prueba.sql"
)

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker no esta instalado o no esta disponible en PATH."
}

if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    throw "Minikube no esta instalado o no esta disponible en PATH."
}

if (-not (Test-Path -LiteralPath $passwordFile -PathType Leaf)) {
    throw "No existe db\password.txt. Crealo antes de ejecutar este script."
}

if ((Get-Item -LiteralPath $passwordFile).Length -eq 0) {
    throw "El archivo db\password.txt esta vacio."
}

if (-not (Test-Path -LiteralPath $jwtSecretFile -PathType Leaf)) {
    throw "No existe db\jwt-secret.txt. Crealo antes de ejecutar este script."
}

if ((Get-Item -LiteralPath $jwtSecretFile).Length -lt 32) {
    throw "La clave de db\jwt-secret.txt debe tener al menos 32 caracteres."
}

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $relativePath

    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        throw "Falta el archivo requerido: $relativePath"
    }
}

Push-Location -LiteralPath $projectRoot

try {
    Write-Host "[1/9] Comprobando Docker Desktop..."
    docker info --format "{{.ServerVersion}}" | Out-Null
    Confirm-NativeCommand -Step "comprobar Docker Desktop"

    Write-Host "[2/9] Iniciando Minikube..."
    minikube start --driver=docker
    Confirm-NativeCommand -Step "iniciar Minikube"

    Write-Host "[3/9] Construyendo las imagenes Blue v1 dentro de Minikube..."
    minikube image build -t clinica-veterinaria:v1 .
    Confirm-NativeCommand -Step "construir la imagen Blue de FastAPI"

    minikube image build -t clinica-frontend:v1 -f Dockerfile.k8s frontend
    Confirm-NativeCommand -Step "construir la imagen Blue del frontend"

    Write-Host "[4/9] Creando el namespace..."
    minikube kubectl -- apply -f k8s\namespace.yaml
    Confirm-NativeCommand -Step "crear el namespace"

    Write-Host "[5/9] Creando o actualizando los Secrets..."
    # dry-run genera el YAML sin guardar el Secret; apply lo crea o actualiza
    $secretManifest = minikube kubectl -- create secret generic postgres-secret --from-file=db-password=db/password.txt --namespace=clinica-veterinaria --dry-run=client -o yaml
    Confirm-NativeCommand -Step "generar el Secret de PostgreSQL"
    $secretManifest | minikube kubectl -- apply -f -
    Confirm-NativeCommand -Step "aplicar el Secret de PostgreSQL"

    $jwtSecretManifest = minikube kubectl -- create secret generic jwt-secret --from-file=jwt-secret=db/jwt-secret.txt --namespace=clinica-veterinaria --dry-run=client -o yaml
    Confirm-NativeCommand -Step "generar el Secret JWT"
    $jwtSecretManifest | minikube kubectl -- apply -f -
    Confirm-NativeCommand -Step "aplicar el Secret JWT"

    Write-Host "[6/9] Creando o actualizando el ConfigMap con los SQL..."
    # Se usa el mismo mecanismo para que el comando pueda repetirse
    $configMapManifest = minikube kubectl -- create configmap postgres-init --from-file=db/init --namespace=clinica-veterinaria --dry-run=client -o yaml
    Confirm-NativeCommand -Step "generar el ConfigMap de PostgreSQL"
    $configMapManifest | minikube kubectl -- apply -f -
    Confirm-NativeCommand -Step "aplicar el ConfigMap de PostgreSQL"

    Write-Host "[7/9] Aplicando los manifiestos de Kubernetes..."
    # kubectl puede aplicar todos los YAML de una carpeta en un solo comando
    minikube kubectl -- apply -f k8s
    Confirm-NativeCommand -Step "aplicar los manifiestos de Kubernetes"

    Write-Host "[8/9] Reiniciando FastAPI y el frontend para utilizar las imagenes recien construidas..."
    minikube kubectl -- rollout restart deployment/api-blue --namespace=clinica-veterinaria
    Confirm-NativeCommand -Step "reiniciar el Deployment Blue"

    minikube kubectl -- rollout restart deployment/frontend-blue --namespace=clinica-veterinaria
    Confirm-NativeCommand -Step "reiniciar el Deployment Blue del frontend"

    Write-Host "Esperando a PostgreSQL..."
    minikube kubectl -- rollout status statefulset/postgres --namespace=clinica-veterinaria --timeout=180s
    Confirm-NativeCommand -Step "esperar a PostgreSQL"

    Write-Host "Esperando a FastAPI Blue..."
    minikube kubectl -- rollout status deployment/api-blue --namespace=clinica-veterinaria --timeout=180s
    Confirm-NativeCommand -Step "esperar a FastAPI Blue"

    Write-Host "Esperando al frontend Blue..."
    minikube kubectl -- rollout status deployment/frontend-blue --namespace=clinica-veterinaria --timeout=180s
    Confirm-NativeCommand -Step "esperar al frontend Blue"

    Write-Host "[9/9] Estado final de los recursos:"
    minikube kubectl -- get all,pvc,configmap,secret --namespace=clinica-veterinaria
    Confirm-NativeCommand -Step "consultar el estado final"

    Write-Host ""
    Write-Host "Kubernetes quedo preparado. Para obtener la URL del frontend ejecuta:"
    Write-Host "minikube service frontend --namespace=clinica-veterinaria --url"
    Write-Host ""
    Write-Host "Para obtener la URL directa de la API ejecuta:"
    Write-Host "minikube service api --namespace=clinica-veterinaria --url"
}
finally {
    # Devuelve la terminal a la carpeta desde la que se ejecuto el script
    Pop-Location
}
