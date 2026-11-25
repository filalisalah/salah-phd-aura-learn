#Requires -Version 5.1
<#
.SYNOPSIS
    Opens Microsoft Edge on the local Streamlit application.

.DESCRIPTION
    This script performs NO debugger attachment to the browser:
    it uses neither --remote-debugging-port, nor --remote-debugging-pipe, nor
    --user-data-dir. It simply opens a regular tab on the application URL,
    which works around the js-debug error
    "Unable to attach to browser" (js-debug 1.93 vs Edge 158).

    Sequence:
      1. waits until the URL responds (Invoke-WebRequest loop, 60 s timeout, 500 ms interval);
      2. opens an Edge tab on the URL;
      3. exits with code 0.

    Idempotent: does not reopen a window if an Edge instance has already been
    launched with this URL, and opens NOTHING if the URL does not respond (code 1).

.PARAMETER Url
    Application URL. Default: http://localhost:8501

.PARAMETER TimeoutSeconds
    Maximum server wait time. Default: 60

.PARAMETER PollIntervalMs
    Attempt interval. Default: 500

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .vscode/open-edge.ps1
#>
[CmdletBinding()]
param(
    [string]$Url = 'http://localhost:8501',
    [int]$TimeoutSeconds = 60,
    [int]$PollIntervalMs = 500
)

$ErrorActionPreference = 'Stop'

if ($PSScriptRoot) {
    $scriptRoot = $PSScriptRoot
}
else {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
}

$logFile = Join-Path $scriptRoot 'open-edge.log'

function Write-Log {
    param([string]$Message)

    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    try {
        Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        # The log is a diagnostic convenience: its failure must never block.
    }
    Write-Host $line
}

function Resolve-EdgeExe {
    $candidates = New-Object System.Collections.Generic.List[string]

    if ($env:ProgramFiles) {
        $candidates.Add((Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'))
    }
    if (${env:ProgramFiles(x86)}) {
        $candidates.Add((Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'))
    }
    if ($env:LOCALAPPDATA) {
        $candidates.Add((Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe'))
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    $onPath = Get-Command -Name 'msedge.exe' -ErrorAction SilentlyContinue
    if ($onPath -and $onPath.Source) {
        return $onPath.Source
    }

    return $null
}

function Test-AppReady {
    param([string]$TargetUrl)

    try {
        $response = Invoke-WebRequest -Uri $TargetUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
    }
    catch {
        return $false
    }
}

function Test-EdgeAlreadyOpen {
    param([string]$TargetUrl)

    try {
        $processes = @(Get-CimInstance -ClassName Win32_Process -Filter "Name = 'msedge.exe'" -ErrorAction Stop)
    }
    catch {
        Write-Log ('Information: unable to inspect Edge command lines ({0}).' -f $_.Exception.Message)
        return $false
    }

    foreach ($process in $processes) {
        if ($process.CommandLine -and
            ($process.CommandLine.IndexOf($TargetUrl, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)) {
            return $true
        }
    }

    return $false
}

Write-Log ('Waiting for {0} (timeout {1}s, interval {2}ms).' -f $Url, $TimeoutSeconds, $PollIntervalMs)

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$ready = $false
while ((Get-Date) -lt $deadline) {
    if (Test-AppReady -TargetUrl $Url) {
        $ready = $true
        break
    }
    Start-Sleep -Milliseconds $PollIntervalMs
}

if (-not $ready) {
    Write-Log ('FAILURE: {0} does not respond after {1}s. No Edge window opened.' -f $Url, $TimeoutSeconds)
    Write-Log 'Check that Streamlit is listening on port 8501 (Python terminal), then press F5 again.'
    exit 1
}

$edgeExe = Resolve-EdgeExe
if (-not $edgeExe) {
    Write-Log 'FAILURE: msedge.exe not found (Program Files, Program Files (x86), LOCALAPPDATA, PATH).'
    exit 1
}

if (Test-EdgeAlreadyOpen -TargetUrl $Url) {
    Write-Log ('Edge already positioned on {0}: no new window opened.' -f $Url)
    exit 0
}

try {
    Start-Process -FilePath $edgeExe -ArgumentList $Url -ErrorAction Stop | Out-Null
    Write-Log ('Edge launched: {0} -> {1}' -f $edgeExe, $Url)
    exit 0
}
catch {
    Write-Log ('FAILURE: unable to launch Edge ({0}).' -f $_.Exception.Message)
    exit 1
}
