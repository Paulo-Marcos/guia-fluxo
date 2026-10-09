---
description: "READ-ONLY by default — show open Dependabot PRs and what the executor will do with them (security first, then the batch when the queue is empty); `--now` creates the batch demand right away (agent at level >= `queue`). `--json` for machine output. The batch is worked like any demand (`pr-bump` skill)."
---

# Deps

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
deps [--json]
deps --now
```
