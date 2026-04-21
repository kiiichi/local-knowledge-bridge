param(
  [ValidateSet('Copy', 'Link')]
  [string]$Mode = 'Copy',
  [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }),
  [switch]$BootstrapRuntime,
  [switch]$IncludeDeepDeps,
  [switch]$PrefetchModels,
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Remove-ExistingTarget {
  param([string]$PathValue)
  if (-not (Test-Path -LiteralPath $PathValue)) {
    return
  }
  Remove-Item -LiteralPath $PathValue -Recurse -Force
}

function Copy-Or-LinkDirectory {
  param(
    [string]$Source,
    [string]$Target,
    [string]$InstallMode
  )

  if (Test-Path -LiteralPath $Target) {
    if (-not $Force) {
      throw "Target already exists. Re-run with -Force to replace: $Target"
    }
    Remove-ExistingTarget -PathValue $Target
  }

  if ($InstallMode -eq 'Copy') {
    Copy-Item -LiteralPath $Source -Destination $Target -Recurse
    return
  }

  New-Item -ItemType Junction -Path $Target -Target $Source | Out-Null
}

function Resolve-PythonCommand {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    foreach ($selector in @('-3.11', '-3.12', '-3.13', '-3')) {
      try {
        & $py.Source $selector -c "import sys; assert sys.version_info >= (3, 11)" *> $null
        if ($LASTEXITCODE -eq 0) {
          return @($py.Source, $selector)
        }
      } catch {
      }
    }
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    try {
      & $python.Source -c "import sys; assert sys.version_info >= (3, 11)" *> $null
      if ($LASTEXITCODE -eq 0) {
        return @($python.Source)
      }
    } catch {
    }
  }
  throw 'Python 3.11+ is required. Install Python and ensure `py` or `python` is on PATH.'
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$skillSource = Join-Path $repoRoot 'skill'
$gatewaySource = Join-Path $repoRoot 'gateway'

if (-not (Test-Path -LiteralPath $skillSource)) {
  throw "Missing skill source directory: $skillSource"
}
if (-not (Test-Path -LiteralPath $gatewaySource)) {
  throw "Missing gateway source directory: $gatewaySource"
}

$skillsRoot = Join-Path $CodexHome 'skills'
$functionRoot = Join-Path $CodexHome 'Function'
$skillTarget = Join-Path $skillsRoot 'local-knowledge-bridge'
$gatewayTarget = Join-Path $functionRoot 'local_knowledge_bridge'

New-Item -ItemType Directory -Force -Path $skillsRoot, $functionRoot | Out-Null

Copy-Or-LinkDirectory -Source $skillSource -Target $skillTarget -InstallMode $Mode
Copy-Or-LinkDirectory -Source $gatewaySource -Target $gatewayTarget -InstallMode $Mode

$configTemplate = Join-Path $gatewayTarget 'templates\lkb_config.template.json'
$configTarget = Join-Path $gatewayTarget 'lkb_config.json'
if ((Test-Path -LiteralPath $configTemplate) -and -not (Test-Path -LiteralPath $configTarget)) {
  Copy-Item -LiteralPath $configTemplate -Destination $configTarget
}

if ($BootstrapRuntime -or $PrefetchModels) {
  $pythonCmd = Resolve-PythonCommand
  $bootstrapScript = Join-Path $gatewayTarget 'lkb_bootstrap_runtime.py'
  $bootstrapArgs = @($bootstrapScript)
  if ($IncludeDeepDeps) {
    $bootstrapArgs += '--include-deep'
  }
  if ($PrefetchModels) {
    $bootstrapArgs += '--prefetch-models'
  }
  if ($pythonCmd.Count -eq 2) {
    & $pythonCmd[0] $pythonCmd[1] @bootstrapArgs
  } else {
    & $pythonCmd[0] @bootstrapArgs
  }
}

Write-Host "Installed Local Knowledge Bridge"
Write-Host "  Codex home : $CodexHome"
Write-Host "  Skill      : $skillTarget"
Write-Host "  Gateway    : $gatewayTarget"
Write-Host "  Mode       : $Mode"
