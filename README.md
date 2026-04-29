# Local Knowledge Bridge

`Local Knowledge Bridge` is a local-first gateway for Codex. It searches your own notes, reference libraries, PDFs, Office documents, and folders before the model falls back to memory.

`Local Knowledge Bridge` 是一个本地优先的 Codex 知识网关。它会在模型依赖自身记忆之前，先检索你的笔记、文献库、PDF、Office 文档和本地文件夹。

## Project Introduction / 项目介绍

**中文**

这个项目会在你的 Windows 机器上安装一个本地 Codex skill 和一组 `lkb_*` 网关命令。配置完成后，你可以把 Obsidian、EndNote、Zotero 和普通文件夹接入同一个本地索引，用 `lkb_search` 检索证据，用 `lkb_ask` 基于本地材料回答问题，也可以在需要时启用本地 deep 检索。

所有索引、日志、模型、运行时文件和配置都保留在本机。项目默认只读取你配置的数据源，不会把你的知识库复制到仓库里。

**English**

This project installs a local Codex skill and a set of `lkb_*` gateway commands on your Windows machine. After configuration, you can connect Obsidian, EndNote, Zotero, and regular folders into one local index, retrieve evidence with `lkb_search`, answer from local material with `lkb_ask`, and optionally enable local deep retrieval.

All indexes, logs, models, runtime files, and configuration stay on your machine. By default, the project reads only the sources you configure and does not copy your knowledge base into the repository.

**支持的数据源 / Supported Sources**

| 中文 | English |
| --- | --- |
| `Obsidian` 知识库 | `Obsidian` vaults |
| `EndNote` 文献库，以及可读取的 PDF、Markdown、文本、DOCX、PPTX、XLSX 附件 | `EndNote` libraries and readable PDF, Markdown, text, DOCX, PPTX, and XLSX attachments |
| `Zotero` 文献库、笔记、批注、全文缓存和可读取附件 | `Zotero` libraries, notes, annotations, full-text cache, and readable attachments |
| 本地文件夹中的 Markdown、文本、PDF、DOCX、PPTX、XLSX 文件 | Local folders containing Markdown, text, PDF, DOCX, PPTX, and XLSX files |

## Sponsorship / 赞助

| 支持方式 / Method | 链接 / Link |
| --- | --- |
| 微信 / WeChat | [![WeChat](https://img.shields.io/badge/WeChat-Kiiichi-07C160?logo=wechat&logoColor=white)](sponsor-wechat.png) |
| PayPal | [![PayPal](https://img.shields.io/badge/PayPal-Kiiichi-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/kiiichi) |

**中文**

很高兴这个项目能遇见你。

我把它开源出来，是真心希望它能为你带来一点帮助。也许是节省一段摸索的时间，也许是解决一个棘手的问题，又或者是成为你前行的路上，一块小小的垫脚石。

愿你始终勇敢，不负韶华，在属于自己的征途上披荆斩棘、一往无前。

如果这个项目曾在某个时刻照亮过你，而你恰好有余力，欢迎请我喝杯咖啡，或者留下一份赞助。你的每一份支持，都会让这个工具走得更远，也让我更有动力把它打磨得更好。

**English**

I'm truly glad this project found you.

I built and open-sourced it with the hope that it can help you in some way: save you time, solve a tricky problem, or simply give you one less thing to worry about on your journey.

May you stay brave, make the most of your time, and charge ahead fearlessly through whatever challenges come your way.

If this project has ever made your day a little easier, and you have the means, you're welcome to buy me a coffee or leave a sponsorship. Every bit of support keeps this project alive and evolving.

## Prerequisites / 前期准备

| 中文 | English |
| --- | --- |
| Windows PowerShell | Windows PowerShell |
| Python 3.11+，可通过 `py` 或 `python` 调用 | Python 3.11+ available as `py` or `python` |
| Codex desktop，或其他使用 `%USERPROFILE%\.codex` 的 Codex 环境 | Codex desktop or another Codex setup that uses `%USERPROFILE%\.codex` |
| 至少一个可读取的本地知识源 | At least one readable local knowledge source |

检查 Python / Check Python:

```powershell
py -3 --version
```

如果 `py` 不可用，请改用 `python` / If `py` is not available:

```powershell
python --version
```

## Quick Start / 快速启动

**中文**

在仓库根目录双击 `lkb_setup.cmd`，或在 PowerShell 中运行：

**English**

Double-click `lkb_setup.cmd` from the repo root, or run:

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

安装向导会询问你要执行哪一种操作 / The setup wizard asks whether to:

- 配置已有部署 / configure the existing deployment
- 安装或重新部署 Local Knowledge Bridge / install or redeploy Local Knowledge Bridge

选择配置后，会打开已部署的维护向导。你可以在其中添加或编辑 Obsidian、EndNote、Zotero 和文件夹数据源，选择 route-weight 预设，配置 deep 检索，查看状态，并重建数据库。

Configuration opens the deployed maintenance wizard. Use it to add or edit Obsidian, EndNote, Zotero, and folder sources, choose route-weight presets, configure deep retrieval, inspect status, and rebuild the database.

完成设置后，检索所有已配置的数据源 / After setup, search everything configured:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile balanced --limit 5
```

基于本地材料提问 / Ask a question:

```powershell
& "$LKB\lkb_ask.cmd" "What is the passive linear optics paper about?" --profile fast --limit 3
```

运行诊断 / Run diagnostics:

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
