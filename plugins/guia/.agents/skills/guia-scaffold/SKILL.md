---
name: guia-scaffold
description: "SETUP — generate delivery scaffolding: `scaffold auditoria` (audit status workflow), `pr-template`, `dependabot`; or print `ci-ok` (aggregator job) and `protection` (branch protection command) for the developer to apply. Applying GitHub settings is the developer's decision."
---

# Scaffold

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
scaffold auditoria | pr-template | dependabot
scaffold ci-ok | protection        # prints; the developer applies
```
