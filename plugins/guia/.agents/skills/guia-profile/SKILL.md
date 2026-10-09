---
name: guia-profile
description: "SETUP — propose the delivery profile from the repository facts (`solo-direct`, `pr-basic`, `pr-audited`); `--apply` writes the block without overwriting existing keys, `--name` picks another profile, `--json` for machine output. Changing delivery defaults is the developer's decision: show the proposal and ask before `--apply`."
---

# Profile

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
profile [--json]
profile --apply [--name pr-audited]
```
