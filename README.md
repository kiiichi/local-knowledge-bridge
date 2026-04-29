# Local Knowledge Bridge

`Local Knowledge Bridge` installs a local Codex skill and Windows gateway that search your own knowledge sources before falling back to model memory.

Supported sources:

- `Obsidian` vaults
- `EndNote` libraries and attached PDF, Markdown, text, DOCX, PPTX, and XLSX files
- `Zotero` libraries, notes, annotations, full-text cache, and readable attachments
- Local folder knowledge sources with Markdown, text, PDF, DOCX, PPTX, and XLSX files

All indexes, logs, models, and runtime files stay on the local machine.

## Prerequisites

Install or confirm:

- Windows PowerShell
- Python 3.11+ available as `py` or `python`
- Codex desktop or another Codex setup that uses `%USERPROFILE%\.codex`
- readable local paths for at least one supported source

Check Python:

```powershell
py -3 --version
```

If `py` is not available:

```powershell
python --version
```

## Install

Always start with the guided setup wizard for first-time deployment, redeployment, or configuration:

Double-click `lkb_setup.cmd` from the repo root, or run:

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

The setup wizard first asks whether to configure the existing deployment or install/redeploy. Configuration opens the deployed maintenance wizard, where source paths, route-weight presets, deep settings, and index rebuilds are managed. Deployment can also install deep dependencies and prefetch the default models.

For a normal non-interactive install:

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Copy -BootstrapRuntime
```

For a development install that reflects repo edits immediately:

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Link -BootstrapRuntime
```

If PowerShell blocks script execution:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\lkb_setup.ps1
```

After install, set a PowerShell variable for the deployed gateway path. Examples below use `&` to run commands through that path:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
```

## Configure Sources

For guided source setup, route-weight presets, deep setup, and index rebuilds, start the repo setup wizard and choose `Configure existing deployment`:

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

The setup wizard opens `$LKB\lkb_wizard.cmd` for configuration. Both setup and maintenance wizards edit only `lkb_config.json`; removing an entry from a wizard does not delete your real notes, libraries, attachments, or folders. Long-running setup, deep, and index commands show `[RUNNING]`, `[DONE]`, or `[FAILED]` status; deployed maintenance commands log details to `$LKB\.logs\wizard.log`.

Configure Obsidian:

```powershell
& "$LKB\lkb_configure.cmd" --obsidian "D:\Notes\Vault"
```

Configure EndNote:

```powershell
& "$LKB\lkb_configure.cmd" --endnote "D:\EndNote\My Library.enl" --endnote-name "Main Library"
```

Configure Zotero:

```powershell
& "$LKB\lkb_configure.cmd" --zotero "$env:APPDATA\Zotero\Zotero\Profiles\<profile>\zotero\zotero.sqlite"
```

Configure one or more folder knowledge sources:

```powershell
& "$LKB\lkb_configure.cmd" --folder-library "D:\Research Materials" --folder-name "Research Materials"
& "$LKB\lkb_configure.cmd" --folder-library "E:\Project Files" --folder-name "Project Files"
```

You can configure any supported source combination. Show the current configuration with:

```powershell
& "$LKB\lkb_configure.cmd" --show
```

## Build And Refresh The Index

The setup wizard opens the deployed maintenance wizard for index status, refresh, or full rebuild after confirmation. You can also build the local index manually:

```powershell
& "$LKB\lkb_index.cmd" --force
& "$LKB\lkb_index.cmd" --status
```

Refresh the index after source changes:

```powershell
& "$LKB\lkb_refresh.cmd"
```

To rebuild only an Obsidian folder prefix:

```powershell
& "$LKB\lkb_refresh.cmd" --folder "Projects"
```

## Search, Ask, And Report

Use `fast` for lightweight answers, `balanced` for the default user-facing retrieval flow, and `deep` only after deep setup is complete.

Search:

```powershell
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile balanced --limit 5
```

`both` searches all configured sources. Use `obsidian`, `endnote`, `zotero`, or `folder` to restrict a query to one source family.

Ask:

```powershell
& "$LKB\lkb_ask.cmd" "What is the passive linear optics paper about?" --profile fast --limit 3
```

Report:

```powershell
& "$LKB\lkb_report.cmd" "passive linear optics" --target both --profile balanced --limit 5 --read-top 3
```

`lkb_search`, `lkb_ask`, and `lkb_report` use the local HTTP service by default and start it automatically when needed. Add `--no-service` if you want to run in-process instead.

## Diagnostics And Version Check

Run diagnostics:

```powershell
& "$LKB\lkb_doctor.cmd" --json
```

Check whether GitHub has a newer public release:

```powershell
& "$LKB\lkb_doctor.cmd" --refresh
```

`lkb_doctor --refresh` checks release metadata and reports version status. It does not update the installation automatically.

## Optional: Enable Deep Retrieval

`deep` uses machine-local model files under `.models` and does not download them lazily during a query.

Prepare the runtime and prefetch the deep models:

```powershell
& "$LKB\lkb_bootstrap_runtime.cmd" --include-deep --prefetch-models
```

Check readiness:

```powershell
& "$LKB\lkb_doctor.cmd" --json
```

In the JSON output, `deep_status.ready` should be `true`.

Test deep retrieval:

```powershell
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile deep --limit 5 --no-service
```

If you want GPU deep retrieval, confirm that the embedded runtime can see your NVIDIA GPU:

```powershell
nvidia-smi
& "$LKB\runtime\py311\python.exe" -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

When changing the PyTorch wheel in the embedded runtime, choose the build that matches the CUDA runtime reported by `nvidia-smi` and use the [official PyTorch selector](https://pytorch.org/get-started/locally/).

## Troubleshooting

If PowerShell blocks scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\lkb_setup.ps1
```

If a source path is missing or unreadable:

```powershell
& "$LKB\lkb_configure.cmd" --show
& "$LKB\lkb_doctor.cmd" --json
```

If the service path fails or throws `ConnectionResetError`, inspect the service log and retry with `--no-service` to separate transport issues from retrieval behavior:

```powershell
Get-Content "$LKB\.logs\service.log" -Tail 80
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile balanced --limit 5 --no-service
```

If `deep_status.ready` is `false`, rerun:

```powershell
& "$LKB\lkb_bootstrap_runtime.cmd" --include-deep --prefetch-models
```

If model prefetch fails with a network timeout, retry when network access is available.

## Machine-Local Data

Do not copy these generated paths between machines from the deployed gateway root:

- `runtime/`
- `.index/`
- `.cache/`
- `.logs/`
- `.models/`
- `lkb_config.json`

On each new machine, install the gateway, configure local source paths, prefetch deep models if needed, and build the index locally.
