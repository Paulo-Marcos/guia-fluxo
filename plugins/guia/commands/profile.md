---
description: "SETUP — propose the delivery profile from the repository facts (`solo-direct`, `pr-basic`, `pr-audited`); `--apply` writes the block without overwriting existing keys, `--name` picks another profile, `--json` for machine output. Changing delivery defaults is the developer's decision: show the proposal and ask before `--apply`."
---

# Profile

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
profile [--json]
profile --apply [--name pr-audited]
```
