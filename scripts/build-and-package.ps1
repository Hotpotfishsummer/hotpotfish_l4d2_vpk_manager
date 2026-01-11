# Build and Package Script for L4D2 VPK Manager
# This script builds the application and compresses the output

# Set encoding for proper UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONUTF8 = "1"
$env:LANG = "zh_CN.UTF-8"

# Change code page to UTF-8
chcp 65001 > $null

$ErrorActionPreference = "Stop"

# Get workspace root - scripts folder is one level down from root
# If script is at: C:\...\hotpotfish_l4d2_vpk_manager\scripts\build-and-package.ps1
# Then root is at: C:\...\hotpotfish_l4d2_vpk_manager
$workspaceRoot = Split-Path -Parent $PSScriptRoot
$buildDir = Join-Path $workspaceRoot "build"
$windowsBuildDir = Join-Path $buildDir "windows"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$packageName = "hpf-vpk-manager-$timestamp.zip"
$packagePath = Join-Path $buildDir $packageName

Write-Host "Starting build and package process..." -ForegroundColor Green
Write-Host "Workspace root: $workspaceRoot" -ForegroundColor Cyan
Write-Host "Build directory: $buildDir" -ForegroundColor Cyan

# Step 1: Build with Flet
Write-Host "`nStep 1: Installing dependencies..." -ForegroundColor Yellow
Set-Location $workspaceRoot
Write-Host "Current location: $(Get-Location)" -ForegroundColor Cyan

# Verify Python executable is from conda environment
Write-Host "`nVerifying conda environment..." -ForegroundColor Cyan
& conda run -n flet-env python -c "import sys; print(f'Python executable: {sys.executable}')"

# Install dependencies in conda environment
Write-Host "`nInstalling packages in conda environment..." -ForegroundColor Cyan
& conda run -n flet-env pip install --upgrade pip

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to upgrade pip with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

& conda run -n flet-env pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

Write-Host "Dependencies installed successfully in conda environment" -ForegroundColor Green

# Verify zstandard is installed
Write-Host "`nVerifying zstandard installation..." -ForegroundColor Cyan
& conda run -n flet-env python -c "import zstandard; print(f'zstandard version: {zstandard.__version__}')"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: zstandard verification failed, but continuing..." -ForegroundColor Yellow
}

# Step 2: Build with Flet
Write-Host "`nStep 2: Building with flet..." -ForegroundColor Yellow
Write-Host "main.py exists: $(Test-Path (Join-Path $workspaceRoot 'main.py'))" -ForegroundColor Cyan

# Run flet build directly using conda run
& conda run -n flet-env flet build windows --clear-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

Write-Host "Build completed successfully" -ForegroundColor Green

# Step 3: Check if windows directory exists
if (-not (Test-Path $windowsBuildDir)) {
    Write-Host "Error: Windows build directory not found at $windowsBuildDir" -ForegroundColor Red
    exit 1
}

# Step 4: Compress the windows directory
Write-Host "`nStep 3: Compressing windows directory..." -ForegroundColor Yellow
Write-Host "Source: $windowsBuildDir"
Write-Host "Destination: $packagePath"

# Remove existing package if it exists
if (Test-Path $packagePath) {
    Remove-Item $packagePath -Force
}

# Create zip file using .NET compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($windowsBuildDir, $packagePath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

Write-Host "Package created successfully: $packagePath" -ForegroundColor Green
Write-Host "`nBuild and package process completed!" -ForegroundColor Green
Write-Host "Package name: $packageName" -ForegroundColor Cyan
