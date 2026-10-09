# Ship

Take the demand from its worktree to a pull request. All checks run before any effect: if one refuses, nothing was pushed and the state did not change.

{{include_per_target: _partials/run_cmd}}

```text
ship [D-NNN] --subject "<emoji> <type>(D-NNN): <title>" --body "<why>" --unlock-reason "<reason>"
```

- Commit first (`commit-message` builds the message); ship pushes what is committed.
- Without an id, the demand comes from the `d-NNN-*` branch.
- Next step: `audit` on the new head.

{{include_per_target: _partials/post_cli}}
