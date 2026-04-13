---
name: local-knowledge-bridge
description: Search the user's local Obsidian and EndNote knowledge sources before answering research questions. Use when Codex should ground answers in the user's local notes, papers, PDFs, and reference libraries rather than model memory first, especially for literature review, method comparison, paper summary, note lookup, evidence gathering, or local knowledge-base retrieval tasks.
---

# Local Knowledge Bridge

Use this skill to answer research questions from the user's local knowledge base first.

## Hard Rules

- Treat the configured Obsidian vault as read-only.
- Treat the configured EndNote library and `.Data` folder as read-only.
- Never create helper files in the source vault, source library, or source PDF folders.
- Keep all derived artifacts inside `C:\Users\<user>\.codex\Function\local_knowledge_bridge`.

## Gateway

The local gateway is expected at:

`C:\Users\<user>\.codex\Function\local_knowledge_bridge`

It exposes these commands:

- `lkb_ask.cmd`
- `lkb_search.cmd`
- `lkb_report.cmd`
- `lkb_index.cmd`
- `lkb_refresh.cmd`
- `lkb_service.cmd`
- `lkb_configure.cmd`
- `lkb_doctor.cmd`
- `lkb_eval.cmd`
- `lkb_bootstrap_runtime.cmd`

`kb_*` names belong to the legacy packaged reference and should not be used as the active engineering surface for this skill.

## Workflow

1. For research or literature questions, call `lkb_ask.cmd` before relying on memory.
2. Prefer `--profile fast` for normal retrieval.
3. `--profile deep` is reserved for a later milestone and should not be the default path in the current implementation.
4. If the user wants raw matches or diagnostics, use `lkb_search.cmd` or `lkb_report.cmd`.
5. If the user asks to refresh first, use `lkb_index.cmd --force` or the command-level refresh flags.
6. Separate direct local evidence from your inference in the final answer.
7. If no direct local evidence is found, say that explicitly.

## Preferred Commands

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

Config and status:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_configure.cmd --show
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_index.cmd --status
```

Runtime bootstrap:

```powershell
C:\Users\<user>\.codex\Function\local_knowledge_bridge\lkb_bootstrap_runtime.cmd
```

## Notes

- `fast` should remain lightweight and avoid loading deep models.
- `balanced` is also lexical in V1; it widens recall but does not load semantic models.
- `deep` is intentionally not implemented in V1 and should fail explicitly rather than silently degrading.
- This skill is only as useful as the user's local notes and library contents.
