# Local Knowledge Bridge

`Local Knowledge Bridge` is an open-source, Windows-first repository for building and deploying a local Codex knowledge skill backed by the user's own files.

The current V1 target is:

- `Obsidian`
- `EndNote`

This repository is intended to be:

- the canonical source repo for development
- the deployment source for Windows users
- the shared layout used across devices

The V1 lexical milestone is implemented. This repository already contains:

- skill metadata and prompt surface
- gateway directory layout
- Windows install and deployment scripts
- config templates
- wrapper scripts and working command entrypoints
- runtime bootstrap support
- SQLite index schema and index builder
- Obsidian note and chunk indexing
- EndNote metadata, attachment, and PDF full-text indexing
- lexical retrieval with weighted route fusion
- a local HTTP service for `ask`, `search`, and `report`

## Repository Layout

```text
local-knowledge-bridge/
+- skill/
|  +- SKILL.md
|  +- agents/openai.yaml
+- gateway/
|  +- lkb_*.cmd / lkb_*.ps1 / lkb_*.py
|  +- templates/lkb_config.template.json
|  +- requirements.runtime.txt
|  +- requirements.deep.txt
|  +- VERSION
|  +- VERSION_PREFIX
|  +- src/local_knowledge_bridge/
+- scripts/
   +- install_windows.cmd
   +- install_windows.ps1
```

## Naming Convention

- `kb_*` is reserved for the legacy reference package under `function/kb_gateway/` and `skills/kb-answer/`.
- `lkb_*` is the active engineering command surface for `Local Knowledge Bridge`.
- New implementation work in this repository should use `lkb_*` consistently.

## What Gets Deployed

When installed, this repository deploys to:

- skill:
  - `C:\Users\<you>\.codex\skills\local-knowledge-bridge`
- gateway:
  - `C:\Users\<you>\.codex\Function\local_knowledge_bridge`

The repository source should remain clean. Runtime-generated files are not committed:

- `gateway/runtime/`
- `gateway/.cache/`
- `gateway/.index/`
- `gateway/.logs/`
- `gateway/.models/`
- `gateway/lkb_config.json`

On a real installation, those are created in the deployed gateway directory.

## Install On Windows

### Prerequisites

- Windows PowerShell
- Codex desktop or another Codex environment that uses `~/.codex`
- Python 3.11+ available as `py` or `python`

### Option 1: Normal Install

Copy the skill and gateway into your `.codex` directory:

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1
```

### Option 2: Development Install

Use directory junctions so edits in the repo are reflected immediately in the deployed Codex directories:

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Link
```

This is the recommended mode for active development.

## Bootstrap The Gateway Runtime

After installation, create a local Python runtime for the gateway:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd
```

To include deep-mode dependencies during bootstrap:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd --include-deep
```

The bootstrap step creates:

- `runtime/py311/`
- a default `lkb_config.json` if missing
- installed Python dependencies inside the gateway runtime

The runtime requirements currently include:

- `PyYAML`
- `pypdf`
- `cryptography`

`cryptography` is included so AES-encrypted PDFs can be parsed when `pypdf` needs that backend.

## Configure Data Sources

After bootstrap, point the gateway at your own local data:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --obsidian "D:\Notes\Vault"
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --endnote "D:\EndNote\My Library.enl" --endnote-name "Main Library"
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --show
```

## Build The Index

After configuration, build the local index:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --force
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --status
```

The default index database is:

- `C:\Users\<you>\.codex\Function\local_knowledge_bridge\.index\lkb_index.sqlite`

## Query The Local Knowledge Base

Primary answer flow:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_ask.cmd "passive linear optics 这篇文献是什么？"
```

Raw merged search:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "passive linear optics" --profile balanced --limit 10
```

Structured report:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_report.cmd "passive linear optics" --target both --profile balanced --limit 8 --read-top 3
```

JSON output is available on the main commands:

- `lkb_search.cmd ... --json`
- `lkb_ask.cmd ... --json`
- `lkb_report.cmd ... --json`

## Service Mode

`Local Knowledge Bridge` is `service-first`.

- `lkb_search`, `lkb_ask`, and `lkb_report` default to the local HTTP service
- `--no-service` forces direct in-process execution
- the default service address is `127.0.0.1:53744`

You can start the service explicitly:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_service.cmd
```

