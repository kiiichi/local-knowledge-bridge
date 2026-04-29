---
name: local-knowledge-bridge
description: Search the user's local Obsidian, EndNote, Zotero, and folder knowledge sources before answering research questions. Trigger this skill when the user explicitly mentions lkb, asks to use lkb to search or answer, or wants Codex to ground answers in local notes, papers, PDFs, local folders, and reference libraries rather than model memory first.
---

# Local Knowledge Bridge

Use this skill to answer research questions from the user's local knowledge base first.

## Hard Rules

- Treat the configured Obsidian vault as read-only.
- Treat the configured EndNote library and `.Data` folder as read-only.
- Treat the configured Zotero library and folder knowledge sources as read-only.
- Never create helper files in the source vault, source library, source PDF folders, Zotero storage, or folder knowledge sources.
- Keep all derived artifacts inside `C:\Users\<user>\.codex\Function\local_knowledge_bridge`.

## Gateway

The local gateway is expected at:

`C:\Users\<user>\.codex\Function\local_knowledge_bridge`

Available commands:

- `lkb_ask.cmd`
- `lkb_search.cmd`
- `lkb_report.cmd`
- `lkb_index.cmd`
- `lkb_refresh.cmd`
- `lkb_service.cmd`
- `lkb_wizard.cmd`
- `lkb_configure.cmd`
- `lkb_doctor.cmd`
- `lkb_eval.cmd`
- `lkb_bootstrap_runtime.cmd`

Use the `lkb_*` commands for this skill. Do not call legacy `kb_*` commands from this skill flow.

## Workflow

1. For repository install, redeploy, or configuration, start with `lkb_setup.cmd` from the source repo root.
2. If setup action is configuration, it opens the deployed `lkb_wizard.cmd` for source path changes, route-weight presets, deep setup, or index rebuilds.
3. For research or literature questions, call `lkb_ask.cmd` before relying on memory.
4. Prefer `--profile fast` for the default answer flow.
5. Use `--profile deep` only when the user explicitly asks for deep retrieval or when higher recall and reranking are worth the extra local runtime cost.
6. If the user wants raw matches or diagnostics, use `lkb_search.cmd` or `lkb_report.cmd`.
7. If the user asks to refresh first, use `lkb_refresh.cmd` or refresh once before the query sequence.
8. Separate direct local evidence from your inference in the final answer.
9. If no direct local evidence is found, say that explicitly instead of silently falling back.

## Multi-Search Policy

When the user asks for multiple independent knowledge-base searches, run them sequentially unless the user explicitly asks for parallel execution.

For each search:

1. Run one `lkb_search.cmd`, `lkb_report.cmd`, or `lkb_ask.cmd` command.
2. Read and summarize the result before starting the next search.
3. Keep evidence separated by query.
4. Do not use repeated refresh flags across multiple searches; refresh once before the sequence if needed.
5. Do not run multiple `--profile deep` searches concurrently. Deep searches must be sequential.

## Output Format

- For EndNote-backed evidence, cite the EndNote entry title and locator, not the local PDF path.
- Default citation form:
  - `EndNote: <title>, locator: <locator>`
- Do not emit Markdown local-file links or Windows file paths unless the user explicitly asks for them.
- If the same source will be mentioned multiple times in one answer, define a short alias on first mention:
  - `<alias> = EndNote: <title>`
- After defining the alias, cite later mentions as:
  - `<alias>, <locator>`
- Keep direct local evidence separate from inference.
- If no direct local evidence is found, say that explicitly.

Examples:

- `laser locking tutorial = EndNote: Tutorial on laser locking techniques and the manufacturing of vapor cells for spectroscopy`
- `Advanced interferometry = EndNote: Advanced interferometry for gravitational wave detection`
- Later references:
  - `laser locking tutorial, p.14-15`
  - `Advanced interferometry, p.125-127`

## Trigger Examples

These user requests should activate this skill:

- `use lkb to search passive linear optics`
- `answer with lkb`
- `search my local notes with lkb`
- `使用 lkb 检索 passive linear optics`
- `用 lkb 查一下 balanced detector`
- `基于 lkb 回答这个问题`

## Preferred Commands

Primary answer:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_ask.cmd "<question>" --profile fast
```

Raw search:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "<query>" --profile balanced --limit 10
```

Use target `obsidian`, `endnote`, `zotero`, or `folder` when the user explicitly asks to restrict the search. `both` means all configured source families.

Combined report:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_report.cmd "<query>" --target both --profile balanced --limit 8 --read-top 3
```

Refresh and status:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_refresh.cmd
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --show
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --status
```

Repository install or redeploy:

```powershell
cd <repo>\local-knowledge-bridge
.\lkb_setup.cmd
```

Runtime bootstrap:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd
```

Deep setup when explicitly needed:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd --include-deep --prefetch-models
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_doctor.cmd --json
```

## Behavior Notes

- `fast` and `balanced` must not load deep models.
- `deep` requires prefetched local models under `gateway/.models/`.
- Deep retrieval should fail explicitly when models or dependencies are missing.
