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
3. **Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
6. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, say so plainly - switching is the developer's call. A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
7. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).
