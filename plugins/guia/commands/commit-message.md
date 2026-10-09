---
description: "COMMIT MESSAGE — print the commit message in the configured format (`gitmoji-conventional`: `<emoji> <type>(D-NNN): <title>`, the why as body, `[unlock:<lock>] motivo: ...` marks and `Co-Authored-By`). In `pr` mode the marks come from the branch diff against the base. Options: `--subject`, `--body`, `--unlock-reason \"<lock>=<reason>\"` (required when a lock is touched). Use it to commit before `ship`."
---

# Commit message

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
commit-message [D-NNN] --subject "..." --body "<why>" --unlock-reason "<reason>" > msg.txt
git commit -F msg.txt
```

- A lock touched without a reason refuses, naming each lock: the developer's authorization comes first.
