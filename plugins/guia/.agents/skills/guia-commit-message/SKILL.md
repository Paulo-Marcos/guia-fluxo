---
name: guia-commit-message
description: "COMMIT MESSAGE — print the commit message in the configured format (`gitmoji-conventional`: `<emoji> <type>(D-NNN): <title>`, the why as body, `[unlock:<lock>] motivo: ...` marks and `Co-Authored-By`). In `pr` mode the marks come from the branch diff against the base. Options: `--subject`, `--body`, `--unlock-reason \"<lock>=<reason>\"` (required when a lock is touched). Use it to commit before `ship`."
---

# Commit message

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
commit-message [D-NNN] --subject "..." --body "<why>" --unlock-reason "<reason>" > msg.txt
git commit -F msg.txt
```

- A lock touched without a reason refuses, naming each lock: the developer's authorization comes first.
