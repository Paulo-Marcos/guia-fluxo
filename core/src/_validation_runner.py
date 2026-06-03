"""Run validation commands declared in process.json."""

from __future__ import annotations

import subprocess
from typing import Any

from _constants import ROOT
from _tasks import merge_list


def run_validation_commands(
    task: dict[str, Any],
    config: dict[str, Any],
    section: str,
) -> None:
    commands = config.get(section, {}).get("validationCommands", [])
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, shell=True, text=True)
        status = "OK" if result.returncode == 0 else f"falhou ({result.returncode})"
        merge_list(task, "validations", [f"{command} - {status}"])
        if result.returncode != 0:
            raise SystemExit(result.returncode)


__all__ = ["run_validation_commands"]
