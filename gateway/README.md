# Local Knowledge Bridge Gateway

This directory is the source-controlled gateway deployed to:

```text
C:\Users\<user>\.codex\Function\local_knowledge_bridge
```

For install, redeploy, or user configuration, start from the repo root:

```powershell
.\lkb_setup.cmd
```

The repo setup entry opens the deployed maintenance wizard `lkb_wizard` for source configuration, route-weight presets, deep setup, index status, and rebuilds.

## Current Source Scope

The gateway currently indexes and searches:

- `Obsidian`
- `EndNote`
- `Zotero`
- local `folder` libraries

Supported document extraction includes Markdown, text, PDF, DOCX, PPTX, and XLSX where applicable.

## User-Facing Commands

- `lkb_wizard`
- `lkb_bootstrap_runtime`
- `lkb_configure`
- `lkb_index`
- `lkb_refresh`
- `lkb_search`
- `lkb_ask`
- `lkb_report`
- `lkb_service`
- `lkb_doctor`
- `lkb_eval`

The `.cmd` and `.ps1` wrappers live beside the Python entrypoints and are copied or linked as part of deployment.

## Important Modules

- `src/local_knowledge_bridge/config.py` - config normalization, source library lists, route/scoring settings
- `src/local_knowledge_bridge/schema.py` - SQLite schema and FTS tables
- `src/local_knowledge_bridge/retrieval.py` - indexing and search orchestration
- `src/local_knowledge_bridge/obsidian.py` - Obsidian indexing
- `src/local_knowledge_bridge/endnote.py` - EndNote metadata, attachments, and full text
- `src/local_knowledge_bridge/zotero.py` - Zotero metadata, notes, annotations, cache text, and attachments
- `src/local_knowledge_bridge/folder.py` - recursive folder source indexing
- `src/local_knowledge_bridge/document_text.py` - non-PDF text extraction helpers
- `src/local_knowledge_bridge/deep_models.py` and `deep_ranking.py` - local deep retrieval stack
- `src/local_knowledge_bridge/wizard.py` and `terminal_ui.py` - deployed maintenance wizard and terminal UI helpers

## Generated Local State

These paths are created after deployment and are intentionally not committed:

- `runtime/`
- `.cache/`
- `.index/`
- `.logs/`
- `.models/`
- `lkb_config.json`

Use `lkb_bootstrap_runtime` to create or repair the embedded runtime. Use `lkb_bootstrap_runtime --include-deep --prefetch-models` on machines that need `profile=deep`.

## Developer Validation

From the repo root:

```powershell
python -m unittest discover -s gateway\tests
```

Compile-check the wizard stack:

```powershell
python -m py_compile gateway\lkb_wizard.py gateway\src\local_knowledge_bridge\wizard.py gateway\src\local_knowledge_bridge\terminal_ui.py
```
