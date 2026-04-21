# Local Knowledge Bridge Gateway

This directory is the source-controlled gateway implementation for `Local Knowledge Bridge`.

It is designed to be deployed into:

- `C:\Users\<user>\.codex\Function\local_knowledge_bridge`

The V1 gateway currently provides:

- `lkb_index` for local index construction
- `lkb_search` for merged hybrid retrieval
- `lkb_ask` for evidence-first answers
- `lkb_report` for structured evidence summaries
- `lkb_service` for the local HTTP service on `127.0.0.1:53744`
- `lkb_doctor` for local diagnostics
- `lkb_eval` for retrieval regression evaluation
- `lkb_configure` and `lkb_bootstrap_runtime` for setup

The current retrieval stack is:

- `SQLite FTS5`
- Obsidian note and chunk indexing
- EndNote metadata, attachments, and PDF full-text indexing
- route-local lightweight hybrid scoring for `fast` and `balanced`
- real `mode` request / service / retrieval semantics
- weighted reciprocal rank fusion across routes

Current V1 notes:

- `lkb_doctor` mirrors the legacy `kb_doctor` sections for `VERSION`, `SOURCES`, `AUTHORIZATION`, and `INDEX`
- `lkb_eval` mirrors the legacy `kb_eval` shape for `profile`, `cases`, `metrics`, and `per_case`
- version lookup is currently local-only and reads the gateway `VERSION` files
- service stdout / stderr append to `.logs/service.log`
- `gateway/eval/cases.jsonl` is a smoke regression set grounded in the active local corpus and should be curated further as the corpus evolves
- the current bundled cases cover non-Gaussian-state tomography, homodyne tomography, third-order OPO state tomography, single-mode squeezed-light tomography, one EndNote paraphrase case, and one Obsidian-biased case

Generated directories such as `runtime/`, `.cache/`, `.index/`, `.logs/`, and `.models/` are intentionally excluded from git and should be created after deployment.

## Runtime Bootstrap

The gateway does not depend on any legacy `kb` files when deployed on a new machine.

- `lkb_bootstrap_runtime` uses the machine's available Python to build an embedded runtime inside `gateway/runtime/py311`
- when several Python versions are installed, the bootstrap path prefers Python `3.11`
- the resulting embedded runtime is the interpreter that wrapper scripts and service auto-start use afterward
