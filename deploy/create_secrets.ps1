# Crée le Secret app.secrets à partir du fichier .env (ignoré par Git).
# Usage : ./deploy/create_secrets.ps1 [-EnvFile .env]
param(
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\.env"),
    [string]$Namespace = "latablee"
)

$ErrorActionPreference = "Stop"
$keys = @(
    "POSTGRES_USER", "POSTGRES_PASSWORD",
    "USERS_DB_PASSWORD", "MEALS_DB_PASSWORD", "BOOKINGS_DB_PASSWORD", "ACCOUNTS_DB_PASSWORD",
    "JWT_SECRET"
)

if (-not (Test-Path $EnvFile)) {
    throw "Fichier $EnvFile introuvable. Lancer : Copy-Item .env.example .env"
}

$values = @{}
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        $values[$Matches[1]] = $Matches[2].Trim()
    }
}

$literals = foreach ($key in $keys) {
    if (-not $values.ContainsKey($key) -or $values[$key] -eq "") {
        throw "Variable $key absente de $EnvFile"
    }
    "--from-literal=$key=$($values[$key])"
}

kubectl create secret generic app.secrets --namespace $Namespace @literals --dry-run=client -o yaml |
    kubectl apply -f -
