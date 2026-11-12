```powershell
# ============================================================
# GIAR-ORION
# Script: Crear_Estructura_Agents.ps1
# Objetivo: Crear la estructura de directorios de los agentes
# Ejecutar desde la raiz del proyecto GIAR-ORION
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " GIAR-ORION - CREACION DE AGENTS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# ------------------------------------------------------------
# 1. Verificar directorio raiz
# ------------------------------------------------------------

$Root = Get-Location
$AgentsPath = Join-Path $Root "Agents"

Write-Host ""
Write-Host "Directorio del proyecto: $Root" -ForegroundColor Gray

# ------------------------------------------------------------
# 2. Definir agentes
# ------------------------------------------------------------

$Agents = @(
    "ORION",
    "ORION-ROBOTICS",
    "ORION-SOFTWARE",
    "ORION-SECURITY",
    "ORION-LANGUAGES",
    "ORION-MARKETING"
)

# ------------------------------------------------------------
# 3. Definir directorios internos
# ------------------------------------------------------------

$Subdirectories = @(
    "Core",
    "Configuration",
    "Memory",
    "Knowledge",
    "Tools",
    "Logs"
)

# ------------------------------------------------------------
# 4. Crear directorio principal
# ------------------------------------------------------------

if (!(Test-Path $AgentsPath)) {

    New-Item -ItemType Directory -Path $AgentsPath | Out-Null

    Write-Host "[CREADO] Agents" -ForegroundColor Green
}
else {

    Write-Host "[EXISTE] Agents" -ForegroundColor DarkGray
}

# ------------------------------------------------------------
# 5. Crear estructura de cada agente
# ------------------------------------------------------------

foreach ($Agent in $Agents) {

    $AgentPath = Join-Path $AgentsPath $Agent

    if (!(Test-Path $AgentPath)) {

        New-Item -ItemType Directory -Path $AgentPath | Out-Null

        Write-Host ""
        Write-Host "[AGENTE CREADO] $Agent" -ForegroundColor Green
    }
    else {

        Write-Host ""
        Write-Host "[AGENTE EXISTENTE] $Agent" -ForegroundColor DarkGray
    }

    foreach ($Subdirectory in $Subdirectories) {

        $Path = Join-Path $AgentPath $Subdirectory

        if (!(Test-Path $Path)) {

            New-Item -ItemType Directory -Path $Path | Out-Null

            Write-Host "  [CREADO] $Subdirectory" -ForegroundColor Green
        }
        else {

            Write-Host "  [EXISTE] $Subdirectory" -ForegroundColor DarkGray
        }
    }
}

# ------------------------------------------------------------
# 6. Mostrar estructura final
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ESTRUCTURA AGENTS GENERADA" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

tree $AgentsPath /F

Write-Host ""
Write-Host "Proceso finalizado correctamente." -ForegroundColor Green
Write-Host ""
```