The service exposes:

- `GET /health`
- `POST /search`
- `POST /ask`
- `POST /report`
- `POST /shutdown`

## Current Status

Implemented now in V1:

- installation and deployment scripts
- gateway runtime bootstrap
- local config creation and editing
- `lkb_index`
- `lkb_search`
- `lkb_ask`
- `lkb_report`
- `lkb_service`
- `lkb_doctor`
- SQLite FTS5 lexical retrieval across Obsidian and EndNote
- EndNote PDF full-text extraction with locator-aware chunks
- weighted route fusion across metadata, attachments, and full text

Current V1 limitations:

- `fast` and `balanced` are implemented as lexical retrieval profiles
- `deep` is reserved but not implemented yet
- `lkb_eval` remains scaffolded
- diagnostics are intentionally minimal in this milestone

## Current Verified State In This Workspace

These facts were verified on this machine during the current implementation pass:

- configured Obsidian vault:
  - `C:\Users\kichi\Documents\kichi@git\kc-notes`
- configured EndNote library:
  - `C:\Users\kichi\Documents\My EndNote Library.enl`
- active engineering service port:
  - `127.0.0.1:53744`
- current index snapshot after the latest successful full rebuild:
  - `obsidian_notes = 112`
  - `obsidian_chunks = 1994`
  - `endnote_docs = 583`
  - `endnote_attachments = 655`
  - `endnote_fulltext = 29511`
- latest full rebuild status:
  - completed successfully
  - `warnings = []`
- service lifecycle:
  - `lkb_search` can auto-start the service
  - `/health` and `/shutdown` were both verified
- `deep` behavior:
  - currently fails explicitly with a not-implemented message

Important validation nuance:

- the latest full-corpus `lkb_index --force` succeeded before the final `pdf_text.py` logging-suppression adjustment
- after that final adjustment, targeted extraction of several large PDFs was rechecked successfully without noisy console output
- if you want to reconfirm the final PDF logging behavior end-to-end, rerun `lkb_index.cmd --force`

## Testing

Recommended test order on Windows:

1. Verify configuration and runtime:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --show
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_doctor.cmd --json
```

2. Verify index status:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --status
```

3. If needed, rebuild the index:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --force
```

4. Test direct lexical search without the service:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "passive linear optics" --profile balanced --limit 5 --no-service
```

5. Test answer generation without the service:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_ask.cmd "passive linear optics 这篇文献是什么？" --limit 3 --no-service
```

6. Test structured report output:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_report.cmd "passive linear optics" --profile balanced --limit 3 --json --no-service
```

7. Test the default service-first path:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "passive linear optics" --limit 3
```

8. Test the service endpoints explicitly:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:53744/health" | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:53744/shutdown" | ConvertTo-Json -Depth 4
```

9. Confirm the current V1 `deep` placeholder behavior:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "passive linear optics" --profile deep --no-service
```

Expected result:

- the command should fail clearly with a not-implemented message

## Cross-Device Workflow

Use this repository as the source of truth on every machine.

Recommended flow:

1. Clone or download this repository on the new machine.
2. Run `scripts/install_windows.ps1`.
3. Run `lkb_bootstrap_runtime.cmd`.
4. Configure the local source paths for that machine.
5. Build indexes on that machine with `lkb_index.cmd --force`.

Do not copy these between devices:

- `.index`
- `.logs`
- `.cache`
- `.models` unless you intentionally want to reuse downloaded deep models
- `lkb_config.json` if source paths differ

## Development Notes

- Edit the implementation in this repository, not in `.codex`.
- Use `-Mode Link` during development to avoid duplicate copies.
- Keep the skill folder thin and procedural.
- Keep all runtime-generated artifacts out of git.
- Prefer `lkb_*.cmd` or `lkb_*.ps1` in normal use so the gateway selects its configured runtime automatically.
- Plain `python gateway\lkb_*.py` is intended for development only and assumes the required dependencies are already available in that interpreter.

## Related Workspace Docs

If you are working from the broader analysis workspace, the design notes live under:

- `../rebuild/`

That folder documents the target architecture, recovery path, and current validation state.
