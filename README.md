# Local Knowledge Bridge

`Local Knowledge Bridge` is the canonical open-source repository for the new `lkb` system.  
This repo is the source of truth for implementation, Windows deployment, and cross-device development.

Current scope:

- `Obsidian`
- `EndNote`

## Quick Start For New Users

This section is the shortest safe path for a first Windows deployment.  
Run commands from PowerShell.

### 1. Prerequisites

Install or confirm:

- Python 3.11+ available as `py` or `python`
- Codex desktop or another Codex setup using `%USERPROFILE%\.codex`
- readable local source paths for Obsidian and/or EndNote

Check Python:

```powershell
py -3 --version
```

If `py` is not available:

```powershell
python --version
```

### 2. Install LKB Into Codex

Clone or download this repository, then run:

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Copy -BootstrapRuntime
```

Use development link mode instead if you are editing this repo:

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Link -BootstrapRuntime
```

If PowerShell blocks script execution, run the same command through:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows.ps1 -Mode Copy -BootstrapRuntime
```

### 3. Configure Your Sources

Configure Obsidian:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
& "$LKB\lkb_configure.cmd" --obsidian "D:\Notes\Vault"
```

Configure EndNote:

```powershell
$LKB = "$env:USERPROFILE\.codex\Function\local_knowledge_bridge"
& "$LKB\lkb_configure.cmd" --endnote "D:\EndNote\My Library.enl" --endnote-name "Main Library"
```

You can configure only one source if you do not use both.  
Check the resulting config:

```powershell
& "$LKB\lkb_configure.cmd" --show
```

### 4. Build The Local Index

Each machine builds its own index from its own source paths:

```powershell
& "$LKB\lkb_index.cmd" --force
& "$LKB\lkb_index.cmd" --status
```

### 5. Verify Basic Retrieval

Run diagnostics:

```powershell
& "$LKB\lkb_doctor.cmd" --json
```

Search:

```powershell
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile balanced --limit 5
```

Ask:

```powershell
& "$LKB\lkb_ask.cmd" "What is the passive linear optics paper about?" --limit 3
```

Report:

```powershell
& "$LKB\lkb_report.cmd" "passive linear optics" --target both --profile balanced --limit 5 --read-top 3
```

### 6. Optional: Enable Deep Retrieval

`deep` uses local model files and can be large. It is not downloaded lazily during search.  
Run this only on machines where you want semantic/reranker retrieval:

```powershell
& "$LKB\lkb_bootstrap_runtime.cmd" --include-deep --prefetch-models
```

Models are cached under:

```text
<deployed-gateway>\.models\
```

Check readiness:

```powershell
& "$LKB\lkb_doctor.cmd" --json
```

In the JSON output, `deep_status.ready` should be `true`.  
Then test deep retrieval:

```powershell
& "$LKB\lkb_search.cmd" both "passive linear optics" --profile deep --limit 5 --no-service
```

If model prefetch fails with a Hugging Face network timeout, retry when network access is available. The repo intentionally does not commit `.models/`.

### 7. What Not To Copy Between Machines

Do not copy these generated directories by default:

- `gateway/runtime/`
- `gateway/.index/`
- `gateway/.cache/`
- `gateway/.logs/`
- `gateway/.models/`
- `gateway/lkb_config.json`

On each new machine, install, configure local paths, prefetch deep models if needed, and rebuild the index locally.

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

## Naming Boundary

- `kb_*` is the legacy reference namespace under `../function/kb_gateway/` and `../skills/kb-answer/`.
- `lkb_*` is the active engineering namespace in this repository.
- New code and new docs in this repository should always use `lkb_*`.

## Current Implementation Status

Implemented now:

- Windows install and deployment scripts
- runtime bootstrap
- local config creation and editing
- `lkb_index`
- `lkb_search`
- `lkb_ask`
- `lkb_report`
- `lkb_service`
- `lkb_doctor`
- `lkb_eval`
- Obsidian indexing
- EndNote metadata / attachment / PDF full-text indexing
- lexical retrieval with weighted route fusion
- lightweight hybrid route scoring for `fast` and `balanced`
- `deep` semantic retrieval with explicit machine-local model prefetch under `gateway/.models/`
- real `mode` execution semantics across CLI, service, and retrieval payloads
- config-backed route weights and lightweight scoring defaults
- `deep_worker.py` service dispatch for `profile=deep`
- `lkb_doctor` `deep_status` diagnostics
- service stdout / stderr logging to `gateway/.logs/service.log`
- self-contained embedded runtime bootstrap
- service-first execution on `127.0.0.1:53744`

