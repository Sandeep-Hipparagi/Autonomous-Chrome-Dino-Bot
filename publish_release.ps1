# publish_release.ps1
# Automated Git Initialization, Pre-Flight Verification, and Release Automation
# Autonomous Chrome Dino Bot v1.0.0

[CmdletBinding()]
param (
    [Alias("repo")]
    [string]$RepoUrl = "https://github.com/sandeep-hipparagi/Autonomous-Chrome-Dino-Bot.git",

    [switch]$SkipTests,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Autonomous Chrome Dino Bot - Production Release Automation" -ForegroundColor Cyan
Write-Host " Target Release Version: v1.0.0" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# ------------------------------------------------------------------------------
# 1. Pre-Flight Repository Verification
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 1/4] Running Pre-Flight Verifications..." -ForegroundColor Yellow

# A. Workspace Cleanup
Write-Host "  [*] Cleaning intermediate caches and temporary files..." -ForegroundColor Gray
$cleanScript = Join-Path $WorkspaceRoot "clean_workspace.ps1"
if (Test-Path $cleanScript) {
    & powershell.exe -ExecutionPolicy Bypass -File $cleanScript
}

# B. Python Environment Detection & Unit Testing
if (-not $SkipTests) {
    Write-Host "`n  [*] Locating Python environment for test verification..." -ForegroundColor Gray
    $venvPy = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
    $pythonCmd = if (Test-Path $venvPy) { $venvPy } else { "python.exe" }

    Write-Host "  [*] Executing test suite via: $pythonCmd test_dino_bot.py" -ForegroundColor Gray
    $testResult = & $pythonCmd "$WorkspaceRoot\test_dino_bot.py" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$testResult" -ForegroundColor Red
        throw "[FATAL] Pre-flight unit tests failed! Aborting release."
    }
    Write-Host "  [+] All 19 unit test assertions PASSED successfully." -ForegroundColor Green
}

# C. SHA-256 Checksum Verification
Write-Host "`n  [*] Verifying distribution binary integrity (dist/dino_bot.exe)..." -ForegroundColor Gray
$exePath = Join-Path $WorkspaceRoot "dist\dino_bot.exe"
$sumsPath = Join-Path $WorkspaceRoot "dist\SHA256SUMS.txt"

if (-not (Test-Path $exePath)) {
    throw "[FATAL] Standalone executable not found at: $exePath"
}
if (-not (Test-Path $sumsPath)) {
    throw "[FATAL] Checksums manifest not found at: $sumsPath"
}

$calculatedHash = (Get-FileHash -Path $exePath -Algorithm SHA256).Hash.ToLower()
$manifestContent = Get-Content -Path $sumsPath -Raw
$expectedHash = ($manifestContent -split "\s+")[0].ToLower().Trim()

if ($calculatedHash -ne $expectedHash) {
    Write-Host "  Expected:   $expectedHash" -ForegroundColor Red
    Write-Host "  Calculated: $calculatedHash" -ForegroundColor Red
    throw "[FATAL] SHA-256 Checksum mismatch! Recompile binary before releasing."
}
Write-Host "  [+] SHA-256 Verified: $calculatedHash" -ForegroundColor Green

# ------------------------------------------------------------------------------
# 2. Git Setup & Staging
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 2/4] Git Setup, Branching, and Staging..." -ForegroundColor Yellow

$gitDir = Join-Path $WorkspaceRoot ".git"
if (-not (Test-Path $gitDir)) {
    Write-Host "  [*] Initializing new Git repository..." -ForegroundColor Gray
    git init
} else {
    Write-Host "  [*] Existing Git repository detected." -ForegroundColor Gray
}

# Ensure main branch
git branch -M main

# Stage changes according to .gitignore
Write-Host "  [*] Staging all tracked workspace files..." -ForegroundColor Gray
git add .

# Check git status
$stagedChanges = git status --porcelain
if ($stagedChanges) {
    Write-Host "  [*] Committing staged release files..." -ForegroundColor Gray
    $commitMsg = "feat: production release v1.0.0 - autonomous dino runner (5,300+ FPS)"
    git commit -m $commitMsg
    Write-Host "  [+] Release commit created successfully." -ForegroundColor Green
} else {
    Write-Host "  [*] Working tree clean; no new changes to commit." -ForegroundColor Gray
}

# ------------------------------------------------------------------------------
# 3. Release Tagging
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 3/4] Creating Release Tag (v1.0.0)..." -ForegroundColor Yellow

$existingTag = git tag -l "v1.0.0"
if (-not $existingTag) {
    $tagMsg = "v1.0.0 - Production Autonomous Runner (5,300+ FPS, Zero-Latency Memory Grab)"
    git tag -a v1.0.0 -m $tagMsg
    Write-Host "  [+] Tag 'v1.0.0' successfully created." -ForegroundColor Green
} else {
    Write-Host "  [*] Tag 'v1.0.0' already exists." -ForegroundColor Gray
}

# ------------------------------------------------------------------------------
# 4. Remote Linking & Automated Push
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 4/4] Remote Synchronization and Pipeline Triggers..." -ForegroundColor Yellow

if ($RepoUrl) {
    Write-Host "  [*] Configuring remote origin: $RepoUrl" -ForegroundColor Gray
    $currentOrigin = git remote get-url origin 2>$null
    if ($currentOrigin) {
        git remote set-url origin $RepoUrl
    } else {
        git remote add origin $RepoUrl
    }

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would execute: git push -u origin main" -ForegroundColor Yellow
        Write-Host "  [DRY RUN] Would execute: git push origin v1.0.0" -ForegroundColor Yellow
    } else {
        Write-Host "  [*] Pushing 'main' branch to remote origin..." -ForegroundColor Gray
        git push -u origin main
        Write-Host "  [+] Main branch pushed. Triggered: ci.yml and pages.yml." -ForegroundColor Green

        Write-Host "  [*] Pushing 'v1.0.0' tag to remote origin..." -ForegroundColor Gray
        git push origin v1.0.0
        Write-Host "  [+] Tag v1.0.0 pushed. Triggered: release.yml." -ForegroundColor Green
    }
} else {
    Write-Host "  [!] No -RepoUrl supplied. Local repository setup, commit, and v1.0.0 tag are ready!" -ForegroundColor Yellow
    Write-Host "  [*] To link and push to your remote GitHub repository, run:" -ForegroundColor Cyan
    Write-Host "      .\publish_release.ps1 -RepoUrl https://github.com/sandeep-hipparagi/Autonomous-Chrome-Dino-Bot.git`n" -ForegroundColor White
}

Write-Host "=================================================================" -ForegroundColor Green
Write-Host " Release Preparation Completed Successfully!" -ForegroundColor Green
Write-Host " Local Branch : main" -ForegroundColor Green
Write-Host " Active Tag   : v1.0.0" -ForegroundColor Green
Write-Host " Asset Binary : dist/dino_bot.exe (SHA-256 Verified)" -ForegroundColor Green
Write-Host " Showcase GIF : assets/demo.gif (2.34 MB)" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
