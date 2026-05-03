## [中文 README / Chinese Documentation](README.zh-CN.md)

# Local Knowledge Bridge

`Local Knowledge Bridge` is a local-first gateway for Codex. It searches your own notes, reference libraries, PDFs, Office documents, and folders before the model falls back to memory.

## Project Introduction

<p align="center">
  <img src="assets/lkb-comic.jpg" alt="Four-panel comic: a cat imagines a luxury cat house, searches through messy files, uses lkb, and happily receives the right documents." width="900">
</p>

Your best answers are often already somewhere on your own machine: in an Obsidian note, a Zotero paper, an EndNote attachment, a PDF from last year, or a folder full of project files. The problem is not that the knowledge is missing. The problem is finding the right piece quickly enough to use it.

`Local Knowledge Bridge` gives Codex a local, searchable route into that material. Ask in natural language, invoke `$Local Knowledge Bridge`, mention `Local Knowledge Bridge`, or include `lkb` anywhere in your request, and Codex can search your configured sources before relying on model memory.

## Feature Highlights

- Natural-language first: use it from Codex with `$Local Knowledge Bridge`, `Local Knowledge Bridge`, or `lkb`; no need to manually run search commands for everyday work.
- One bridge for scattered knowledge: connect Obsidian, EndNote, Zotero, and local folders into a single local retrieval layer.
- Local and read-only by default: indexes, logs, models, runtime files, and configuration stay on your machine; the project reads configured sources and does not edit your knowledge base.
- Practical retrieval modes: use `fast` for quick lookup, `balanced` for broader evidence, and optional `deep` for local semantic retrieval and reranking.
- Evidence-oriented answers: make Codex look through your own notes, papers, annotations, and documents before falling back to general model memory.
- Still scriptable when needed: the `lkb_*` commands remain available for setup, diagnostics, rebuilds, automation, and development.

## Supported Sources

| Source | Scope |
| --- | --- |
| `Obsidian` vaults | Markdown notes and note chunks |
| `EndNote` libraries | Library records plus readable PDF, Markdown, text, DOCX, PPTX, and XLSX attachments |
| `Zotero` libraries | Library records, notes, annotations, full-text cache, and readable attachments |
| Local folders | Markdown, text, PDF, DOCX, PPTX, and XLSX files |

## Sponsorship

I'm truly glad this project found you.

I built and open-sourced it with the hope that it can help you in some way: save you time, solve a tricky problem, or simply give you one less thing to worry about on your journey.

May you stay brave, make the most of your time, and charge ahead fearlessly through whatever challenges come your way.

If this project has ever made your day a little easier, and you have the means, you're welcome to buy me a coffee or leave a sponsorship. Every bit of support keeps this project alive and evolving.

