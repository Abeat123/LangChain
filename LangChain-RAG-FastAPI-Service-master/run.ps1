$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$frontendDir = Join-Path $projectRoot "front"
$backendDir = Join-Path $projectRoot "backend"
$djangoDir = Join-Path $projectRoot "DjangoUserService"
$logDir = Join-Path $projectRoot "logs"

function Write-Step {
    param([string]$Message)
    Write-Host "[run] $Message"
}

function Stop-PortProcess {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        return
    }

    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Step "Stopping process $($process.Id) on port $Port"
            Stop-Process -Id $process.Id -Force
        }
    }
}

function Wait-HttpReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }

    return $false
}

function Start-BackgroundProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [string]$StdoutPath,
        [string]$StderrPath
    )

    if (Test-Path $StdoutPath) {
        Remove-Item -LiteralPath $StdoutPath -Force
    }
    if (Test-Path $StderrPath) {
        Remove-Item -LiteralPath $StderrPath -Force
    }

    Write-Step "Starting $Name"
    return Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath `
        -WindowStyle Hidden `
        -PassThru
}

if (-not (Test-Path $pythonExe)) {
    throw "Missing Python virtual environment: $pythonExe"
}

$npmCmd = (Get-Command npm.cmd -ErrorAction Stop).Source

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Step "node_modules not found, running npm install"
    Push-Location $frontendDir
    try {
        & $npmCmd install
        if ($LASTEXITCODE -ne 0) {
            throw "npm install failed"
        }
    } finally {
        Pop-Location
    }
}

New-Item -ItemType Directory -Force $logDir | Out-Null

Write-Step "Stopping old services on ports 3000, 8000, 8001"
Stop-PortProcess -Port 3000
Stop-PortProcess -Port 8000
Stop-PortProcess -Port 8001

Write-Step "Running Django migrations"
Push-Location $djangoDir
try {
    & $pythonExe manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        throw "Django migrate failed"
    }
} finally {
    Pop-Location
}

$djangoProcess = Start-BackgroundProcess `
    -Name "Django user service" `
    -FilePath $pythonExe `
    -ArgumentList @("manage.py", "runserver", "127.0.0.1:8001") `
    -WorkingDirectory $djangoDir `
    -StdoutPath (Join-Path $logDir "django.stdout.log") `
    -StderrPath (Join-Path $logDir "django.stderr.log")

$backendProcess = Start-BackgroundProcess `
    -Name "FastAPI backend" `
    -FilePath $pythonExe `
    -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $backendDir `
    -StdoutPath (Join-Path $logDir "backend.stdout.log") `
    -StderrPath (Join-Path $logDir "backend.stderr.log")

$frontendProcess = Start-BackgroundProcess `
    -Name "Frontend" `
    -FilePath "cmd.exe" `
    -ArgumentList @("/c", "npm.cmd", "run", "dev", "--", "--host", "127.0.0.1", "--port", "3000") `
    -WorkingDirectory $frontendDir `
    -StdoutPath (Join-Path $logDir "frontend.stdout.log") `
    -StderrPath (Join-Path $logDir "frontend.stderr.log")

$checks = @(
    @{ Name = "Django user service"; Url = "http://127.0.0.1:8001/docs/" },
    @{ Name = "FastAPI backend"; Url = "http://127.0.0.1:8000/health/ready" },
    @{ Name = "Frontend"; Url = "http://127.0.0.1:3000/" }
)

foreach ($check in $checks) {
    if (-not (Wait-HttpReady -Url $check.Url -TimeoutSeconds 90)) {
        throw "$($check.Name) failed to start. Check the logs directory for details."
    }
}

Write-Host ""
Write-Host "All services are running:"
Write-Host "  Frontend: http://127.0.0.1:3000"
Write-Host "  FastAPI : http://127.0.0.1:8000"
Write-Host "  Django  : http://127.0.0.1:8001/docs/"
Write-Host ""
Write-Host "Process IDs:"
Write-Host "  Django  : $($djangoProcess.Id)"
Write-Host "  FastAPI : $($backendProcess.Id)"
Write-Host "  Frontend: $($frontendProcess.Id)"
Write-Host ""
Write-Host "Logs:"
Write-Host "  $logDir"
