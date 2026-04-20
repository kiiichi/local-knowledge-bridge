Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Set-LkbUtf8 {
  $utf8 = [System.Text.UTF8Encoding]::new($false)
  [Console]::InputEncoding = $utf8
  [Console]::OutputEncoding = $utf8
  $script:OutputEncoding = $utf8
  $env:PYTHONIOENCODING = 'utf-8'
}

function Test-LkbPythonExecutable {
  param(
    [Parameter(Mandatory = $true)]
    [string]$PythonSpec
  )

  try {
    if ($PythonSpec.StartsWith('py ')) {
      $selector = $PythonSpec.Substring(3)
      & py $selector -c "import sys; assert sys.version_info >= (3, 11)" *> $null
    } else {
      & $PythonSpec -c "import sys; assert sys.version_info >= (3, 11)" *> $null
    }
    return ($LASTEXITCODE -eq 0)
  } catch {
    return $false
  }
}

function Get-LkbRuntimeHome {
  param([string]$GatewayRoot)

  $configPath = Join-Path $GatewayRoot 'lkb_config.json'
  if (Test-Path -LiteralPath $configPath) {
    try {
      $config = Get-Content -Raw $configPath | ConvertFrom-Json
      $pythonHome = $config.runtime.python_home
      if ($pythonHome) {
        return $pythonHome
      }
    } catch {
    }
  }

  $defaultHome = Join-Path $GatewayRoot 'runtime\py311'
  if (Test-Path -LiteralPath $defaultHome) {
    return $defaultHome
  }

  return $null
}

function Resolve-LkbPython {
  param(
    [string]$GatewayRoot,
    [switch]$AllowFallback
  )

  $runtimeHome = Get-LkbRuntimeHome -GatewayRoot $GatewayRoot
  $brokenRuntimeCandidates = @()
  if ($runtimeHome) {
    foreach ($candidate in @(
      (Join-Path $runtimeHome 'python.exe'),
      (Join-Path $runtimeHome 'Scripts\python.exe')
    )) {
      if (-not (Test-Path -LiteralPath $candidate)) {
        continue
      }
      if (Test-LkbPythonExecutable -PythonSpec $candidate) {
        return $candidate
      }
      $brokenRuntimeCandidates += $candidate
    }
  }

  if ($brokenRuntimeCandidates.Count -gt 0 -and -not $AllowFallback) {
    throw "Embedded LKB runtime is present but not executable: $($brokenRuntimeCandidates -join ', '). This usually means the runtime depends on a base interpreter outside the current sandbox. Re-run lkb_bootstrap_runtime to repair it."
  }

  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    foreach ($selector in @('-3.11', '-3.12', '-3.13', '-3')) {
      $pythonSpec = "py $selector"
      if (Test-LkbPythonExecutable -PythonSpec $pythonSpec) {
        return $pythonSpec
      }
    }
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python -and (Test-LkbPythonExecutable -PythonSpec $python.Source)) {
    return $python.Source
  }

  if ($brokenRuntimeCandidates.Count -gt 0) {
    throw "Embedded LKB runtime is present but not executable, and no fallback Python is available. Broken runtime candidates: $($brokenRuntimeCandidates -join ', ')"
  }

  throw 'Python 3.11+ is required. Install Python and ensure `py` or `python` is on PATH.'
}

function Invoke-LkbPythonScript {
  param(
    [string]$ScriptBase,
    [string[]]$Arguments = @(),
    [switch]$AllowPythonFallback
  )

  Set-LkbUtf8

  $scriptDir = Split-Path -Parent $ScriptBase
  $scriptPath = @("${ScriptBase}.py", "${ScriptBase}.pyc") | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if (-not $scriptPath) {
    throw "Entry script not found: $ScriptBase(.py/.pyc)"
  }

  $pythonSpec = Resolve-LkbPython -GatewayRoot $scriptDir -AllowFallback:$AllowPythonFallback
  Push-Location $scriptDir
  try {
    if ($pythonSpec.StartsWith('py ')) {
      $selector = $pythonSpec.Substring(3)
      & py $selector $scriptPath @Arguments
    } else {
      & $pythonSpec $scriptPath @Arguments
    }
    exit $LASTEXITCODE
  } finally {
    Pop-Location
  }
}
