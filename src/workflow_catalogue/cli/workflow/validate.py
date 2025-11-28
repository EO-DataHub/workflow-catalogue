"""Workflow validation CLI."""

from __future__ import annotations

import json
from pathlib import Path

import click

from workflow_catalogue.schemas.workflow import EodhWorkflowRecord
from workflow_catalogue.utils.logging import get_logger

_logger = get_logger(__name__)


@click.command("validate")
@click.option(
    "--workflow-definition-path",
    type=click.Path(exists=True, path_type=Path, file_okay=True, dir_okay=False),  # type: ignore[type-var]
    required=True,
    help="Path to workflow definition.",
)
def validate_workflow_schema(
    workflow_definition_path: Path,
) -> None:
    """Validate workflow schema."""
    _logger.info(
        "Running with: %s",
        json.dumps(
            {"workflow_definition_path": workflow_definition_path.as_posix()},
            indent=4,
        ),
    )

    EodhWorkflowRecord.model_validate(json.loads(workflow_definition_path.read_text(encoding="utf-8")))

    _logger.info("Workflow definition is valid.")
