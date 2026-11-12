```powershell
# ============================================================
# GIAR-ORION
# Script: Crear_Estructura_Interface.ps1
# Objetivo: Crear estructura de Interface y Avatars
# Ejecutar desde la raiz de GIAR-ORION
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " GIAR-ORION - CREACION DE INTERFACE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# ------------------------------------------------------------
# 1. Verificar directorio raiz
# ------------------------------------------------------------

$Root = Get-Location

$Interface = Join-Path $Root "Interface"
$Avatars = Join-Path $Interface "Avatars"

Write-Host ""
Write-Host "Directorio del proyecto: $Root"

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
# 3. Crear directorios principales
# ------------------------------------------------------------

$Directories = @(
    $Interface,
    $Avatars,
    (Join-Path $Interface "UI")
)

foreach ($Directory in $Directories) {

    if (!(Test-Path $Directory)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
        Write-Host "[CREADO] $Directory" -ForegroundColor Green
    }
    else {
        Write-Host "[EXISTE] $Directory" -ForegroundColor DarkGray
    }
}

# ------------------------------------------------------------
# 4. Crear estructura de cada avatar
# ------------------------------------------------------------

foreach ($Agent in $Agents) {

    $AgentPath = Join-Path $Avatars $Agent

    $Subdirectories = @(
        "Model",
        "Textures",
        "Animations",
        "Voice"
    )

    if (!(Test-Path $AgentPath)) {
        New-Item -ItemType Directory -Path $AgentPath -Force | Out-Null
    }

    foreach ($Subdirectory in $Subdirectories) {

        $Path = Join-Path $AgentPath $Subdirectory

        if (!(Test-Path $Path)) {
            New-Item -ItemType Directory -Path $Path -Force | Out-Null
            Write-Host "[CREADO] $Agent/$Subdirectory" -ForegroundColor Green
        }
    }

    # --------------------------------------------------------
    # 5. Crear avatar_config.json
    # --------------------------------------------------------

    $AvatarConfig = Join-Path $AgentPath "avatar_config.json"

    if (!(Test-Path $AvatarConfig)) {

        $Config = @{
            agent_id = $Agent
            display_name = $Agent
            avatar_enabled = $true
            model_path = "Model"
            textures_path = "Textures"
            animations_path = "Animations"
            voice_path = "Voice"
        } | ConvertTo-Json -Depth 5

        Set-Content -LiteralPath $AvatarConfig `
            -Value $Config -Encoding UTF8

        Write-Host "[CREADO] $Agent/avatar_config.json" -ForegroundColor Green
    }
    else {
        Write-Host "[EXISTE] $Agent/avatar_config.json" -ForegroundColor DarkGray
    }

    # --------------------------------------------------------
    # 6. Crear voice_config.json
    # --------------------------------------------------------

    $VoiceConfig = Join-Path $AgentPath "Voice\voice_config.json"

    if (!(Test-Path $VoiceConfig)) {

        $Config = @{
            agent_id = $Agent
            voice_enabled = $true
            tts_engine = ""
            voice_id = ""
            language = "es"
            speed = 1.0
            pitch = 1.0
        } | ConvertTo-Json -Depth 5

        Set-Content -LiteralPath $VoiceConfig `
            -Value $Config -Encoding UTF8

        Write-Host "[CREADO] $Agent/Voice/voice_config.json" -ForegroundColor Green
    }
    else {
        Write-Host "[EXISTE] $Agent/Voice/voice_config.json" -ForegroundColor DarkGray
    }
}

# ------------------------------------------------------------
# 7. Mostrar estructura final
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ESTRUCTURA INTERFACE GENERADA" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

tree $Interface /F

Write-Host ""
Write-Host "Proceso finalizado correctamente." -ForegroundColor Green
Write-Host ""
```