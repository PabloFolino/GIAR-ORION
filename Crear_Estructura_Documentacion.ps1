# ============================================================
# GIAR-ORION
# Script: Crear_Estructura_Documentacion.ps1
# Objetivo: Crear y organizar la estructura Documents
# Ejecutar desde la raíz del proyecto.
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " GIAR-ORION - ORGANIZACION DE DOCUMENTACION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# 1. Verificar directorio raiz
# ------------------------------------------------------------

$Root = Get-Location
$Documents = Join-Path $Root "Documents"

if (!(Test-Path $Documents -PathType Container)) {
    Write-Host "ERROR: No se encuentra el directorio Documents." -ForegroundColor Red
    Write-Host "Ejecuta este script desde la raiz de GIAR-ORION."
    exit 1
}

Write-Host "Directorio del proyecto: $Root" -ForegroundColor Gray

# ------------------------------------------------------------
# 2. Crear estructura de directorios
# ------------------------------------------------------------

$Directories = @(
    "00_GENERAL",
    "01_REQUIREMENTS",
    "02_DESIGN",
    "03_IMPLEMENTATION",
    "04_TESTS",
    "05_CHANGELOG",
    "06_MANUALS",
    "Images"
)

foreach ($Directory in $Directories) {

    $Path = Join-Path $Documents $Directory

    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
        Write-Host "[CREADO] $Directory" -ForegroundColor Green
    }
    else {
        Write-Host "[EXISTE] $Directory" -ForegroundColor DarkGray
    }
}

# ------------------------------------------------------------
# 3. Mover documentos existentes
# ------------------------------------------------------------

$FilesToMove = @(
    @{
        Name = "GIAR-ORION.md"
        Destination = "00_GENERAL"
    },
    @{
        Name = "Instrucciones-prueba-comparativa.md"
        Destination = "04_TESTS"
    },
    @{
        Name = "Manual-Instalacion-Ollama.md"
        Destination = "06_MANUALS"
    },
    @{
        Name = "Registro-cambios-KnowledgeRetriever-iteracion-2.md"
        Destination = "05_CHANGELOG"
    },
    @{
        Name = "Registro-cambios-KnowledgeRetriever-iteracion-3.md"
        Destination = "05_CHANGELOG"
    }
)

foreach ($File in $FilesToMove) {

    $Source = Join-Path $Documents $File.Name

    $DestinationFolder = Join-Path $Documents $File.Destination

    $Destination = Join-Path $DestinationFolder $File.Name

    if (Test-Path $Source -PathType Leaf) {

        if (!(Test-Path $Destination)) {

            Move-Item -LiteralPath $Source -Destination $Destination

            Write-Host "[MOVIDO] $($File.Name) -> $($File.Destination)" -ForegroundColor Green

        }
        else {

            Write-Host "[OMITIDO] Ya existe el destino: $($File.Name)" -ForegroundColor Yellow

        }
    }
    else {

        if (Test-Path $Destination -PathType Leaf) {
            Write-Host "[OK] $($File.Name)" -ForegroundColor DarkGray
        }
        else {
            Write-Host "[NO ENCONTRADO] $($File.Name)" -ForegroundColor Yellow
        }
    }
}

# ------------------------------------------------------------
# 4. Crear REQ-001 si no existe
# ------------------------------------------------------------

$RequirementFile = Join-Path $Documents "01_REQUIREMENTS\REQ-001_Knowledge_Manager.md"

if (!(Test-Path $RequirementFile)) {

    $RequirementContent = @'
# REQ-001 - ORION KNOWLEDGE MANAGER

**Proyecto:** GIAR-ORION  
**Versión:** 0.1  
**Estado:** DRAFT  
**Tipo:** Requerimiento funcional  

---

## 1. Objetivo

Definir los requerimientos para desarrollar el administrador
del conocimiento de la plataforma multiagente ORION.

## 2. Alcance

El módulo deberá permitir administrar el conocimiento
particular y compartido de los distintos agentes.

## 3. Requerimientos funcionales

Pendiente de especificación.

## 4. Requerimientos no funcionales

Pendiente de especificación.

## 5. Arquitectura

Pendiente de definición.

## 6. Plan de tareas

| Identificador | Descripción | Estado |
|---|---|---|
| REQ-001-T001 | Definir estructura de almacenamiento | PENDIENTE |
| REQ-001-T002 | Implementar catálogo documental | PENDIENTE |
| REQ-001-T003 | Implementar administración documental | PENDIENTE |
| REQ-001-T004 | Implementar metadatos y auditoría | PENDIENTE |
| REQ-001-T005 | Implementar procesamiento documental | PENDIENTE |
| REQ-001-T006 | Integrar indexación RAG | PENDIENTE |
| REQ-001-T007 | Implementar permisos de acceso | PENDIENTE |
| REQ-001-T008 | Implementar transferencia de conocimiento | PENDIENTE |
| REQ-001-T009 | Implementar revisión de propuestas | PENDIENTE |
| REQ-001-T010 | Ejecutar pruebas de aceptación | PENDIENTE |

## 7. Pruebas y criterios de aceptación

Pendiente de especificación.

## 8. Historial de modificaciones

| Versión | Descripción |
|---|---|
| 0.1 | Creación inicial del documento |
'@

    Set-Content -LiteralPath $RequirementFile -Value $RequirementContent -Encoding UTF8

    Write-Host "[CREADO] REQ-001_Knowledge_Manager.md" -ForegroundColor Green

}
else {

    Write-Host "[EXISTE] REQ-001_Knowledge_Manager.md" -ForegroundColor DarkGray

}

# ------------------------------------------------------------
# 5. Crear INDEX.md si no existe
# ------------------------------------------------------------

$IndexFile = Join-Path $Documents "INDEX.md"

if (!(Test-Path $IndexFile)) {

    $IndexContent = @'
# GIAR-ORION - INDICE DE DOCUMENTACION

## Documentación general

- [GIAR-ORION](00_GENERAL/GIAR-ORION.md)

## Requerimientos

- [REQ-001 - ORION KNOWLEDGE MANAGER](01_REQUIREMENTS/REQ-001_Knowledge_Manager.md)

## Diseño

Documentos de diseño técnico.

## Implementación

Documentación de las implementaciones.

## Pruebas

- [Prueba comparativa del recuperador](04_TESTS/Instrucciones-prueba-comparativa.md)

## Historial de cambios

- [KnowledgeRetriever - Iteración 2](05_CHANGELOG/Registro-cambios-KnowledgeRetriever-iteracion-2.md)
- [KnowledgeRetriever - Iteración 3](05_CHANGELOG/Registro-cambios-KnowledgeRetriever-iteracion-3.md)

## Manuales

- [Instalación de Ollama](06_MANUALS/Manual-Instalacion-Ollama.md)
'@

    Set-Content -LiteralPath $IndexFile -Value $IndexContent -Encoding UTF8

    Write-Host "[CREADO] INDEX.md" -ForegroundColor Green

}
else {

    Write-Host "[EXISTE] INDEX.md" -ForegroundColor DarkGray

}

# ------------------------------------------------------------
# 6. Resultado
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ESTRUCTURA DE DOCUMENTACION GENERADA" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

tree $Documents /F

Write-Host ""
Write-Host "Proceso finalizado." -ForegroundColor Green
Write-Host ""