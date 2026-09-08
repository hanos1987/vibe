<#
.SYNOPSIS
  Install the VIBE compiler on Windows.

.DESCRIPTION
  Installs vibec with pip, from a local checkout when run inside one and
  from GitHub otherwise.

  vibec itself runs natively on Windows. The executables it produces are
  static Linux x86-64 ELF binaries, so to *run* compiled programs use WSL
  (wsl --install) and launch them from there. Compiling on Windows and
  running under WSL is a normal workflow.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File install.ps1

.EXAMPLE
  irm https://raw.githubusercontent.com/hanos1987/vibe/master/install.ps1 | iex
#>

[CmdletBinding()]
param(
    [string]$Repo = "https://github.com/hanos1987/vibe.git"
)

$ErrorActionPreference = "Stop"

function Find-Python {
    foreach ($c in @("py -3", "python3", "python")) {
        $exe, $rest = $c.Split(" ", 2)
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            try {
                $v = & $exe $rest -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
                if ($LASTEXITCODE -eq 0 -and [version]$v -ge [version]"3.8") {
                    return $c
                }
            } catch { }
        }
    }
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Error "Python 3.8 or newer is required. Install it from https://python.org or the Microsoft Store, then run this again."
}
Write-Host "using $py"

$exe, $rest = $py.Split(" ", 2)
$pyArgs = @()
if ($rest) { $pyArgs += $rest }

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$local = Join-Path $here "pyproject.toml"

if (Test-Path $local) {
    Write-Host "installing from this checkout"
    & $exe @pyArgs -m pip install --user --upgrade $here
} else {
    Write-Host "installing from $Repo"
    & $exe @pyArgs -m pip install --user --upgrade "git+$Repo"
}
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed" }

$scripts = & $exe @pyArgs -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))"
$vibec = Join-Path $scripts "vibec.exe"

Write-Host ""
if (Test-Path $vibec) {
    Write-Host "installed: $vibec"
} else {
    Write-Host "installed to: $scripts"
}

$path = [Environment]::GetEnvironmentVariable("Path", "User")
if ($path -notlike "*$scripts*") {
    Write-Host ""
    Write-Host "add it to your PATH for this user:"
    Write-Host "  [Environment]::SetEnvironmentVariable('Path', `"`$env:Path;$scripts`", 'User')"
}

Write-Host ""
Write-Host "vibec compiles to static Linux x86-64 executables."
Write-Host "To run what you compile, use WSL:"
Write-Host "  wsl --install          (once, then reboot)"
Write-Host "  vibec hello.vibe -o hello"
Write-Host "  wsl ./hello"
Write-Host ""
Write-Host "Language reference: https://github.com/hanos1987/vibe/blob/master/SPEC.md"
