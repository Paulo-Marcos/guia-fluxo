---
name: guia-changelog
description: "CHANGELOG — `changelog add [D-NNN] --text \"<entry with the id>\" [--category Added|Changed|Deprecated|Removed|Fixed|Security]` writes the demand's fragment in `changelog.d/` (with `delivery.changelog.style: fragments`; never edit CHANGELOG.md in a PR). `changelog compile --version X.Y.Z` folds the fragments into CHANGELOG.md at release time (developer)."
---

# Changelog

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
changelog add [D-NNN] --text "<what changed and why (D-NNN)>"
changelog compile --version X.Y.Z   # release only
```