Not implemented yet:

- remote release lookup beyond local version files

Current retrieval shape:

- `SQLite FTS5` route-level lexical retrieval
- `mode` is now a real request / response contract
- route-local token-hit, expanded-token, char-ngram, and FTS-bonus scoring
- search hits expose fused `score` plus `lexical_score`, `hybrid_score`, `semantic_score`, and `rerank_score`
- weighted reciprocal rank fusion
- `fast` and `balanced` now use lightweight hybrid route ordering without loading deep models
- `deep` adds `BAAI/bge-m3` semantic scoring, semantic route fusion, and `BAAI/bge-reranker-v2-m3` reranking
- `deep` requires explicit local model prefetch into `gateway/.models/` and does not download models lazily during a query

## Current Deep Deployment Route

Steps 1-7 of the locked retrieval route are complete. The current operating rules for `deep` are:

1. Keep `deep` machine-local and reproducible.  
   The active deployment path is:
   - install or update the gateway
   - run `lkb_bootstrap_runtime --include-deep --prefetch-models`
   - cache models only under `gateway/.models/`
   - keep `.models/` out of git and do not copy it across machines by default

2. Keep the repository modular and cross-device deployable.  
   Retrieval orchestration stays in `retrieval.py`, lightweight ranking stays in `scoring.py` / `ranking.py`, deep model loading stays in `deep_models.py`, deep ranking stays in `deep_ranking.py`, and service isolation stays in `deep_worker.py`.

`lkb_*` remains the CLI prefix, and users can also refer to this skill as `lkb` in natural-language requests such as “use lkb to search” or “answer with lkb”.

## What Gets Deployed

When installed, this repository deploys to:

- skill:
  - `C:\Users\<you>\.codex\skills\local-knowledge-bridge`
- gateway:
  - `C:\Users\<you>\.codex\Function\local_knowledge_bridge`

The deployed gateway creates machine-local state:

- `gateway/runtime/`
- `gateway/.cache/`
- `gateway/.index/`
- `gateway/.logs/`
- `gateway/.models/`
- `gateway/lkb_config.json`

These paths are intentionally not committed to git.

## Git Policy

Tracked in git:

- `skill/**`
- `scripts/install_windows.*`
- `gateway/lkb_*.cmd`
- `gateway/lkb_*.ps1`
- `gateway/lkb_*.py`
- `gateway/deep_worker.py`
- `gateway/templates/lkb_config.template.json`
- `gateway/requirements.runtime.txt`
- `gateway/requirements.deep.txt`
- `gateway/pyproject.toml`
- `gateway/VERSION`
- `gateway/VERSION_PREFIX`
- `gateway/eval/cases.jsonl`
- `gateway/src/local_knowledge_bridge/**/*.py`
- repository documentation

Not tracked in git:

- `gateway/runtime/`
- `gateway/.cache/`
- `gateway/.index/`
- `gateway/.logs/`
- `gateway/.models/`
- `gateway/lkb_config.json`
- `__pycache__/`
- local test deployment directories

## Install On Windows

### Prerequisites

- Windows PowerShell
- Codex desktop or another Codex environment that uses `~/.codex`
- standalone Python available as `py` or `python`

Runtime bootstrap notes:

- `Local Knowledge Bridge` does not require any `kb` files or any legacy `kb` runtime on a new machine.
- `scripts/install_windows.ps1` and `lkb_bootstrap_runtime` prefer Python `3.11` when multiple versions are installed.
- bootstrap creates a machine-local embedded runtime under `gateway/runtime/py311`.
- if only Python `3.12` or `3.13` is installed, bootstrap can still build the local runtime, but `3.11` remains the preferred version for the eventual deep stack.

### Option 1: Copy Install

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Copy
```

### Option 2: Development Install

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Link
```

`-Mode Link` is the recommended option for active development because edits in the repo are reflected immediately in the deployed Codex directories.

Install and immediately prepare the deep runtime plus machine-local models:

