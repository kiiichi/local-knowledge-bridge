. (Join-Path $PSScriptRoot 'lkb_common.ps1')
Invoke-LkbPythonScript -ScriptBase (Join-Path $PSScriptRoot 'lkb_bootstrap_runtime') -Arguments $args -AllowPythonFallback
