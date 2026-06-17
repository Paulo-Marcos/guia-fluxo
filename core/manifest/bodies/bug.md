# Bug

Create a bug task before editing code. Use for a regression, a defect, or any incorrect behavior that needs investigation and fix.

{{include: _partials/title_context_rules.md}}

{{include_per_target: _partials/run_cmd}}

```text
bug "<title>" --context "<observed symptom + impact>"
```

Useful flags:
- `--context "<symptom + impact>"` — observed behavior vs expected, who is affected.
- `--status backlog|planned|in-development` (default `in-development`) — `backlog` if not triaged, `planned` if planned but not now.
- `--origin "<source>"` — alternate origin.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Then continue with the investigation and fix.
