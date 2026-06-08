---
name: guia-ready
description: HANDOFF to developer validation — does NOT close the task. THE AGENT runs this when implementation is finished, NOT the human; it is the gate that forces human-in-the-loop before $finish. Triggered by /ready or "$ready" / "pronto para validar / enviar para teste". Marks the in-progress D-NNN as awaiting manual validation and records changed files, summary, and pending checks. Do NOT use for: closing an already-validated task (use $finish), or just inspecting the current task without changing its state (use $status).
---

# Ready

**The agent (you) calls this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish` — that bypasses the human-in-the-loop gate (the reason `validate` was deprecated in F-003).

Run:

```powershell
.\core\bin\guia.ps1 ready <D-NNN> --file path/to/file --summary "What changed" --validation "What passed"
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands run with `--validation`, and manual gaps still pending with `--pending`.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py ready <D-NNN> ...`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
