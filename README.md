# Local Knowledge Bridge

`Local Knowledge Bridge` is a local-first gateway for Codex. It searches your own notes, reference libraries, PDFs, Office documents, and folders before the model falls back to memory.

`Local Knowledge Bridge` 是一个本地优先的 Codex 知识网关。它会在模型依赖自身记忆之前，先检索你的笔记、文献库、PDF、Office 文档和本地文件夹。

## Project Introduction / 项目介绍

**English**

This project installs the `Local Knowledge Bridge` Codex skill and supporting Windows gateway commands on your machine. In everyday use, just ask Codex in natural language and invoke the skill as `$Local Knowledge Bridge`, mention `Local Knowledge Bridge`, or include `lkb` anywhere in your request so Codex knows to search your local sources first.

After configuration, you can connect Obsidian, EndNote, Zotero, and regular folders into one local knowledge bridge. The command-line tools remain available for setup, diagnostics, scripting, and development, while the intended user experience is natural-language access inside Codex.

All indexes, logs, models, runtime files, and configuration stay on your machine. By default, the project reads only the sources you configure and does not edit your knowledge base.

**中文**

这个项目会在你的 Windows 机器上安装 `Local Knowledge Bridge` Codex skill 和配套的 Windows 网关命令。日常使用时，只要用自然语言向 Codex 提问，并使用 `$Local Knowledge Bridge` 调用 skill，写出 `Local Knowledge Bridge`，或者在请求中的任意位置加入 `lkb`，Codex 就会知道应当先检索你的本地资料。

配置完成后，你可以把 Obsidian、EndNote、Zotero 和普通文件夹接入同一个本地知识桥。命令行工具仍然可用于安装、诊断、脚本化和开发；面向用户的主要体验是在 Codex 中用自然语言访问本地知识。

所有索引、日志、模型、运行时文件和配置都保留在本机。项目默认只读取你配置的数据源，不会对你的知识库做任何编辑操作。

**Supported Sources / 支持的数据源**

| English | 中文 |
| --- | --- |
| `Obsidian` vaults | `Obsidian` 知识库 |
| `EndNote` libraries and readable PDF, Markdown, text, DOCX, PPTX, and XLSX attachments | `EndNote` 文献库，以及可读取的 PDF、Markdown、文本、DOCX、PPTX、XLSX 附件 |
| `Zotero` libraries, notes, annotations, full-text cache, and readable attachments | `Zotero` 文献库、笔记、批注、全文缓存和可读取附件 |
| Local folders containing Markdown, text, PDF, DOCX, PPTX, and XLSX files | 本地文件夹中的 Markdown、文本、PDF、DOCX、PPTX、XLSX 文件 |

## Sponsorship / 赞助

