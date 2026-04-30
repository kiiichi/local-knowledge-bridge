# Domain Docs

This is a single-context repo. Engineering skills should use the root domain docs and ADRs when they exist.

## Before Exploring

Read these files when they are relevant to the task:

- `CONTEXT.md` at the repo root
- `docs/adr/` for architectural decisions that touch the area being changed

If these files do not exist, proceed silently. Do not require them before doing ordinary engineering work.

## Expected Layout

```text
/
|-- CONTEXT.md
|-- docs/
|   `-- adr/
|       |-- 0001-example-decision.md
|       `-- 0002-example-decision.md
|-- gateway/
|-- scripts/
`-- skill/
```

## Vocabulary

When output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, prefer the term used in `CONTEXT.md`.

If a needed concept is missing from the glossary, either the work is inventing language the project does not use or the docs have a real gap. Note that gap for a future documentation pass.

## ADR Conflicts

If a proposed change contradicts an existing ADR, call out the conflict explicitly instead of silently overriding the decision.
