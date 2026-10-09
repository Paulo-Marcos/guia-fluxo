---
name: guia-worktree
description: "WORKTREE — `worktree add D-NNN` creates the demand's isolated worktree and branch (`d-NNN-<slug>`, following the PR branch from origin when one exists); `worktree remove D-NNN [--force]` removes it safely (junctions undone first). Options: `--path`, `--branch`. Run from the main tree."
---

# Worktree

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
worktree add D-NNN
worktree remove D-NNN
```

- State stays in the main tree; commands run inside the worktree resolve the demand by branch.
