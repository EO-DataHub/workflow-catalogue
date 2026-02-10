from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from workflow_catalogue.consts import directories
from workflow_catalogue.schemas.catalogue import EodhCatalogue
from workflow_catalogue.schemas.notebook import EodhNotebookRecord
from workflow_catalogue.schemas.workflow import EodhWorkflowRecord

if TYPE_CHECKING:
    from pathlib import Path

TEST_DATA_DIR = directories.TESTS_DIR / "test_data"
CATALOGUE_DIR = directories.CATALOGUE_DIR


@pytest.mark.parametrize(
    "workflow_definition_path",
    list((TEST_DATA_DIR / "workflows").glob("*.json")),
    ids=lambda p: p.stem,
)
def test_workflow(workflow_definition_path: Path) -> None:
    EodhWorkflowRecord.model_validate(json.loads(workflow_definition_path.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "notebook_definition_path",
    list((TEST_DATA_DIR / "notebooks").glob("*.json")),
    ids=lambda p: p.stem,
)
def test_notebook(notebook_definition_path: Path) -> None:
    EodhNotebookRecord.model_validate(json.loads(notebook_definition_path.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "catalogue_path",
    [TEST_DATA_DIR / "catalog.json"],
    ids=lambda p: p.stem,
)
def test_catalogue(catalogue_path: Path) -> None:
    EodhCatalogue.model_validate(json.loads(catalogue_path.read_text(encoding="utf-8")))


# Tests for the actual catalogue/ directory data (defense-in-depth)


@pytest.mark.parametrize(
    "workflow_definition_path",
    list((CATALOGUE_DIR / "workflows").glob("*.json")),
    ids=lambda p: p.stem,
)
def test_catalogue_workflow(workflow_definition_path: Path) -> None:
    EodhWorkflowRecord.model_validate(json.loads(workflow_definition_path.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "notebook_definition_path",
    list((CATALOGUE_DIR / "notebooks").glob("*.json")),
    ids=lambda p: p.stem,
)
def test_catalogue_notebook(notebook_definition_path: Path) -> None:
    EodhNotebookRecord.model_validate(json.loads(notebook_definition_path.read_text(encoding="utf-8")))


def test_catalogue_catalog_json() -> None:
    EodhCatalogue.model_validate(json.loads((CATALOGUE_DIR / "catalog.json").read_text(encoding="utf-8")))
