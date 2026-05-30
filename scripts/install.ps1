$ErrorActionPreference = "Stop"

function Find-Python {
    $candidates = @(
        @{ Command = "py"; Args = @("-3") },
        @{ Command = "python"; Args = @() },
        @{ Command = "python3"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if ($null -eq $cmd) {
            continue
        }
        try {
            $version = & $candidate.Command @($candidate.Args + @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"))
            if ([version]$version -ge [version]"3.11") {
                return $candidate
            }
        } catch {
            continue
        }
    }

    return $null
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$Arguments
    )
    & $Python.Command @($Python.Args + $Arguments)
}

Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Checking for Python 3.11+..."
$python = Find-Python
if ($null -eq $python) {
    Write-Host ""
    Write-Host "Python 3.11 or newer was not found."
    Write-Host "Install Python from https://www.python.org/downloads/windows/"
    Write-Host "During install, check: Add python.exe to PATH"
    exit 1
}

Write-Host "Creating local Python environment..."
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $recreateVenv = $false
    try {
        & $venvPython -c "import sys; print(sys.version)" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $recreateVenv = $true
        }
    } catch {
        $recreateVenv = $true
    }
    if ($recreateVenv) {
        Write-Host "Existing .venv is broken; recreating it..."
        Remove-Item -Recurse -Force ".venv"
    }
}
Invoke-Python -Python $python -Arguments @("-m", "venv", ".venv")

Write-Host "Upgrading pip..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip

Write-Host "Installing app dependencies..."
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Created .env from .env.example."
}

$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "YouTube to Anki.lnk"
$targetPath = Join-Path (Get-Location) "START_HERE.bat"
try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $targetPath
    $shortcut.WorkingDirectory = (Get-Location).Path
    $shortcut.Description = "Start YouTube Russian-to-Anki"
    $shortcut.Save()
    Write-Host "Created desktop shortcut: YouTube to Anki"
} catch {
    Write-Host "Could not create desktop shortcut. You can still use START_HERE.bat."
}

$startupShortcutPath = Join-Path ([Environment]::GetFolderPath("Startup")) "YouTube to Anki Service.lnk"
$serviceTargetPath = Join-Path (Get-Location) "start_service.bat"
try {
    $shell = New-Object -ComObject WScript.Shell
    $startupShortcut = $shell.CreateShortcut($startupShortcutPath)
    $startupShortcut.TargetPath = $serviceTargetPath
    $startupShortcut.WorkingDirectory = (Get-Location).Path
    $startupShortcut.Description = "Run YouTube-to-Anki local service at sign-in"
    $startupShortcut.WindowStyle = 7
    $startupShortcut.Save()
    Write-Host "Created startup shortcut: YouTube to Anki Service"
} catch {
    Write-Host "Could not create startup shortcut. You can still use start_service.bat."
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Install AnkiConnect in Anki using add-on code 2055492159"
Write-Host "2. Double-click START_HERE.bat, or use the desktop shortcut"
Write-Host "3. In Chrome, load the extension folder if it is not loaded yet"
Write-Host "4. After this, the local service will auto-start when you sign in to Windows"
Write-Host ""
Write-Host "No DeepL key is required by default. Argos Translate is used locally."

exit 0
