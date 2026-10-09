---
description: "AUDIT — show what to audit on the PR head (the `skills.audit` skill, default `pr-audit`, or the built-in checklist when it is missing), then record the result: `--report <file>` comments it on the PR; `--approve` adds the `<!-- auditoria-aprovada sha=<head> -->` marker and saves `auditedSha` + `auditedPatchId`; `--finding SEV=N` (repeatable) records open findings for the `pilot` auto-finish. Also `--skill-ran`, `--skill-missing`. Agent at level >= `pr`. Before: `ship`; after: `queue add`."
---

# Audit

Audit the PR head adversarially: read everything before executing anything from the PR.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
audit [D-NNN]                                     # what to audit (skill or checklist)
audit [D-NNN] --report report.md --approve --finding BLOQUEANTE=0 --finding CORRIGIR=0 --skill-ran pr-audit
```

- The marker must point at the head GitHub sees: push (or `ship`) first.
- Without `--finding`, the `pilot` level never closes the demand on its own.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it actually helps navigation.** The print does *not* rename the chat; renaming is a user-facing convenience, never required. When this chat tracks a single demand and a rename would help the developer, call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the demand title (also places a divider + ToC entry) and/or try `/rename <title>` if this build exposes it. Skip the rename when the chat already holds multiple demandas — renaming to one demand's title would mislead.
