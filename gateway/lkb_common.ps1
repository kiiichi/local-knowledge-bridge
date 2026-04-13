Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Set-LkbUtf8 {
  $utf8 = [System.Text.UTF8Encoding]::new($false)
  [Console]::InputEncoding = $utf8
  [Console]::OutputEncoding = $utf8
  $script:OutputEncoding = $utf8
  $env:PYTHONIOENCODING = 'utf-8'
}

function Resolve-LkbPython {
  param([string]$GatewayRoot)

  $configPath = Join-Path $GatewayRoot 'lkb_config.json'
  if (Test-Path -LiteralPath $configPath) {
    try {
      $config = Get-Content -Raw $configPath | ConvertFrom-Json
      $pythonHome = $config.runtime.python_home
      if ($pythonHome) {
        $candidate = Join-Path $pythonHome 'python.exe'
        if (Test-Path -LiteralPath $candidate) {
          return $candidate
        }
        $candidate = Join-Path $pythonHome 'Scripts\python.exe'
        if (Test-Path -LiteralPath $candidate) {
          return $candidate
        }
      }
    } catch {
    }
  }

  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    return 'py -3'
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return $python.Source
  }

  throw 'Python 3.11+ is required. Install Python and ensure `py` or `python` is on PATH.'
}

function Invoke-LkbPythonScript {
  param(
    [string]$ScriptBase,
    [string[]]$Arguments = @()
  )

  Set-LkbUtf8

  $scriptDir = Split-Path -Parent $ScriptBase
  $scriptPath = @("${ScriptBase}.py", "${ScriptBase}.pyc") | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if (-not $scriptPath) {
    throw "Entry script not found: $ScriptBase(.py/.pyc)"
  }

  $pythonSpec = Resolve-LkbPython -GatewayRoot $scriptDir
  Push-Location $scriptDir
  try {
    if ($pythonSpec -eq 'py -3') {
      & py -3 $scriptPath @Arguments
    } else {
      & $pythonSpec $scriptPath @Arguments
    }
    exit $LASTEXITCODE
  } finally {
    Pop-Location
  }
}
