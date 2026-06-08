---
name: ready
description: HANDOFF to developer validation — does NOT close the task. THE AGENT runs this when implementation is finished, NOT the human; it is the gate that forces human-in-the-loop before $finish. Triggered by /ready or "$ready" / "pronto para validar / enviar para teste". Marks the in-progress D-NNN as awaiting manual validation and records changed files, summary, and pending checks. Do NOT use for: closing an already-validated task (use $finish), or just inspecting the current task without changing its state (use $status).
---

# Ready

**Quem dispara este verbo: a IA, ao terminar de codar.** Nao e o humano avisando que vai validar. `ready` e o handoff que sinaliza "implementacao concluida, aguardando validacao humana em uso real". O proprio nome do estado e `Aguardando validacao`. Fluxo: IA implementa -> IA roda `ready` -> humano valida -> IA roda `finish`. Nao pule o `ready` indo direto pro `finish`: ele e o gate que forca human-in-the-loop (`validate` foi depreciado em F-003 justamente por isso).

Move the current task to developer validation without finalizing it.

Run:

```powershell
.\core\bin\guia.ps1 ready $ARGUMENTS
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and manual gaps with `--pending`.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py ready $ARGUMENTS`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
