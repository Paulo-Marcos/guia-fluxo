---
description: "READ-ONLY — open the local dashboard in the browser: every Guia project registered on this machine, its demands by stage (Backlog, Planejada, DEV, validacao, PR, fila, Integrada, Bloqueada), the merge queue in order (who is at the head, why each item waits) and whether a queue executor is alive. Serves only on 127.0.0.1. The agent never changes state through it: its only writes are two owner buttons (D-187: resume a paused queue, start the queue executor when none is alive), which run the engine inside the project behind Host/Origin checks and a per-session token. Options: `--scan <folder>` / `--add <folder>` / `--remove <folder>` to manage the project list, `--list`, `--json`, `--port`, `--no-open`. For one task in the terminal use `status`; for the queue in text use `queue`."
---

# Dashboard

Open the local dashboard: the Guia projects on this machine, their demands by stage and the merge queue (head, order, why each item waits, executor alive or not).

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
dashboard                    # registers this project and serves http://127.0.0.1:8765/
dashboard --scan <folder>    # finds Guia projects under the folder and registers them
dashboard --add <folder>     # registers one project; --remove <folder> takes it out
dashboard --list             # registered projects
dashboard --json             # the same snapshot the page shows, in JSON
```

- The server keeps running until Ctrl+C: start it **in the background** and show the developer the `PAINEL: <url>` line.
- The project list lives in `~/.guia/projects.json` (`$GUIA_HOME` overrides). Running `dashboard` inside a project registers it.
- The page reads state. Its only two buttons belong to the developer (D-187): **Retomar fila** (paused or frozen queue -> `queue resume`) and **Iniciar executor** (`pr` mode, no live executor -> `queue run` detached, output in `.guia/queue/executor-painel.log`). **Never click them yourself** - like `queue-control`, they are the user's action. Act on everything else with the usual verbs (`queue`, `approve`, `finish`...).
