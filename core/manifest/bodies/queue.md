# Queue

The chat launches (`ship` -> `audit` -> `queue add`) and is free; one executor integrates one PR at a time.

{{include_per_target: _partials/run_cmd}}

```text
queue                     # list, with the reason each item waits
queue add [D-NNN] [--priority hotfix]
queue import              # PRs labeled guia:fila from the cloud (no audit yet)
```

- If `add` prints `alwaysHuman: ...`, the item waits for the developer's `approve`: tell them the reason.

{{include_per_target: _partials/post_cli}}
