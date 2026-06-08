# Chore

Create a chore task (maintenance, small refactor, build/lint, docs or config adjustments — anything that is not a new feature nor a bug, but deserves a trace). Introduced in ADR-0011 Phase 4.

{{include: _partials/title_context_rules.md}}

Run:

```powershell
.\core\bin\guia.ps1 chore "<title>" --context "<what + why>"
```

Useful flags:
- `--context "<what/why>"` — describes the maintenance and its motivation.
- `--status backlog|planned|in-development` (default `in-development`).
- `--origin "<source>"`.

When to use `chore` vs alternatives:
- **New feature** (user-visible capability) → use `/feature`.
- **Bug** (broken/regression) → use `/bug`.
- **Chore** → everything else: cleanup, dep upgrade, folder organization, config tweak, improving an error message without changing behavior.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py chore "<title>"`.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Then continue with the maintenance work.
