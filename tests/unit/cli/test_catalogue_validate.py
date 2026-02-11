"""Tests for catalogue validation CLI."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from click.testing import CliRunner

from workflow_catalogue.cli.catalogue.validate import validate_catalogue
from workflow_catalogue.consts import directories

if TYPE_CHECKING:
    from pathlib import Path

CATALOGUE_DIR = directories.CATALOGUE_DIR
TEST_DATA_DIR = directories.TESTS_DIR / "test_data"


def test_validate_catalogue_full_directory() -> None:
    """Validates all records in the catalogue directory."""
    runner = CliRunner()
    result = runner.invoke(validate_catalogue, ["--catalogue-path", str(CATALOGUE_DIR)])
    assert result.exit_code == 0


def test_validate_catalogue_test_data_directory() -> None:
    """Validates all records in the test_data directory."""
    runner = CliRunner()
    result = runner.invoke(validate_catalogue, ["--catalogue-path", str(TEST_DATA_DIR)])
    assert result.exit_code == 0


def test_validate_catalogue_single_workflow_via_changed_files() -> None:
    """Validates a single workflow file using --changed-files."""
    wf_file = CATALOGUE_DIR / "eodh-workflows-notebooks" / "workflows" / "ndvi-workflow.json"
    runner = CliRunner()
    result = runner.invoke(
        validate_catalogue,
        ["--catalogue-path", str(CATALOGUE_DIR), "--changed-files", str(wf_file)],
    )
    assert result.exit_code == 0


def test_validate_catalogue_single_notebook_via_changed_files() -> None:
    """Validates a single notebook file using --changed-files."""
    nb_file = CATALOGUE_DIR / "eodh-workflows-notebooks" / "notebooks" / "ndvi_calculation.json"
    runner = CliRunner()
    result = runner.invoke(
        validate_catalogue,
        ["--catalogue-path", str(CATALOGUE_DIR), "--changed-files", str(nb_file)],
    )
    assert result.exit_code == 0


def test_validate_catalogue_invalid_json(tmp_path: Path) -> None:
    """Fails validation for a JSON file missing required fields."""
    invalid_file = tmp_path / "bad-workflow.json"
    invalid_file.write_text(json.dumps({"id": "bad", "properties": {"type": "workflow"}}), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(validate_catalogue, ["--catalogue-path", str(tmp_path)])
    assert result.exit_code == 1


def test_validate_catalogue_filename_id_mismatch(tmp_path: Path) -> None:
    """Fails validation when filename stem does not match record id."""
    wf_file = CATALOGUE_DIR / "eodh-workflows-notebooks" / "workflows" / "ndvi-workflow.json"
    data = json.loads(wf_file.read_text(encoding="utf-8"))
    data["id"] = "mismatched-id"
    mismatched_file = tmp_path / "ndvi-workflow.json"
    mismatched_file.write_text(json.dumps(data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(validate_catalogue, ["--catalogue-path", str(tmp_path)])
    assert result.exit_code == 1


def test_validate_catalogue_no_json_files(tmp_path: Path) -> None:
    """Succeeds with no files to validate."""
    runner = CliRunner()
    result = runner.invoke(validate_catalogue, ["--catalogue-path", str(tmp_path)])
    assert result.exit_code == 0


def test_validate_catalogue_changed_files_non_json_ignored() -> None:
    """Non-JSON files in --changed-files are ignored."""
    runner = CliRunner()
    result = runner.invoke(
        validate_catalogue,
        ["--catalogue-path", str(CATALOGUE_DIR), "--changed-files", "README.md,docs/guide.rst"],
    )
    assert result.exit_code == 0


def test_validate_catalogue_unknown_record_type(tmp_path: Path) -> None:
    """Fails for unknown record type."""
    unknown_file = tmp_path / "unknown.json"
    unknown_file.write_text(
        json.dumps({"id": "unknown", "properties": {"type": "something_else"}}),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(validate_catalogue, ["--catalogue-path", str(tmp_path)])
    assert result.exit_code == 1
