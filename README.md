# Local Knowledge Bridge

`Local Knowledge Bridge` is an open-source, Windows-first repository for building and deploying a local Codex knowledge skill backed by the user's own files.

The initial target is:

- `Obsidian`
- `EndNote`

This repository is intended to be:

- the canonical source repo for development
- the deployment source for Windows users
- the shared layout used across devices

The core retrieval engine is still under active implementation. This repository already contains:

- the skill metadata and prompt surface
- the gateway directory layout
- Windows install and deployment scripts
- config templates
- wrapper scripts and command skeletons
- runtime bootstrap support

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

## Configure Data Sources

After bootstrap, point the gateway at your own local data:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --obsidian "D:\Notes\Vault"
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --endnote "D:\EndNote\My Library.enl" --endnote-name "Main Library"
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --show
```

## Current Status

The repository currently provides a deployment-ready scaffold.

Implemented now:

- installation and deployment scripts
- gateway runtime bootstrap
- local config creation and editing
- command wrappers and command skeletons

Planned next:

- SQLite index schema
- Obsidian indexing
- EndNote metadata and PDF indexing
- local retrieval
- local HTTP service
- `fast` / `balanced` / `deep` execution paths

The command surface already exists so future implementation can stay compatible with the LKB naming:

- `lkb_ask`
- `lkb_search`
- `lkb_report`
- `lkb_index`
- `lkb_refresh`
- `lkb_service`
- `lkb_configure`
- `lkb_doctor`
- `lkb_eval`
- `lkb_bootstrap_runtime`

## Cross-Device Workflow

Use this repository as the source of truth on every machine.

Recommended flow:

1. Clone or download this repository on the new machine.
2. Run `scripts/install_windows.ps1`.
3. Run `lkb_bootstrap_runtime.cmd`.
4. Configure the local source paths for that machine.
5. Build indexes on that machine after the retrieval engine is implemented.

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

## Related Workspace Docs

If you are working from the broader analysis workspace, the design notes live under:

- `../rebuild/`

That folder documents the target architecture and the clean-room reconstruction path.
