# webapi 端到端驗證（Windows PowerShell 5.1 / 7 通用版）
[CmdletBinding()]
param(
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Dir = Join-Path $Root 'packages\ready-python-docker-webapi'
Set-Location $Dir

$envFile = Join-Path $Dir '.env'
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $Dir '.env.example') $envFile
}

$apiPort = 8000
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*API_PORT\s*=\s*(\d+)\s*$') { $apiPort = [int]$Matches[1] }
}
$base = "http://localhost:$apiPort"

# PS 5.1 會把 native command 的 stderr（docker compose 進度）當成終止錯誤。
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

function Show-DockerLogs {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & docker compose logs api 2>&1
        foreach ($line in $output) {
            if ($line -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $line.Exception.Message
            } else {
                Write-Host $line
            }
        }
    } finally {
        $ErrorActionPreference = $previous
    }
}

# 回傳 HTTP status code；PS 5.1 沒有 -SkipHttpErrorCheck，所以用 try/catch 取回應碼。
function Get-HttpStatus {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Uri,
        [string]$Body = ''
    )
    try {
        $params = @{
            Method          = $Method
            Uri             = $Uri
            UseBasicParsing = $true
        }
        if ($Body) {
            $params.ContentType = 'application/json'
            $params.Body = $Body
        }
        $resp = Invoke-WebRequest @params
        return [int]$resp.StatusCode
    } catch {
        if ($_.Exception.Response -ne $null) {
            return [int]$_.Exception.Response.StatusCode
        }
        throw
    }
}

function Invoke-Cleanup {
    Write-Host '==> 清理容器與 volume' -ForegroundColor Cyan
    $null = Invoke-Native -FilePath 'docker' -ArgumentList @('compose', 'down', '-v', '--remove-orphans')
}

try {
    Write-Host '==> 建置並啟動 api + db' -ForegroundColor Cyan
    $code = Invoke-Native -FilePath 'docker' -ArgumentList @('compose', 'up', '-d', '--build')
    if ($code -ne 0) { throw "docker compose up 失敗 (exit $code)" }

    Write-Host '==> 等待 readyz' -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-RestMethod -Uri "$base/readyz" -TimeoutSec 3 -UseBasicParsing | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    if (-not $ready) {
        Show-DockerLogs
        throw 'readyz 超時'
    }

    Write-Host '==> 檢查 healthz' -ForegroundColor Cyan
    Invoke-RestMethod -Uri "$base/healthz" -UseBasicParsing | Out-Null

    Write-Host '==> 建立 item' -ForegroundColor Cyan
    $create = Invoke-RestMethod -Method Post -Uri "$base/api/v1/items" `
        -ContentType 'application/json' -UseBasicParsing `
        -Body '{"name":"e2e-item","description":"created by e2e","price":9.99}'
    $id = $create.id
    if (-not $id) { throw '建立 item 失敗（沒有 id）' }
    Write-Host "item id = $id"

    Write-Host '==> 讀取列表' -ForegroundColor Cyan
    $list = Invoke-RestMethod -Uri "$base/api/v1/items" -UseBasicParsing
    if ($list.total -lt 1) { throw "list total 不正確: $($list.total)" }

    Write-Host '==> 讀取單筆' -ForegroundColor Cyan
    $one = Invoke-RestMethod -Uri "$base/api/v1/items/$id" -UseBasicParsing
    if ($one.name -ne 'e2e-item') { throw "item name 不正確: $($one.name)" }

    Write-Host '==> 更新' -ForegroundColor Cyan
    $patched = Invoke-RestMethod -Method Patch -Uri "$base/api/v1/items/$id" `
        -ContentType 'application/json' -UseBasicParsing -Body '{"price":12.5}'
    if ([math]::Abs([double]$patched.price - 12.5) -gt 0.000001) { throw 'patch price 不正確' }

    Write-Host '==> 刪除' -ForegroundColor Cyan
    $code = Get-HttpStatus -Method 'Delete' -Uri "$base/api/v1/items/$id"
    if ($code -ne 204) { throw "DELETE 期望 204，實際 $code" }

    Write-Host '==> 確認已刪除' -ForegroundColor Cyan
    $code = Get-HttpStatus -Method 'Get' -Uri "$base/api/v1/items/$id"
    if ($code -ne 404) { throw "GET 已刪除 item 期望 404，實際 $code" }

    Write-Host 'e2e 全部通過' -ForegroundColor Green
}
finally {
    Invoke-Cleanup
}
