$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Updating local files from GitHub..."
git pull --ff-only

Write-Host ""
Write-Host "Installing/updating dependencies..."
& "$repoRoot\scripts\install.ps1"

Write-Host ""
Write-Host "Restarting local service on port 8766 if it is running..."
try {
    $connections = Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        if ($processId -and $processId -ne $PID) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped service process $processId."
        }
    }
} catch {
    Write-Host "Could not inspect port 8766. If the old service is still running, close its window manually."
}

Write-Host ""
Write-Host "Starting service in a new minimized window..."
Start-Process -FilePath "$repoRoot\start_service.bat" -WorkingDirectory $repoRoot -WindowStyle Minimized

Write-Host ""
Write-Host "Done. In Chrome, click the extension icon and choose Reload Extension, then refresh YouTube."
