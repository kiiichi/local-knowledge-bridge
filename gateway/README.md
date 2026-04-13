# Local Knowledge Bridge Gateway

This directory is the source-controlled gateway implementation for `Local Knowledge Bridge`.

It is designed to be deployed into:

- `C:\Users\<user>\.codex\Function\local_knowledge_bridge`

The V1 gateway currently provides:

- `lkb_index` for local index construction
- `lkb_search` for merged lexical search
- `lkb_ask` for evidence-first answers
- `lkb_report` for structured evidence summaries
- `lkb_service` for the local HTTP service on `127.0.0.1:53744`
- `lkb_configure` and `lkb_bootstrap_runtime` for setup

The current retrieval stack is:

- `SQLite FTS5`
- Obsidian note and chunk indexing
- EndNote metadata, attachments, and PDF full-text indexing
- weighted reciprocal rank fusion across routes

Generated directories such as `runtime/`, `.cache/`, `.index/`, `.logs/`, and `.models/` are intentionally excluded from git and should be created after deployment.
