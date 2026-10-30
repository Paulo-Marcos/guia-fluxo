---
description: "CLEANUP — list what pollutes the folder that holds the projects (e.g. `C:/DEV`): inactive worktrees of this project (demand Integrada/Finalizada/Cancelada, or branch already in the base, and no local changes) and loose files (audit reports, gate logs, `.msg`, patches). Report only; `--remove <path|D-NNN|file>` (repeatable) or `--remove all` removes ONLY with the developer's ok, through the safe `worktree remove` path. `--json` for machine output; `--session-start` is the one-line report of the plugin's SessionStart hook. New worktrees live in `../<repo>-worktrees/<idCompact>`; agent artifacts go in `.guia/tmp/<D-NNN>/`."
---

# Cleanup

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
cleanup                       # report only: inactive worktrees + loose files in the parent folder
cleanup --json
cleanup --remove <path|D-NNN|file> [--remove ...]   # ONLY with the developer's ok
cleanup --remove all                                # ONLY with the developer's ok
```

- **Report first, never remove on your own.** Show the list, ask the developer which items go, and run `--remove` only with their ok (quote their words). The engine refuses anything the report did not propose and removes worktrees through the same safe path as `worktree remove` (junctions undone first, refuses local changes).
- An inactive worktree is one whose demand is Integrada/Finalizada/Validada/Cancelada. A worktree with no demand is never proposed (a fresh branch also looks "already in the base"). With uncommitted changes, an ignored file that removal would delete (e.g. `.env`) or a detached HEAD it is listed as kept, never proposed.
- A loose file is an agent artifact in the folder that holds the projects (e.g. `C:/DEV`): logs, `.msg`, patches, command output, draft `.txt`/`.md`/`.json` with a number or step prefix in the name. Never dotfiles or documents.
- `--remove all` takes only what the last `cleanup` listing showed (saved in `.guia/tmp/`); run the listing first.
- New worktrees live in `../<repo>-worktrees/<idCompact>` (one folder per project); agent artifacts (audit reports, gate logs, commit messages, patches) go in `.guia/tmp/<D-NNN>/` - the path `start` prints as `ARTIFACTS_DIR` and `next --json` returns as `artifactsDir`. Never write them in the parent folder.
- The plugin's SessionStart hook runs `cleanup --session-start`: one line when there is something to clean, silent otherwise.
