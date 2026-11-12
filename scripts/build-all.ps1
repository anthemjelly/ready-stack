# 依序建置所有 Docker 映像（Windows PowerShell 5.1 / 7 通用版）
[CmdletBinding()]
param(
    [string]$Tag = 'dev'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

$CoreImage = "ready-stack/core:$Tag"
$PythonImage = "ready-stack/python:$Tag"
$DiscordImage = "ready-stack/discord:$Tag"

# PS 5.1 會把 native command 的 stderr（docker build 進度）當成終止錯誤，
# 所以執行期間暫時改回 Continue，之後自己檢查 exit code。
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

function Invoke-DockerBuild {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string[]]$DockerArgs
    )
    Write-Host "==> 建置 $Label" -ForegroundColor Cyan
    $code = Invoke-Native -FilePath 'docker' -ArgumentList (@('build') + $DockerArgs)
    if ($code -ne 0) { throw "$Label 建置失敗 (exit $code)" }
}

Invoke-DockerBuild -Label 'core' -DockerArgs @(
    '-t', $CoreImage,
    '-f', "$Root\packages\ready-docker\core\Dockerfile",
    "$Root\packages\ready-docker"
)
Invoke-DockerBuild -Label 'lang/python' -DockerArgs @(
    '-t', $PythonImage,
    '--build-arg', "CORE_IMAGE=$CoreImage",
    '-f', "$Root\packages\ready-docker\lang\python\Dockerfile",
    "$Root\packages\ready-docker"
)
Invoke-DockerBuild -Label 'scenarios/discord' -DockerArgs @(
    '-t', $DiscordImage,
    '--build-arg', "PYTHON_IMAGE=$PythonImage",
    '-f', "$Root\packages\ready-docker\scenarios\discord\Dockerfile",
    "$Root\packages\ready-docker"
)
Invoke-DockerBuild -Label 'ready-python' -DockerArgs @(
    '-t', "ready-stack/ready-python:$Tag",
    "$Root\packages\ready-python"
)
Invoke-DockerBuild -Label 'webapi' -DockerArgs @(
    '-t', "ready-stack/webapi:$Tag",
    "$Root\packages\ready-python-docker-webapi"
)

Write-Host "全部映像建置完成（Tag=$Tag）" -ForegroundColor Green
