# Chore

Create a chore task for maintenance that deserves a trace but is not a new feature nor a bug fix: small refactor, dependency upgrade, build/lint tweak, config or doc adjustment without behavior change.

{{include: _partials/title_context_rules.md}}

{{include_per_target: _partials/run_cmd}}

```text
chore "<title>" --context "<what + why>"
```

Useful flags:
- `--context "<what/why>"` — describes the maintenance and its motivation.
- `--status backlog|planned|in-development` (default `in-development`).
- `--origin "<source>"`.

When to use `chore` vs alternatives:
- **New feature** (user-visible capability) → use `/feature`.
- **Bug** (broken/regression) → use `/bug`.
- **Chore** → everything else: cleanup, dep upgrade, folder organization, config tweak, improving an error message without changing behavior.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Then continue with the maintenance work.