| Method | Link |
| --- | --- |
| WeChat | [![WeChat](https://img.shields.io/badge/WeChat-Kiiichi-07C160?logo=wechat&logoColor=white)](https://github.com/kiiichi/local-knowledge-bridge/raw/refs/heads/main/assets/sponsor-wechat.png) |
| PayPal | [![PayPal](https://img.shields.io/badge/PayPal-Kiiichi-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/kiiichi) |

## Prerequisites

| Requirement | Notes |
| --- | --- |
| Windows PowerShell | Used by the setup and deployed command wrappers |
| Python 3.11+ available as `py` or `python` | Check with `py -3 --version` or `python --version` |
| Codex desktop or another Codex setup that uses `%USERPROFILE%\.codex` | The installer deploys the skill and gateway under your Codex home |
| At least one readable local knowledge source | Obsidian, EndNote, Zotero, or a local folder |

## Quick Start

Double-click `lkb_setup.cmd` from the repo root, or run:

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

The setup wizard asks whether to:

- configure the existing deployment
- install or redeploy Local Knowledge Bridge

When the maintenance wizard asks for source paths, paste the raw path without quotes, even if the path contains spaces.

### Setup Choices

When installing or redeploying, `Copy` mode is the normal choice: it copies the gateway and skill into your Codex home so the installed tool stays stable. `Link` mode is mainly for development: the installed gateway and skill point back to this repo, so local source edits take effect without reinstalling.

`deep` mode is optional. It enables local embedding and reranking models for deeper semantic retrieval, but it requires extra dependencies and about 6 GB of model downloads under `gateway/.models/`. Choosing `deep` during the first install can take a long time, especially on a slow network. You can skip it at first and enable it later from the maintenance wizard; `fast` and `balanced` work without loading deep models.

Configuration opens the deployed maintenance wizard. Use it to add or edit Obsidian, EndNote, Zotero, and folder sources, choose route-weight presets, configure deep retrieval, inspect status, and rebuild the database.

### Enable Deep Mode Later

You can skip `deep` during the first install. To enable it later, run the setup entry again and choose the existing deployment path instead of redeploying:

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

Select these wizard options:

1. `Configure existing deployment`
2. `Configure deep retrieval`
3. `Install deep dependencies and prefetch models`

This downloads about 6 GB for the default `BAAI/bge-m3` embedding model and `BAAI/bge-reranker-v2-m3` reranker. The console shows download progress and speed during the prefetch step.

Do not choose `Install or redeploy` just to add `deep`; redeploy is for replacing the installed gateway and skill. Use redeploy only when you intentionally want to reinstall the deployed files.

Check readiness after the download:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
& "$LKB\lkb_doctor.cmd" --json
```

When `deep_status.ready` is `true`, use `--profile deep` in search, ask, or report commands.

### Use It In Codex

After setup, use natural language in Codex. Invoke `$Local Knowledge Bridge`, mention `Local Knowledge Bridge`, or include `lkb` anywhere in the prompt when you want Codex to search your configured local sources first.

| Example |
| --- |
| `$Local Knowledge Bridge: find my notes on transformer model compression and summarize the main methods.` |
| `Based on my Zotero and Obsidian sources, use lkb to find what I have on solid-state battery electrolyte materials.` |
| `Compare my local notes on CRISPR off-target detection methods with Local Knowledge Bridge, and cite the sources you used.` |
| `lkb, use deep mode to make a short report from my local papers about passive linear optics.` |

Choose the LKB output surface that matches the task:

| Mode | Best for | Command | Source policy |
| --- | --- | --- | --- |
| Raw retrieval | Finding and opening candidate local materials. Use this when recall and inspection are more important than a polished answer. | `lkb_search.cmd` | `DATA SOURCES` may list all displayed hits, numbered by final retrieval rank after de-duplication. |
| Evidence report | Reviewing the strongest evidence before writing, comparing sources, or checking what the index found. | `lkb_report.cmd` | `DATA SOURCES` may list all displayed evidence hits because the report is an evidence surface. |
| Answer synthesis | Producing a concise answer grounded in local evidence. Use this for final explanations, decisions, and prose answers. | `lkb_ask.cmd` | `DATA SOURCES` should list only sources cited in the answer body. Useful uncited hits should be separated as `ADDITIONAL RETRIEVED SOURCES`. |

Source numbers are global within an output, such as `[1]`, `[2]`, `[3]`, and should not restart inside `Literature`, `Documents`, or other source-family sections. For `lkb_ask`, use the same numbers inline for claims and analysis that depend on local evidence, for example `... [1]` or `Inference from [1], [3]`.

Run diagnostics from PowerShell:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
& "$LKB\lkb_doctor.cmd" --json
```

## Command Overview

Main deployed commands:

- `lkb_wizard.cmd` - maintenance wizard for source configuration, route weights, deep setup, and index rebuilds
- `lkb_search.cmd` - raw retrieval results for candidate-source inspection
- `lkb_report.cmd` - structured evidence report from retrieved materials
- `lkb_ask.cmd` - answer synthesis from cited local evidence
- `lkb_index.cmd` / `lkb_refresh.cmd` - index status and rebuilds
- `lkb_doctor.cmd` - source, index, service, version, and deep diagnostics
- `lkb_bootstrap_runtime.cmd` - embedded runtime repair and optional deep model prefetch

Search targets:

- `both` - all configured source families
- `obsidian`
- `endnote`
- `zotero`
- `folder`

Retrieval profiles:

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
