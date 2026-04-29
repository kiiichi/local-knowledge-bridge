# Local Knowledge Bridge

Respons:
[![微信支付](https://img.shields.io/badge/微信-Kiiichi-green?logo=wechat)](sponsor-wechat.png)
[![PayPal](https://img.shields.io/badge/PayPal-Kiiichi-blue?logo=paypal)](https://www.paypal.com/paypalme/kiiichi)


`Local Knowledge Bridge` installs a local Codex skill and Windows gateway that searches your own notes, reference libraries, PDFs, Office documents, and folders before falling back to model memory.

Supported sources:

- `Obsidian` vaults
- `EndNote` libraries and attached PDF, Markdown, text, DOCX, PPTX, and XLSX files
- `Zotero` libraries, notes, annotations, full-text cache, and readable attachments
- Local folder knowledge sources with Markdown, text, PDF, DOCX, PPTX, and XLSX files

All indexes, logs, models, runtime files, and configuration stay on the local machine.

## Prerequisites

- Windows PowerShell
- Python 3.11+ available as `py` or `python`
- Codex desktop or another Codex setup that uses `%USERPROFILE%\.codex`
- At least one readable local knowledge source

Check Python:

```powershell
py -3 --version
```

If `py` is not available:

```powershell
python --version
```

## Quick Start

Double-click `lkb_setup.cmd` from the repo root, or run:

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

The setup wizard asks whether to:

- configure the existing deployment
- install or redeploy Local Knowledge Bridge

Configuration opens the deployed maintenance wizard. Use it to add or edit Obsidian, EndNote, Zotero, and folder sources, choose route-weight presets, configure deep retrieval, inspect status, and rebuild the database.

After setup, search everything configured:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile balanced --limit 5
```

Ask a question:

```powershell
& "$LKB\lkb_ask.cmd" "What is the passive linear optics paper about?" --profile fast --limit 3
```

Run diagnostics:

```powershell
& "$LKB\lkb_doctor.cmd" --json
```

## Command Overview

Main deployed commands:

- `lkb_wizard.cmd` - maintenance wizard for source configuration, route weights, deep setup, and index rebuilds
- `lkb_search.cmd` - raw retrieval results
- `lkb_ask.cmd` - answer synthesis from local evidence
- `lkb_report.cmd` - structured report from retrieved evidence
- `lkb_index.cmd` / `lkb_refresh.cmd` - index status and rebuilds
- `lkb_doctor.cmd` - source, index, service, version, and deep diagnostics
- `lkb_bootstrap_runtime.cmd` - embedded runtime repair and optional deep model prefetch

Search targets:

- `both` - all configured source families
- `obsidian`
- `endnote`
- `zotero`
- `folder`

Profiles:

- `fast` - lightweight local retrieval, default for quick answers
- `balanced` - broader lightweight retrieval
- `deep` - semantic scoring and reranking with local models

## Install And Configuration Details

The guided entry is always:

```powershell
.\lkb_setup.cmd
```

For non-interactive install:

```powershell
.\scripts\install_windows.ps1 -Mode Copy -BootstrapRuntime
```

For development install that reflects repo edits immediately:

```powershell
.\scripts\install_windows.ps1 -Mode Link -BootstrapRuntime
```

If PowerShell blocks scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\lkb_setup.ps1
```

Manual source configuration remains available:

```powershell
& "$LKB\lkb_configure.cmd" --obsidian "D:\Notes\Vault"
& "$LKB\lkb_configure.cmd" --endnote "D:\EndNote\My Library.enl" --endnote-name "Main Library"
& "$LKB\lkb_configure.cmd" --zotero "$env:APPDATA\Zotero\Zotero\Profiles\<profile>\zotero\zotero.sqlite"
& "$LKB\lkb_configure.cmd" --folder-library "D:\Research Materials" --folder-name "Research Materials"
```

The wizards and CLI only edit LKB configuration and generated indexes. Removing a source entry does not delete your real notes, libraries, attachments, or folders.

## Indexing

Build or rebuild the local database:

```powershell
& "$LKB\lkb_index.cmd" --force
```

Show index status:

```powershell
& "$LKB\lkb_index.cmd" --status
```

Refresh after source changes:

```powershell
& "$LKB\lkb_refresh.cmd"
```

## Optional Deep Retrieval

`deep` uses machine-local model files under `.models` and does not download them lazily during a query.

Prepare deep dependencies and prefetch the default models:

```powershell
& "$LKB\lkb_bootstrap_runtime.cmd" --include-deep --prefetch-models
```

Check readiness:

```powershell
& "$LKB\lkb_doctor.cmd" --json
```

Test deep retrieval:

```powershell
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile deep --limit 5 --no-service
```

If you want GPU deep retrieval, confirm the embedded runtime can see CUDA:

```powershell
nvidia-smi
& "$LKB\runtime\py311\python.exe" -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

## Development

Run the test suite from the repo root:

```powershell
python -m unittest discover -s gateway\tests
```

Compile-check the main entrypoints:

```powershell
python -m py_compile gateway\lkb_wizard.py gateway\src\local_knowledge_bridge\wizard.py gateway\src\local_knowledge_bridge\terminal_ui.py
```

Source code lives under:

- `gateway/lkb_*.py` - CLI entrypoints
- `gateway/src/local_knowledge_bridge/` - shared implementation modules
- `gateway/templates/lkb_config.template.json` - default config
- `scripts/` - repo install/setup scripts
- `skill/` - installed Codex skill content

Generated local state is intentionally not committed:

- `gateway/runtime/`
- `gateway/.cache/`
- `gateway/.index/`
- `gateway/.logs/`
- `gateway/.models/`
- `gateway/lkb_config.json`

## Troubleshooting

If a source path is missing or unreadable:

```powershell
& "$LKB\lkb_configure.cmd" --show
& "$LKB\lkb_doctor.cmd" --json
```

If the service path fails or throws `ConnectionResetError`, inspect the service log and retry with `--no-service`:

```powershell
Get-Content "$LKB\.logs\service.log" -Tail 80
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile balanced --limit 5 --no-service
```

If `deep_status.ready` is `false`, rerun:

```powershell
& "$LKB\lkb_bootstrap_runtime.cmd" --include-deep --prefetch-models
```
