---
name: guia-deps
description: "READ-ONLY by default — show open Dependabot PRs and what the executor will do with them (security first, then the batch when the queue is empty); `--now` creates the batch demand right away (agent at level >= `queue`). `--json` for machine output. The batch is worked like any demand (`pr-bump` skill)."
---

# Deps

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
deps [--json]
deps --now
```