| Method / 支持方式 | Link / 链接 |
| --- | --- |
| WeChat / 微信 | [![WeChat](https://img.shields.io/badge/WeChat-Kiiichi-07C160?logo=wechat&logoColor=white)](https://github.com/kiiichi/local-knowledge-bridge/raw/refs/heads/main/sponsor-wechat.png) |
| PayPal | [![PayPal](https://img.shields.io/badge/PayPal-Kiiichi-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/kiiichi) |

**English**

I'm truly glad this project found you.

I built and open-sourced it with the hope that it can help you in some way: save you time, solve a tricky problem, or simply give you one less thing to worry about on your journey.

May you stay brave, make the most of your time, and charge ahead fearlessly through whatever challenges come your way.

If this project has ever made your day a little easier, and you have the means, you're welcome to buy me a coffee or leave a sponsorship. Every bit of support keeps this project alive and evolving.

**中文**

很高兴这个项目能遇见你。

我把它开源出来，是真心希望它能为你带来一点帮助。也许是节省一段摸索的时间，也许是解决一个棘手的问题，又或者是成为你前行的路上，一块小小的垫脚石。

愿你始终勇敢，不负韶华，在属于自己的征途上披荆斩棘、一往无前。

如果这个项目曾在某个时刻照亮过你，而你恰好有余力，欢迎请我喝杯咖啡，或者留下一份赞助。你的每一份支持，都会让这个工具走得更远，也让我更有动力把它打磨得更好。

## Prerequisites / 前期准备

| English | 中文 |
| --- | --- |
| Windows PowerShell | Windows PowerShell |
| Python 3.11+ available as `py` or `python` | Python 3.11+，可通过 `py` 或 `python` 调用 |
| Codex desktop or another Codex setup that uses `%USERPROFILE%\.codex` | Codex desktop，或其他使用 `%USERPROFILE%\.codex` 的 Codex 环境 |
| At least one readable local knowledge source | 至少一个可读取的本地知识源 |

Check Python / 检查 Python:

```powershell
py -3 --version
```

If `py` is not available / 如果 `py` 不可用:

```powershell
python --version
```

## Quick Start / 快速启动

**English**

Double-click `lkb_setup.cmd` from the repo root, or run:

**中文**

在仓库根目录双击 `lkb_setup.cmd`，或在 PowerShell 中运行：

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

The setup wizard asks whether to / 安装向导会询问你要执行哪一种操作:

- configure the existing deployment / 配置已有部署
- install or redeploy Local Knowledge Bridge / 安装或重新部署 Local Knowledge Bridge

### Setup Choices / 安装选项

When installing or redeploying, `Copy` mode is the normal choice: it copies the gateway and skill into your Codex home so the installed tool stays stable. `Link` mode is mainly for development: the installed gateway and skill point back to this repo, so local source edits take effect without reinstalling.

安装或重新部署时，`Copy` 模式是普通用户的默认选择：它会把 gateway 和 skill 复制到你的 Codex home，让已安装工具保持稳定。`Link` 模式主要用于开发：已安装的 gateway 和 skill 会指向当前仓库，因此本地源码改动不需要重新安装就能生效。

`deep` mode is optional. It enables local embedding and reranking models for deeper semantic retrieval, but it requires extra dependencies and model downloads under `gateway/.models/`. You can skip it at first; `fast` and `balanced` work without loading deep models.

`deep` 模式是可选项。它会启用本地 embedding 和 reranking 模型，用于更深入的语义检索，但需要额外依赖，并会在 `gateway/.models/` 下下载模型。你可以先跳过它；`fast` 和 `balanced` 不需要加载 deep 模型也能使用。

Configuration opens the deployed maintenance wizard. Use it to add or edit Obsidian, EndNote, Zotero, and folder sources, choose route-weight presets, configure deep retrieval, inspect status, and rebuild the database.

选择配置后，会打开已部署的维护向导。你可以在其中添加或编辑 Obsidian、EndNote、Zotero 和文件夹数据源，选择 route-weight 预设，配置 deep 检索，查看状态，并重建数据库。

### Use It In Codex / 在 Codex 中使用

After setup, use natural language in Codex. Invoke `$Local Knowledge Bridge`, mention `Local Knowledge Bridge`, or include `lkb` anywhere in the prompt when you want Codex to search your configured local sources first.

完成设置后，请在 Codex 中用自然语言使用它。当你希望 Codex 优先检索已配置的本地资料时，可以使用 `$Local Knowledge Bridge`，显式写出 `Local Knowledge Bridge`，或者在提示词中的任意位置加入 `lkb`。

| English example | 中文示例 |
| --- | --- |
| `$Local Knowledge Bridge: find my notes on transformer model compression and summarize the main methods.` | `$Local Knowledge Bridge：查找我关于 Transformer 模型压缩的笔记，并总结主要方法。` |
| `Based on my Zotero and Obsidian sources, use lkb to find what I have on solid-state battery electrolyte materials.` | `基于我的 Zotero 和 Obsidian 资料，用 lkb 查找我关于固态电池电解质材料有哪些内容。` |
| `Compare my local notes on CRISPR off-target detection methods with Local Knowledge Bridge, and cite the sources you used.` | `用 Local Knowledge Bridge 对比我本地关于 CRISPR 脱靶检测方法的笔记，并说明使用了哪些来源。` |
| `lkb, make a short report from my local papers about passive linear optics.` | `lkb，基于我的本地论文整理一份关于被动线性光学的简短报告。` |

Run diagnostics from PowerShell / 在 PowerShell 中运行诊断:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
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
