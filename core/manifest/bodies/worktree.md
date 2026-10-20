# Worktree

{{include_per_target: _partials/run_cmd}}

```text
worktree add D-NNN
worktree remove D-NNN
```

- State stays in the main tree; commands run inside the worktree resolve the demand by branch.
- The worktree is where the demand's chat works: when this chat is that chat, it also carries the demand's name and session (below) - `worktree add` does not replace that step.

{{include_per_target: _partials/name_chat}}
