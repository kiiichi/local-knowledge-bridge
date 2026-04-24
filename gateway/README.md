# Local Knowledge Bridge Gateway

This directory contains the source-controlled gateway that is deployed to:

- `C:\Users\<user>\.codex\Function\local_knowledge_bridge`

If you are installing or using Local Knowledge Bridge for the first time, start with the repository root [README](../README.md).

## What Lives Here

- Windows wrappers such as `lkb_search.cmd` and `lkb_ask.cmd`
- Python entrypoints such as `lkb_search.py` and `lkb_doctor.py`
- shared source modules under `src/local_knowledge_bridge/`
- runtime and dependency manifests
- the default config template
- the evaluation case bundle used for local regression checks

## Main User-Facing Commands

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

## Generated Local State

These paths are created after deployment and are intentionally not committed to git:

- `runtime/`
- `.cache/`
- `.index/`
- `.logs/`
- `.models/`
- `lkb_config.json`

Use `lkb_bootstrap_runtime` to create the embedded runtime. Use `lkb_bootstrap_runtime --include-deep --prefetch-models` only on machines that need deep retrieval.
