# Dashboard

Open the local dashboard: the Guia projects on this machine, their demands by stage and the merge queue (head, order, why each item waits, executor alive or not).

{{include_per_target: _partials/run_cmd}}

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
