# Local Knowledge Bridge

`Local Knowledge Bridge` is the canonical open-source repository for the new `lkb` system.  
This repo is the source of truth for implementation, Windows deployment, and cross-device development.

Current scope:

- `Obsidian`
- `EndNote`

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
- service-first execution on `127.0.0.1:53744`

Not implemented yet:

- `deep`
- remote release lookup beyond local version files

Current retrieval shape:

- `SQLite FTS5` route-level lexical retrieval
- weighted reciprocal rank fusion
- `fast` and `balanced` are usable
- `deep` fails explicitly

## Locked Next Development Route

The next work on this repository is already defined:

1. Restore real `mode` execution semantics.  
   The CLI still exposes `--mode`, but `mode` has not yet entered the request models, service payloads, and retrieval execution path.

2. Restore the legacy `kb` lightweight hybrid scoring path.  
   The current `lkb` retrieval stack is still lexical + RRF only. The next stage should recover the old token-hit, expanded-token, char-ngram, and FTS bonus logic in a new `src/local_knowledge_bridge/scoring.py`.

3. Move route weights and scoring parameters into configuration.  
   The next stage should make the retrieval weights and scoring constants observable and configurable through `constants.py` and `templates/lkb_config.template.json`.

4. Implement `deep` with the same technical path as legacy `kb`.  
   The target path is:
   - hybrid recall
   - semantic scoring with `BAAI/bge-m3`
   - semantic route fusion
   - reranker with `BAAI/bge-reranker-v2-m3`
   - isolated `deep_worker.py`

5. Keep the repository modular and cross-device deployable.  
   The new retrieval and deep code should be added as modules under `src/local_knowledge_bridge/`, not as a new monolith.

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
- Python 3.11+ available as `py` or `python`

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

## Bootstrap And Configure

Create the local runtime:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd
```

Include deep dependencies in the runtime:

```powershell
C:\Users\<you>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd --include-deep
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

## Cross-Device Development And Deployment

Use this repository as the only source of code on every machine.

Each machine should:

1. clone the repository
2. install with `Copy` or `Link`
3. run `lkb_bootstrap_runtime`
4. install deep dependencies locally if needed
5. configure local Obsidian / EndNote paths
6. build the index locally
7. download deep models locally when deep is implemented

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
  - `obsidian_changed_notes = 3`
  - `endnote_changed_pdfs = 0`
  - `service.running = false`
- `lkb_eval` snapshot:
  - `balanced`: `Recall@5 = 1.0`, `Recall@10 = 1.0`, `MRR@10 = 1.0`, `nDCG@10 = 1.0`, `AvgLatencyMs ~= 139.0`
  - `baseline`: `Recall@5 = 1.0`, `Recall@10 = 1.0`, `MRR@10 = 1.0`, `nDCG@10 = 1.0`, `AvgLatencyMs ~= 137.0`

The current bundled `gateway/eval/cases.jsonl` is a tomography-focused smoke regression set. It should be extended further with paraphrase EndNote cases and Obsidian-biased cases as the repo evolves.

## Related Docs

If you are working from the broader workspace, read in this order:

1. `../agents.md`
2. `README.md`
3. `../rebuild/README.md`
4. `../rebuild/docs/03-architecture-and-modules.md`
5. `../rebuild/docs/05-implementation-roadmap.md`
