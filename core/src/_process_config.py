"""Default .guia/process.json schema.

Isolated so the schema can evolve independently and tests can compare
against a single canonical fixture.
"""

from __future__ import annotations

from typing import Any

from _constants import (
    DEMAND_TITLE_FORMAT_DEFAULT,
    KIND_FEATURE,
    PREFIX_BACKLOG,
    PREFIX_FEATURE,
    PREFIX_ISSUE,
    STATUS_AWAITING_VALIDATION,
    STATUS_VALIDATED,
)


def default_process(project_name: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "name": "guia-fluxo",
        "projectName": project_name,
        "ids": {
            "featurePrefix": PREFIX_FEATURE,
            "issuePrefix": PREFIX_ISSUE,
            "backlogPrefix": PREFIX_BACKLOG,
            "digits": 3,
        },
        "demandTitleFormat": DEMAND_TITLE_FORMAT_DEFAULT,
        "ready": {
            "status": STATUS_AWAITING_VALIDATION,
            "runValidationByDefault": False,
            "validationCommands": [],
        },
        "finish": {
            "status": STATUS_VALIDATED,
            "runValidationByDefault": False,
            "validationCommands": [],
            # D-095: validacao consultiva de qualidade (skills) antes de fechar.
            # Default True (o dono quer sempre); pule um run com --quality-skip.
            "qualityGateByDefault": True,
            "commitByDefault": True,
            "lockOnFinish": False,
        },
        "validate": {
            "status": STATUS_VALIDATED,
            "deprecatedAliasFor": "finish --no-commit",
            "lockOnValidate": False,
        },
    }


__all__ = ["default_process"]
