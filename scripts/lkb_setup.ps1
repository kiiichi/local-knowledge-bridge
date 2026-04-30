param(
  [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' })
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section {
  param([string]$Title)
  Write-Host ""
  Write-Host ("=" * $Title.Length)
  Write-Host $Title
  Write-Host ("=" * $Title.Length)
}

function Read-Default {
  param(
    [string]$Prompt,
    [string]$Default = ''
  )
  if ($Default) {
    $value = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($value)) {
      return $Default
    }
    return $value
  }
  return (Read-Host $Prompt)
}

function Confirm-Setup {
  param(
    [string]$Prompt,
    [bool]$Default = $false
  )
  $suffix = if ($Default) { '[Y/n]' } else { '[y/N]' }
  $value = (Read-Host "$Prompt $suffix").Trim().ToLowerInvariant()
  if (-not $value) {
    return $Default
  }
  return @('y', 'yes') -contains $value
}

function Invoke-SetupCommand {
  param(
    [string]$Label,
    [string[]]$Command
  )
  $started = Get-Date
  Write-Host "[RUNNING] $Label"
  & $Command[0] @($Command | Select-Object -Skip 1)
  $exitCode = $LASTEXITCODE
  $elapsed = ((Get-Date) - $started).TotalSeconds.ToString('0.0')
  if ($exitCode -ne 0) {
    Write-Host "[FAILED] $Label (${elapsed}s) exit $exitCode"
    exit $exitCode
  }
  Write-Host "[DONE] $Label (${elapsed}s)"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$installScript = Join-Path $PSScriptRoot 'install_windows.ps1'
$functionRoot = Join-Path $CodexHome 'Function'
$gatewayTarget = Join-Path $functionRoot 'local_knowledge_bridge'
$wizardCmd = Join-Path $gatewayTarget 'lkb_wizard.cmd'

Write-Section 'Local Knowledge Bridge Setup'
Write-Host "Repo root : $repoRoot"
Write-Host "Codex home: $CodexHome"
Write-Host "Gateway   : $gatewayTarget"
Write-Host "Path input: in the maintenance wizard, paste raw paths without quotes, even if they contain spaces."

Write-Host ""
Write-Host "1. Configure existing deployment (source paths, deep setup, status, index rebuild)"
Write-Host "2. Install or redeploy (replace deployed gateway/skill files)"
$actionDefault = if (Test-Path -LiteralPath $wizardCmd) { '1' } else { '2' }
$action = Read-Default -Prompt 'Select action' -Default $actionDefault
if ($action -in @('1', 'configure', 'config')) {
  if (-not (Test-Path -LiteralPath $wizardCmd)) {
    Write-Host "Maintenance wizard was not found: $wizardCmd"
    Write-Host 'Run this setup again and choose Install or redeploy first.'
    exit 1
  }
  Invoke-SetupCommand -Label 'Open LKB maintenance wizard' -Command @($wizardCmd)
  exit 0
}
if ($action -notin @('2', 'install', 'deploy', 'redeploy')) {
  throw "Unsupported setup action: $action"
}

$mode = Read-Default -Prompt 'Install mode: Copy or Link' -Default 'Copy'
$mode = switch ($mode.ToLowerInvariant()) {
  'copy' { 'Copy' }
  'link' { 'Link' }
  default { $mode }
}
if ($mode -notin @('Copy', 'Link')) {
  throw "Unsupported install mode: $mode"
}

$force = $false
if (Test-Path -LiteralPath $gatewayTarget) {
  Write-Host ""
  Write-Host "Existing deployment detected: $gatewayTarget"
  Write-Host "To enable deep later, choose Configure existing deployment instead of redeploy."
  Write-Host "Redeploy replaces the installed gateway/skill files; machine-local state may need to be rebuilt."
  $force = Confirm-Setup -Prompt 'Redeploy and replace the existing gateway/skill install?' -Default $false
  if (-not $force) {
    Write-Host 'Setup cancelled before deployment.'
    exit 0
  }
}

Write-Host ""
Write-Host "Deep mode is optional. It downloads about 6 GB of local models for semantic retrieval and reranking."
Write-Host "You can skip it now and enable it later with: lkb_setup -> Configure existing deployment -> Configure deep retrieval."
$installDeep = Confirm-Setup -Prompt 'Install deep dependencies and prefetch default models now?' -Default $false
$openWizardAfterDeploy = Confirm-Setup -Prompt 'Open the maintenance wizard after deployment for source configuration and index rebuild?' -Default $true

Write-Section 'Summary'
Write-Host "Action      : deploy"
Write-Host "Mode        : $mode"
Write-Host "Redeploy    : $force"
Write-Host "Deep setup  : $installDeep"
Write-Host "Open wizard : $openWizardAfterDeploy"
if (-not (Confirm-Setup -Prompt 'Continue with setup?' -Default $true)) {
  Write-Host 'Setup cancelled.'
  exit 0
}

$installArgs = @(
  'powershell',
  '-NoProfile',
  '-ExecutionPolicy',
  'Bypass',
  '-File',
  $installScript,
  '-Mode',
  $mode,
  '-BootstrapRuntime'
)
if ($force) {
  $installArgs += '-Force'
}
if ($installDeep) {
  $installArgs += '-IncludeDeepDeps'
  $installArgs += '-PrefetchModels'
}
Invoke-SetupCommand -Label 'Install Local Knowledge Bridge' -Command $installArgs

if ($openWizardAfterDeploy) {
  Invoke-SetupCommand -Label 'Open LKB maintenance wizard' -Command @($wizardCmd)
}

Write-Section 'Done'
Write-Host "Gateway: $gatewayTarget"
Write-Host "Maintenance wizard: $gatewayTarget\lkb_wizard.cmd"
