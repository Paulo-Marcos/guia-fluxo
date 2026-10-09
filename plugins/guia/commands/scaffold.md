---
description: "SETUP — generate delivery scaffolding: `scaffold auditoria` (audit status workflow), `pr-template`, `dependabot`; or print `ci-ok` (aggregator job) and `protection` (branch protection command) for the developer to apply. Applying GitHub settings is the developer's decision."
---

# Scaffold

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
scaffold auditoria | pr-template | dependabot
scaffold ci-ok | protection        # prints; the developer applies
```
