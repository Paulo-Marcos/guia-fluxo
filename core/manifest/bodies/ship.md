# Ship

Take the demand from its worktree to a pull request. All checks run before any effect: if one refuses, nothing was pushed and the state did not change.

{{include_per_target: _partials/run_cmd}}

```text
ship [D-NNN] --subject "<emoji> <type>(D-NNN): <title>" --body "<why>" --unlock-reason "<reason>"
```

- Commit first (`commit-message` builds the message); ship pushes what is committed.
- Run the gate with `gate` (not by hand) once the tree is committed: it records the tree that passed, and ship skips a tree already recorded instead of running the gate twice (`--rerun-gate` forces).
- Without an id, the demand comes from the `d-NNN-*` branch.
- Next step: `audit` on the new head - at levels `pr`/`queue`/`pilot`, go on without asking.

{{include_per_target: _partials/post_cli}}

{{include: _partials/conductor.md}}
