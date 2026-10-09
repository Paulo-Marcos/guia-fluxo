---
name: guia-audit
description: "AUDIT — show what to audit on the PR head (the `skills.audit` skill, default `pr-audit`, or the built-in checklist when it is missing), then record the result: `--report <file>` comments it on the PR; `--approve` adds the `<!-- auditoria-aprovada sha=<head> -->` marker and saves `auditedSha` + `auditedPatchId`; `--finding SEV=N` (repeatable) records open findings for the `pilot` auto-finish. Also `--skill-ran`, `--skill-missing`. Agent at level >= `pr`. Before: `ship`; after: `queue add`."
---

# Audit

Audit the PR head adversarially: read everything before executing anything from the PR.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
audit [D-NNN]                                     # what to audit (skill or checklist)
audit [D-NNN] --report report.md --approve --finding BLOQUEANTE=0 --finding CORRIGIR=0 --skill-ran pr-audit
```

- The marker must point at the head GitHub sees: push (or `ship`) first.
- Without `--finding`, the `pilot` level never closes the demand on its own.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
