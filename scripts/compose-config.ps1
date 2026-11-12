# 驗證所有 compose 檔（Windows PowerShell 5.1 / 7 通用版）
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Webapi = Join-Path $Root 'packages\ready-python-docker-webapi'
$ReadyDocker = Join-Path $Root 'packages\ready-docker'

# PS 5.1 會把 native command 的 stderr 當成終止錯誤，執行期間改回 Continue。
function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & $FilePath @ArgumentList 2>&1
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            foreach ($line in $output) {
                if ($line -is [System.Management.Automation.ErrorRecord]) {
                    Write-Host $line.Exception.Message
                } else {
                    Write-Host $line
                }
            }
        }
        return $exitCode
    } finally {
        $ErrorActionPreference = $previous
    }
}

function Ensure-Env([string]$Dir) {
    $envFile = Join-Path $Dir '.env'
    $example = Join-Path $Dir '.env.example'
    if ((Test-Path $example) -and -not (Test-Path $envFile)) {
        Copy-Item $example $envFile
    }
}

Ensure-Env $Webapi
Write-Host "==> 驗證 $Webapi\compose.yml" -ForegroundColor Cyan
$code = Invoke-Native -FilePath 'docker' -ArgumentList @('compose', '-f', (Join-Path $Webapi 'compose.yml'), 'config', '-q')
if ($code -ne 0) { throw "webapi compose 驗證失敗 (exit $code)" }

if (Test-Path (Join-Path $ReadyDocker 'compose.yml')) {
    Ensure-Env $ReadyDocker
    Write-Host "==> 驗證 $ReadyDocker\compose.yml" -ForegroundColor Cyan
    $code = Invoke-Native -FilePath 'docker' -ArgumentList @('compose', '-f', (Join-Path $ReadyDocker 'compose.yml'), 'config', '-q')
    if ($code -ne 0) { throw "ready-docker compose 驗證失敗 (exit $code)" }
}

Write-Host 'compose 檔全部通過' -ForegroundColor Green
