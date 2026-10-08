# clean_workspace.ps1
# Maintenance and Workspace Clean-Up Utility for Autonomous Chrome Dino Bot

[CmdletBinding()]
param (
    [switch]$DeepClean,
    [switch]$KeepTelemetry
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "     Autonomous Chrome Dino Bot - Workspace Maintenance Clean-Up" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot

# 1. Clean Python __pycache__ directories
Write-Host "`n[*] Scanning and removing Python __pycache__ and bytecode..." -ForegroundColor Yellow
$pycacheDirs = Get-ChildItem -Path $WorkspaceRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
foreach ($dir in $pycacheDirs) {
    Write-Host "  [-] Removing: $($dir.FullName)" -ForegroundColor DarkGray
    Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

$pycFiles = Get-ChildItem -Path $WorkspaceRoot -Recurse -File -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue
foreach ($f in $pycFiles) {
    Remove-Item -Path $f.FullName -Force -ErrorAction SilentlyContinue
}

# 2. Clean PyInstaller intermediate build artifacts
Write-Host "`n[*] Cleaning PyInstaller build artifacts..." -ForegroundColor Yellow
$buildDir = Join-Path $WorkspaceRoot "build"
if (Test-Path $buildDir) {
    Write-Host "  [-] Removing intermediate build directory: $buildDir" -ForegroundColor DarkGray
    Remove-Item -Path $buildDir -Recurse -Force -ErrorAction SilentlyContinue
}

# 3. Clean temporary diagnostic dumps if requested or prune older dumps
if ($DeepClean) {
    Write-Host "`n[*] Deep Clean: Purging debug_deaths and diagnostics replay frames..." -ForegroundColor Yellow
    $deathsDir = Join-Path $WorkspaceRoot "debug_deaths"
    if (Test-Path $deathsDir) {
        Remove-Item -Path "$deathsDir\*.png" -Force -ErrorAction SilentlyContinue
        Write-Host "  [-] Purged all replay frames in $deathsDir" -ForegroundColor DarkGray
    }

    $diagDir = Join-Path $WorkspaceRoot "diagnostics"
    if (Test-Path $diagDir) {
        Remove-Item -Path "$diagDir\*.png" -Force -ErrorAction SilentlyContinue
        Write-Host "  [-] Purged diagnostic snapshots in $diagDir" -ForegroundColor DarkGray
    }

    if (-not $KeepTelemetry) {
        $testCsv = Join-Path $WorkspaceRoot "test_telemetry.csv"
        if (Test-Path $testCsv) {
            Remove-Item -Path $testCsv -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "`n[*] Standard Clean: Preserving ./debug_deaths/ and ./session_telemetry.csv" -ForegroundColor Green
    Write-Host "    (Use -DeepClean to purge old replay frames)" -ForegroundColor DarkGray
}

# 4. Remove temporary scratch/test files
Write-Host "`n[*] Removing temporary test artifacts..." -ForegroundColor Yellow
$tempArtifacts = @("test_grab.png", "chrome_test.png", "printwindow_test.png")
foreach ($art in $tempArtifacts) {
    $artPath = Join-Path $WorkspaceRoot $art
    if (Test-Path $artPath) {
        Write-Host "  [-] Removing: $art" -ForegroundColor DarkGray
        Remove-Item -Path $artPath -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host " Clean-up complete! Production artifacts and binaries intact." -ForegroundColor Green
Write-Host " Standalone Executable : dist/dino_bot.exe" -ForegroundColor Cyan
Write-Host " Core Runner Script    : dino_bot.py" -ForegroundColor Cyan
Write-Host " Verification Suite    : test_dino_bot.py" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Green
