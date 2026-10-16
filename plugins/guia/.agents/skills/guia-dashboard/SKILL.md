---
name: guia-dashboard
description: "READ-ONLY — open the local dashboard in the browser: every Guia project registered on this machine, its demands by stage (Backlog, Planejada, DEV, validacao, PR, fila, Integrada, Bloqueada), the merge queue in order (who is at the head, why each item waits) and whether a queue executor is alive. Serves only on 127.0.0.1 and never changes state. Options: `--scan <folder>` / `--add <folder>` / `--remove <folder>` to manage the project list, `--list`, `--json`, `--port`, `--no-open`. For one task in the terminal use `status`; for the queue in text use `queue`."
---

# Dashboard

Open the local, read-only dashboard: the Guia projects on this machine, their demands by stage and the merge queue (head, order, why each item waits, executor alive or not).

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
dashboard                    # registers this project and serves http://127.0.0.1:8765/
dashboard --scan <folder>    # finds Guia projects under the folder and registers them
dashboard --add <folder>     # registers one project; --remove <folder> takes it out
dashboard --list             # registered projects
dashboard --json             # the same snapshot the page shows, in JSON
```

- The server keeps running until Ctrl+C: start it **in the background** and show the developer the `PAINEL: <url>` line.
- The project list lives in `~/.guia/projects.json` (`$GUIA_HOME` overrides). Running `dashboard` inside a project registers it.
- Read-only: the page never changes state. Act on what it shows with the usual verbs (`queue`, `approve`, `finish`...).