```powershell
cd <repo>\local-knowledge-bridge
.\scripts\install_windows.ps1 -Mode Link -BootstrapRuntime -PrefetchModels
```

## Bootstrap And Configure

Create the local runtime:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd
```

This bootstrap step is self-contained:

- it starts from the currently selected system Python on that machine
- it builds the embedded `gateway/runtime/py311` runtime for `lkb`
- it does not read from `../function/kb_gateway/`

Include deep dependencies in the runtime:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd --include-deep
```

Recreate the runtime and prefetch the deep models into `gateway/.models/`:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd --force-recreate --prefetch-models
```

Configure data sources:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --obsidian "D:\Notes\Vault"
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --endnote "D:\EndNote\My Library.enl" --endnote-name "Main Library"
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --show
```

Build the local index:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --force
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --status
```

## Query And Service

Ask:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_ask.cmd "What is the passive linear optics paper about?"
```

Search:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "passive linear optics" --profile balanced --limit 10
```

Deep search after prefetch:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "passive linear optics" --profile deep --limit 10 --no-service
```

Report:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_report.cmd "passive linear optics" --target both --profile balanced --limit 8 --read-top 3
```

Current service contract:

- host: `127.0.0.1`
- port: `53744`
- `GET /health`
- `POST /search`
- `POST /ask`
- `POST /report`
- `POST /shutdown`

Current service behavior and diagnostics:

- `lkb_search`, `lkb_ask`, and `lkb_report` default to the service path and auto-start the service if needed
- `--no-service` bypasses the HTTP transport and runs retrieval in-process
- service stdout / stderr now append to `gateway/.logs/service.log`
- `idle_shutdown_seconds` exists in config but is not consumed yet, so the service is not auto-shutdown per request
- if the service path throws `ConnectionResetError`, inspect `gateway/.logs/service.log` before changing retrieval code

## Cross-Device Development And Deployment

Use this repository as the only source of code on every machine.

Each machine should:

1. clone the repository
2. install with `Copy` or `Link`
3. run `lkb_bootstrap_runtime`
4. run `lkb_bootstrap_runtime --include-deep --prefetch-models` if `deep` is needed
5. configure local Obsidian / EndNote paths
6. build the index locally
7. validate `lkb_doctor --json` and confirm `deep_status.ready = true` before relying on `profile=deep`

Do not copy these between machines:

- `.index`
- `.cache`
- `.logs`
- `lkb_config.json`
- `.models` by default

## Current Verified Workspace Snapshot

The current workspace has already verified:

- Obsidian vault: `C:\Users\kichi\Documents\kichi@git\kc-notes`
- EndNote library: `C:\Users\kichi\Documents\My EndNote Library.enl`
- service port: `127.0.0.1:53744`
- index counts:
  - `obsidian_notes = 114`
  - `obsidian_chunks = 2015`
  - `endnote_docs = 583`
  - `endnote_attachments = 655`
  - `endnote_fulltext = 29511`
- `lkb_doctor --json` snapshot:
  - `obsidian_stale = true`
  - `endnote_stale = true`
  - `obsidian_changed_notes = 4`
  - `endnote_changed_pdfs = 0`
  - `service.running = false`
- `lkb_eval` snapshot:
  - eval set size: `6` cases
  - case mix: `4` tomography cases + `1` EndNote paraphrase case + `1` Obsidian-biased case
  - `balanced`: `Recall@5 = 1.0`, `Recall@10 = 1.0`, `MRR@10 = 0.9167`, `nDCG@10 = 0.9385`, `AvgLatencyMs ~= 237.2`
  - `baseline`: `Recall@5 = 1.0`, `Recall@10 = 1.0`, `MRR@10 = 0.9167`, `nDCG@10 = 0.9385`, `AvgLatencyMs ~= 222.9`

The current bundled `gateway/eval/cases.jsonl` is still a smoke regression set, but it is no longer tomography-only. It now includes paraphrase EndNote and Obsidian-biased cases and should keep expanding as the corpus evolves.

## Related Docs

If you are working from the broader workspace, read in this order:

1. `../agents.md`
2. `README.md`
3. `../rebuild/README.md`
4. `../rebuild/docs/03-architecture-and-modules.md`
5. `../rebuild/docs/05-implementation-roadmap.md`
