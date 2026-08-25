# Build VLH.exe (onedir) into vlh\dist\VLH\
# Temporarily disables NVIDIA extra-index in ProgramData pip.ini (restored after).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPy = Join-Path (Split-Path $root -Parent) ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { throw "venv python not found: $venvPy" }

$ini = "C:\ProgramData\pip\pip.ini"
$bak = "C:\ProgramData\pip\pip.ini.vlhbak"
$restored = $false
if (Test-Path $ini) {
  Copy-Item $ini $bak -Force
  @"
[global]
no-cache-dir = true
index-url = https://pypi.org/simple
trusted-host = pypi.org
               files.pythonhosted.org
"@ | Set-Content -Path $ini -Encoding ASCII
}

try {
  & $venvPy -m pip install -r requirements.txt
  & $venvPy -m PyInstaller --noconfirm --clean vlh.spec
  Write-Host ""
  Write-Host "Built: $root\dist\VLH\VLH.exe"
}
finally {
  if ((Test-Path $bak) -and -not $restored) {
    Copy-Item $bak $ini -Force
    Remove-Item $bak -Force
  }
}
