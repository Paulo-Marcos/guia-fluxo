# Backlog

Manage parked work without starting implementation. `backlog add` creates a `D-NNN` task with `status=Backlog`. `backlog list` shows all parked items. `backlog promote` delegates to the `/promote` flow.

{{include: _partials/title_context_rules.md}}

{{include_per_target: _partials/run_cmd}}

```text
backlog add "<title>" --context "<context>"    # if the user provided a title
backlog list                                   # show parked work
backlog promote B-001                          # promote a backlog item
```

{{include_per_target: _partials/post_cli}}

**Do not start implementation.** Backlog parks work for later. To begin work on a parked item, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
