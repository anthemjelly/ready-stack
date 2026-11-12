# 本地品質檢查（Windows PowerShell 版，對應 make check）
[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$InstallOnly
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Venv = Join-Path $Root '.venv'
$Py = Join-Path $Venv 'Scripts\python.exe'

function Invoke-Step([string]$Name, [scriptblock]$Block) {
    Write-Host "==> $Name" -ForegroundColor Cyan
    # 注意：native command 寫 stderr（例如 pytest 的 deprecation warning）在
    # ErrorActionPreference=Stop 之下會被當成終止錯誤，所以執行期間改回 Continue。
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Block
        if ($LASTEXITCODE -ne 0) { throw "$Name 失敗 (exit $LASTEXITCODE)" }
    } finally {
        $ErrorActionPreference = $previous
    }
}

if (-not (Test-Path $Py)) {
    Write-Host '==> 建立 .venv' -ForegroundColor Cyan
    python -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw '建立 .venv 失敗' }
}

if (-not $SkipInstall) {
    Invoke-Step '安裝依賴' {
        & $Py -m pip install --upgrade pip --quiet
        & $Py -m pip install --quiet -e 'packages/ready-python[dev]' -e 'packages/ready-python-docker-webapi[dev]'
    }
}
if ($InstallOnly) { exit 0 }

Invoke-Step 'ruff check' { & $Py -m ruff check packages }
Invoke-Step 'ruff format --check' { & $Py -m ruff format --check packages }
Invoke-Step 'pyright' {
    # 讓 pyright 用 venv 內的 interpreter，否則會搵唔到 package 依賴
    $env:PATH = "$(Join-Path $Venv 'Scripts');$env:PATH"
    Push-Location 'packages/ready-python'
    try {
        & $Py -m pyright --pythonpath $Py
        if ($LASTEXITCODE -ne 0) { throw 'pyright (ready-python) 失敗' }
    } finally { Pop-Location }

    Push-Location 'packages/ready-python-docker-webapi'
    try {
        & $Py -m pyright --pythonpath $Py
        if ($LASTEXITCODE -ne 0) { throw 'pyright (webapi) 失敗' }
    } finally { Pop-Location }
}
Invoke-Step 'pytest' {
    Push-Location 'packages/ready-python'
    try {
        & $Py -m pytest -q 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'pytest (ready-python) 失敗' }
    } finally { Pop-Location }

    Push-Location 'packages/ready-python-docker-webapi'
    try {
        & $Py -m pytest -q 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'pytest (webapi) 失敗' }
    } finally { Pop-Location }
}

Write-Host '全部檢查通過' -ForegroundColor Green
