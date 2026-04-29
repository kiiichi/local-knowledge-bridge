---
name: local-knowledge-bridge
description: Search the user's local Obsidian, EndNote, Zotero, and folder knowledge sources before answering research questions. Use when the user mentions lkb, asks to search local notes/libraries/papers/folders, or wants answers grounded in local evidence rather than model memory first.
---

# Local Knowledge Bridge

Use this skill to answer research questions from the user's local knowledge base first.

## Hard Rules

- Treat Obsidian, EndNote, Zotero, and folder knowledge sources as read-only.
- Never write helper files into a source vault, reference library, attachment directory, Zotero storage, or folder source.
- Keep derived artifacts inside the deployed gateway: `C:\Users\<user>\.codex\Function\local_knowledge_bridge`.
- Use `lkb_*` commands only. Do not call legacy `kb_*` commands.
- If no direct local evidence is found, say that explicitly instead of silently falling back.

## Setup And Maintenance

Repo-level install, redeploy, or configuration starts from the source repo root:

```powershell
.\lkb_setup.cmd
```

That setup entry can install/redeploy or open the deployed maintenance wizard:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_wizard.cmd
```

Use the wizard for source paths, route-weight presets, deep setup, status checks, and index rebuilds.

## Gateway Commands

Expected deployed gateway:

```text
C:\Users\<user>\.codex\Function\local_knowledge_bridge
```

Main commands:

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

Targets:

- `both` means all configured source families
- `obsidian`
- `endnote`
- `zotero`
- `folder`

Profiles:

- `fast` for default lightweight answers
- `balanced` for broader local retrieval
- `deep` only when explicitly useful; deep searches must be sequential

## Research Workflow

1. For research or literature questions, call `lkb_ask.cmd` before relying on memory.
2. Prefer `--profile fast` unless the user asks for raw matches, broader recall, or deep retrieval.
3. Use `lkb_search.cmd` for raw matches and `lkb_report.cmd` for structured evidence review.
4. Refresh once before a query sequence only when the user asks to refresh or sources are likely stale.
5. Separate direct local evidence from inference in the answer.

Primary answer:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_ask.cmd "<question>" --profile fast
```

Raw search:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_search.cmd both "<query>" --profile balanced --limit 10
```

Combined report:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_report.cmd "<query>" --target both --profile balanced --limit 8 --read-top 3
```

Status:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --show
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --status
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_doctor.cmd --json
```

Deep setup:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd --include-deep --prefetch-models
```

## Output Policy

- Every answer grounded in LKB results must end with a data source list.
- For literature-backed evidence, include the complete indexed title and DOI when available.
- For non-literature documents, include the original source file name without translating it and the document path.
- Include locators where available so the cited passage can be found again.
- For EndNote-backed evidence, prefer: `EndNote: <title>, DOI: <doi or ->, locator: <locator>, path: <path>`.
- For Zotero-backed evidence, prefer: `Zotero: <title>, DOI: <doi or ->, locator: <locator>, path: <path>`.
- For Obsidian or folder evidence, cite the source file name, document path, and locator.
- If the same source appears repeatedly, define a short alias on first mention and reuse it.
- Keep local evidence separate from model inference.

## Trigger Examples

- `use lkb to search passive linear optics`
- `answer with lkb`
- `search my local notes with lkb`
- `用 lkb 检索 passive linear optics`
- `基于 lkb 回答这个问题`

## Behavior Notes

- `fast` and `balanced` must not load deep models.
- `deep` requires prefetched local models under `gateway/.models/`.
- Deep retrieval should fail explicitly when models or dependencies are missing.
- Do not run multiple `--profile deep` searches concurrently.
