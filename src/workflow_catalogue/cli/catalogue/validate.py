"""Catalogue validation CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from workflow_catalogue.schemas.catalogue import EodhCatalogue
from workflow_catalogue.schemas.notebook import EodhNotebookRecord
from workflow_catalogue.schemas.workflow import EodhWorkflowRecord
from workflow_catalogue.utils.logging import get_logger

_logger = get_logger(__name__)


def _validate_schema(file_path: Path) -> None:
    """Detect record type and validate against the appropriate schema.

    Args:
        file_path: Path to the JSON file to validate.

    Raises:
        ValueError: If the record type is unknown or filename/ID mismatch.

    """
    data = json.loads(file_path.read_text(encoding="utf-8"))

    if file_path.name == "catalog.json":
        EodhCatalogue.model_validate(data)
        return

    record_id = data.get("id")
    if record_id and record_id != file_path.stem:
        msg = f"Filename '{file_path.stem}' does not match record id '{record_id}'"
        raise ValueError(msg)

    record_type = data.get("properties", {}).get("type")
    if record_type == "workflow":
        EodhWorkflowRecord.model_validate(data)
    elif record_type == "notebook":
        EodhNotebookRecord.model_validate(data)
    else:
        msg = f"Unknown or missing record type: {record_type}"
        raise ValueError(msg)


@click.command("validate")
@click.option(
    "--catalogue-path",
    type=click.Path(exists=True, path_type=Path, file_okay=False, dir_okay=True),  # type: ignore[type-var]
    required=True,
    help="Path to catalogue directory.",
)
@click.option(
    "--changed-files",
    type=str,
    default=None,
    help="Comma-separated list of changed file paths. If provided, only these files are validated.",
)
def validate_catalogue(
    catalogue_path: Path,
    changed_files: str | None,
) -> None:
    """Validate JSON records in the catalogue directory against EODH schemas."""
    _logger.info("Validating catalogue at: %s", catalogue_path)

    if changed_files:
        files_to_validate = [Path(f.strip()) for f in changed_files.split(",") if f.strip().endswith(".json")]
    else:
        files_to_validate = sorted(catalogue_path.rglob("*.json"))

    if not files_to_validate:
        _logger.info("No JSON files to validate.")
        return

    errors: list[tuple[Path, Exception]] = []
    for file_path in files_to_validate:
        try:
            _validate_schema(file_path)
            _logger.info("PASS: %s", file_path)
        except Exception as exc:
            _logger.error("FAIL: %s\n  %s", file_path, exc)
            errors.append((file_path, exc))

    if errors:
        _logger.error("%d file(s) failed validation.", len(errors))
        sys.exit(1)

    _logger.info("All %d file(s) passed validation.", len(files_to_validate))
