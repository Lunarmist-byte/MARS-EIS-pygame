<#
================================================================================
 DUSTFALL — Mars Survival & MARS-EIS Environmental Interface
 Full-Stack Deployment & Startup Script (PowerShell)
 
 1. Clones MARS-EIS backend repository if not already present.
 2. Installs / verifies required Python dependencies.
 3. Starts authoritative MARS-EIS scientific engine on http://127.0.0.1:8000.
 4. Launches DUSTFALL Pygame client with live telemetry synchronization.
 5. Cleanly terminates background processes on exit.

 Made by Lunarmist-byte
 GitHub:   https://github.com/Lunarmist-byte
 LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
================================================================================
#>

[CmdletBinding()]
param(
    [string]$BackendRepo = "https://github.com/Lunarmist-byte/drsosospaceadventure.git",
    [int]$Port = 8000,
    [switch]$SkipIntro
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   DUSTFALL // FULL-STACK SIMULATION LAUNCHER (POWERSHELL)" -ForegroundColor Cyan
Write-Host "   Made by Lunarmist-byte" -ForegroundColor Yellow
Write-Host "   GitHub:   https://github.com/Lunarmist-byte" -ForegroundColor DarkGray
Write-Host "   LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Resolve Python executable
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "[ERROR] Python was not found in PATH! Please install Python 3.10+." -ForegroundColor Red
    exit 1
}
$pyExec = $python.Source
Write-Host "[1/5] Using Python: $pyExec" -ForegroundColor Green

# 2. Check / Clone Backend Repository
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$parentDir = Split-Path -Parent $scriptDir

# Check sibling '../ssosalien' or local './ssosalien'
$backendDir = Join-Path $parentDir "ssosalien"
if (-not (Test-Path $backendDir)) {
    $backendDir = Join-Path $scriptDir "ssosalien"
}

if (Test-Path $backendDir) {
    Write-Host "[2/5] Backend directory detected at: $backendDir" -ForegroundColor Green
} else {
    Write-Host "[2/5] Backend not found locally. Cloning from $BackendRepo..." -ForegroundColor Yellow
    $cloneTarget = Join-Path $parentDir "ssosalien"
    try {
        git clone $BackendRepo $cloneTarget
        $backendDir = $cloneTarget
        Write-Host "      Backend successfully cloned to: $backendDir" -ForegroundColor Green
    } catch {
        Write-Host "      Parent folder clone failed, cloning inside workspace..." -ForegroundColor DarkYellow
        $cloneTarget = Join-Path $scriptDir "ssosalien"
        git clone $BackendRepo $cloneTarget
        $backendDir = $cloneTarget
        Write-Host "      Backend successfully cloned to: $backendDir" -ForegroundColor Green
    }
}

# 3. Verify Dependencies
Write-Host "[3/5] Verifying Python dependencies..." -ForegroundColor Yellow
$reqFile = Join-Path $scriptDir "requirements.txt"
if (Test-Path $reqFile) {
    & $pyExec -m pip install -q -r $reqFile
}

$backendReq = Join-Path $backendDir "requirements.txt"
if (Test-Path $backendReq) {
    & $pyExec -m pip install -q -r $backendReq
}
Write-Host "      Dependencies verified." -ForegroundColor Green

# 4. Check & Start MARS-EIS Backend Server
Write-Host "[4/5] Checking MARS-EIS simulation backend on port $Port..." -ForegroundColor Yellow
$backendStartedByUs = $false
$backendProcess = $null

function Test-PortOpen([string]$hostName, [int]$portNumber) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $asyncResult = $client.BeginConnect($hostName, $portNumber, $null, $null)
        $wait = $asyncResult.AsyncWaitHandle.WaitOne(400, $false)
        if ($wait -and $client.Connected) {
            $client.EndConnect($asyncResult)
            return $true
        }
        return $false
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

$isPortOpen = Test-PortOpen "127.0.0.1" $Port
if ($isPortOpen) {
    Write-Host "      Existing MARS-EIS engine found running at http://127.0.0.1:$Port." -ForegroundColor Green
} else {
    Write-Host "      Starting MARS-EIS backend on http://127.0.0.1:$Port in background..." -ForegroundColor Yellow
    
    # Start as background process
    $backendProcess = Start-Process -FilePath $pyExec `
        -ArgumentList "main.py --serve-api --port $Port" `
        -WorkingDirectory $backendDir `
        -PassThru -WindowStyle Hidden
    
    $backendStartedByUs = $true

    # Wait for server ready (up to 10 seconds)
    $ready = $false
    for ($i = 0; $i -lt 25; $i++) {
        Start-Sleep -Milliseconds 400
        if (Test-PortOpen "127.0.0.1" $Port) {
            $ready = $true
            break
        }
    }

    if ($ready) {
        Write-Host "      MARS-EIS backend online and responding on port $Port!" -ForegroundColor Green
    } else {
        Write-Host "      [WARNING] Backend took longer than expected to bind port $Port. Launching client anyway..." -ForegroundColor DarkYellow
    }
}

# 5. Launch DUSTFALL Pygame Client
Write-Host "[5/5] Launching DUSTFALL Client..." -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray

try {
    $gameArgs = @("main.py")
    if ($SkipIntro) {
        $gameArgs += "--skip-intro"
    }
    Push-Location $scriptDir
    & $pyExec $gameArgs
    Pop-Location
} finally {
    if ($backendStartedByUs -and $backendProcess -and (-not $backendProcess.HasExited)) {
        Write-Host ""
        Write-Host "Stopping background MARS-EIS backend process (PID $($backendProcess.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Backend stopped cleanly." -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Session finished. Thank you for playing DUSTFALL!" -ForegroundColor Cyan
    Write-Host "Made by Lunarmist-byte (https://github.com/Lunarmist-byte)" -ForegroundColor DarkGray
}
