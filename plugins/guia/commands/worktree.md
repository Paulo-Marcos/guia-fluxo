---
description: "WORKTREE — `worktree add D-NNN` creates the demand's isolated worktree and branch (`d-NNN-<slug>`, following the PR branch from origin when one exists); `worktree remove D-NNN [--force]` removes it safely (junctions undone first). Options: `--path`, `--branch`. Run from the main tree."
---

# Worktree

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
worktree add D-NNN
worktree remove D-NNN
```

- State stays in the main tree; commands run inside the worktree resolve the demand by branch.
