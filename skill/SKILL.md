---
name: local-knowledge-bridge
description: Search the user's local Obsidian and EndNote knowledge sources before answering research questions. Trigger this skill when the user explicitly mentions lkb, asks to use lkb to search or answer, or wants Codex to ground answers in local notes, papers, PDFs, and reference libraries rather than model memory first.
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
`lkb_*` remains the command prefix, and `lkb` is also a valid user-facing shorthand for this skill.

## Workflow

1. For research or literature questions, call `lkb_ask.cmd` before relying on memory.
2. Prefer `--profile fast` for normal retrieval.
3. `--profile deep` is reserved for a later milestone and should not be the default path in the current implementation.
4. If the user wants raw matches or diagnostics, use `lkb_search.cmd` or `lkb_report.cmd`.
5. If the user asks to refresh first, use `lkb_index.cmd --force` or the command-level refresh flags.
6. Separate direct local evidence from your inference in the final answer.
7. If no direct local evidence is found, say that explicitly.

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

## Alias Examples

These user requests should activate this skill:

- `使用 lkb 检索 "passive linear optics"`
- `用 lkb 查一下 balanced detector`
- `基于 lkb 回答这个问题`
- `search with lkb`
- `answer with lkb`

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
- `balanced` now uses lightweight hybrid route scoring, but it still does not load deep models.
- `deep` is intentionally not implemented in V1 and should fail explicitly rather than silently degrading.
- This skill is only as useful as the user's local notes and library contents.
