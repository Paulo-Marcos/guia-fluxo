# Commit message

{{include_per_target: _partials/run_cmd}}

```text
commit-message [D-NNN] --subject "..." --body "<why>" --unlock-reason "<reason>" > msg.txt
git commit -F msg.txt
```

- A lock touched without a reason refuses, naming each lock: the developer's authorization comes first.
