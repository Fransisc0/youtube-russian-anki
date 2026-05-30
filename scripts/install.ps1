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

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Install AnkiConnect in Anki using add-on code 2055492159"
Write-Host "2. Double-click start_service.bat"
Write-Host "3. In Chrome, open chrome://extensions and load the extension folder"
Write-Host ""
Write-Host "No DeepL key is required by default. Argos Translate is used locally."

exit 0
