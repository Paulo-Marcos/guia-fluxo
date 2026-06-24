---
name: guia-finish
description: CLOSE an already-validated task — runs the docs-check hook AND a consultative quality gate (D-095), then commits by default. **`finish` is the USER's action: the agent only runs it when the developer requests `/guia:finish` or explicitly authorizes, and must NEVER trigger `finish` on its own — stop at `ready` and hand off. Behavioral rule, not a CLI parameter: no env, no flag (D-098 removed the `GUIA_HUMAN_FINISH` env gate the earlier D-080 had tried).** Use only after the developer confirms validation in real use. Required when `.guia/docs-map.yaml` exists: `--docs-touched <path>` (repeatable) or `--docs-skip "<reason>"`. **Quality gate (D-095):** when product files changed, run the available quality skills (project + global: clean-code-review, clean-architecture-guardian, tdd-dotnet, valida-pasta) over `modifiedFiles` (code quality, function/file size, SRP, coverage, need-to-refactor), refactor if needed, then confirm with `--quality-checked` (optional `--quality-skill <name>`, `--quality-finding "<action>"`) or skip with `--quality-skip "<reason>"`. Options: `--file`, `--summary`, `--validation` (same as ready), `--no-commit` (dry close), `--lock --lock-id <slug> --lock-description "..."` (protect files after close). For handoff to validation use `ready`; for inspection use `status`.
---

# Finish

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

> **`finish` is the USER's action (behavioral rule, D-098).** Closing is the developer's call. **If you are an AI agent, run `finish` ONLY when the developer requests `/guia:finish` or explicitly authorizes it — NEVER on your own initiative.** Your default job ends at `ready`: hand off and wait for the developer to ask for the close. This is a behavioral rule, not a CLI parameter — there is no env var or flag to set (D-098 removed the `GUIA_HUMAN_FINISH` env gate the earlier D-080 had tried; sending a variable was bad, and the engine cannot tell an agent apart from a human anyway).

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

## 1) Docs hook (mandatory when `.guia/docs-map.yaml` exists)

Run the docs check before closing:

```text
docs-check
```

For each listed candidate:
- Open the file and decide if this task changes anything relevant to it.
- Update what makes sense (README pointer, CLI reference entry, CHANGELOG entry, ADR, explanation paragraph).
- Note the paths you touched.

If the project has no `.guia/docs-map.yaml`, the hook is a no-op and `finish` runs as before.

## 2) Quality gate — run quality skills over what changed (D-095)

`finish` does **not** just run the test commands; it forces a **consultative quality validation** of the work. When product files changed (anything outside `.guia/`), the tool refuses to close until you confirm you ran it. **You (the agent) run the skills — the core only signals and enforces.**

Before closing:

1. Read `modifiedFiles` (the changed product files for this task).
2. Invoke the available **quality skills** — both **project** and **global** — over those files. Candidates in this environment:
   - `clean-code-review` (micro: readability, names, function size, smells)
   - `clean-architecture-guardian` (macro: layers, SOLID, SRP, coupling)
   - `tdd-dotnet` (tests/coverage of what changed)
   - `valida-pasta` (D-085, folder quality score 0–10, when available)
3. Evaluate every dimension: **(a)** code quality, **(b)** function/file size, **(c)** single responsibility (SRP), **(d)** coverage/tests, **(e)** whether it needs refactoring to reach good quality — and **if it does, refactor before closing**.

This is distinct from **D-088** (DDD/SOLID assessment at LOCK creation — same spirit, different moment) and reuses **D-085**'s `valida-pasta` rather than reimplementing scoring.

Then close, confirming the validation ran:

```text
finish <D-NNN> --docs-skip "..." --quality-checked --quality-skill clean-code-review --quality-finding "extraiu funcao X; cobriu caso Y"
# when there is genuinely nothing to assess (e.g. trivial constant/rename):
finish <D-NNN> --docs-skip "..." --quality-skip "alteracao trivial, sem impacto de qualidade"
```

The gate is a no-op when only `.guia/` bookkeeping changed, or when `finish.qualityGateByDefault` is `false` in `.guia/process.json`.

## 3) Close

Run this **only** because the developer asked for it (no env var or flag — see the rule above):

```text
finish <D-NNN> --docs-touched docs/reference/cli.md --quality-checked
# or, when nothing needed touching:
finish <D-NNN> --docs-skip "internal flow, no user-facing change" --quality-skip "no product code changed"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

## File locks

Before editing files, honor `.guia/locks/registry.yaml`. If a target file is locked:

1. **Stop** before the edit.
2. **Explain to the developer**, in this order:
   - The lock id and which functionality it protects.
   - Why the planned edit is needed.
   - Expected impact (what changes, who notices).
   - Regression risk (what could break that is currently working).
   - Alternatives (route the change through a different file, scope reduction, etc.).
3. **Ask** for explicit authorization to proceed (or to unlock).
4. Only after the developer authorizes, edit — or use `python core/lock/check-lock.py unlock <id>` if the developer asks for the lock to be removed.

Never bypass a lock silently. The hook at commit time will reject the commit anyway, and the developer loses trust if the agent treats locks as advisory.

Task is closed.
