$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Step 1 of 4: Installing/updating local Python app..."
& "$repoRoot\scripts\install.ps1"

Write-Host ""
Write-Host "Step 2 of 4: Preparing Chrome extension path..."
$extensionPath = Join-Path $repoRoot "extension"
Set-Clipboard -Value $extensionPath
Write-Host "Copied this extension folder path to your clipboard:"
Write-Host $extensionPath

Write-Host ""
Write-Host "Step 3 of 4: Opening Chrome extension page..."
try {
    Start-Process "chrome.exe" "chrome://extensions"
} catch {
    Start-Process "https://www.google.com/chrome/"
    Write-Host "Chrome was not found on PATH. Install Chrome, then open chrome://extensions."
}

Write-Host ""
Write-Host "In Chrome:"
Write-Host "1. Turn on Developer mode."
Write-Host "2. Click Load unpacked."
Write-Host "3. Paste the copied folder path."
Write-Host "4. Select the extension folder."

Write-Host ""
Write-Host "Step 4 of 4: The service will start in this window next."
Write-Host "Start Anki first if you have not already."

exit 0
