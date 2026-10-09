---
description: "CHANGELOG — `changelog add [D-NNN] --text \"<entry with the id>\" [--category Added|Changed|Deprecated|Removed|Fixed|Security]` writes the demand's fragment in `changelog.d/` (with `delivery.changelog.style: fragments`; never edit CHANGELOG.md in a PR). `changelog compile --version X.Y.Z` folds the fragments into CHANGELOG.md at release time (developer)."
---

# Changelog

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
changelog add [D-NNN] --text "<what changed and why (D-NNN)>"
changelog compile --version X.Y.Z   # release only
```
