# Script to run the built Windows app and capture logs
# This helps debug issues with the packaged application

param(
    [string]$BuildPath = ".\build\windows"
)

Write-Host "Looking for built executable in: $BuildPath" -ForegroundColor Cyan
$exeFiles = Get-ChildItem -Path $BuildPath -Name "*.exe" -ErrorAction SilentlyContinue

if (-not $exeFiles) {
    Write-Host "Error: No .exe file found in $BuildPath" -ForegroundColor Red
    Write-Host "Available items:" -ForegroundColor Yellow
    Get-ChildItem -Path $BuildPath | Select-Object Name
    exit 1
}

# Take the first exe file (usually the main app)
$exeName = if ($exeFiles -is [array]) { $exeFiles[0] } else { $exeFiles }
$fullPath = Join-Path $BuildPath $exeName

Write-Host "Found executable: $fullPath" -ForegroundColor Green
Write-Host "Running application..." -ForegroundColor Yellow
Write-Host "Close the app window to exit" -ForegroundColor Yellow
Write-Host "-------------------------------------------" -ForegroundColor Cyan

# Run the executable and capture all output
& $fullPath 2>&1

Write-Host "-------------------------------------------" -ForegroundColor Cyan
Write-Host "Application closed" -ForegroundColor Green
