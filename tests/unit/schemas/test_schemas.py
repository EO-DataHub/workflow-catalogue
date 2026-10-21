from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import pytest
from pydantic import ValidationError

from workflow_catalogue.consts import directories
from workflow_catalogue.schemas.catalogue import EodhCatalogue
from workflow_catalogue.schemas.common import HubType
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
    list(CATALOGUE_DIR.glob("*/workflows/*.json")),
    ids=lambda p: p.stem,
)
def test_catalogue_workflow(workflow_definition_path: Path) -> None:
    EodhWorkflowRecord.model_validate(json.loads(workflow_definition_path.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "notebook_definition_path",
    list(CATALOGUE_DIR.glob("*/notebooks/*.json")),
    ids=lambda p: p.stem,
)
def test_catalogue_notebook(notebook_definition_path: Path) -> None:
    EodhNotebookRecord.model_validate(json.loads(notebook_definition_path.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "catalog_path",
    list(CATALOGUE_DIR.glob("*/catalog.json")),
    ids=lambda p: p.parent.name,
)
def test_catalogue_catalog_json(catalog_path: Path) -> None:
    EodhCatalogue.model_validate(json.loads(catalog_path.read_text(encoding="utf-8")))


# Input parameter checks


def _notebook_with_input(param: dict[str, object]) -> dict[str, object]:
    data = json.loads(
        (CATALOGUE_DIR / "eodh-workflows-notebooks/notebooks/ndvi_notebook.json").read_text(encoding="utf-8")
    )
    data["properties"]["inputParameters"] = {"PIN_SET_ID": param}
    return cast("dict[str, object]", data)


def test_input_parameter_accepts_hub_type() -> None:
    record = EodhNotebookRecord.model_validate(
        _notebook_with_input({"label": "Saved set", "type": "text", "hubType": "pin-set", "description": "Set id"}),
    )
    assert record.properties.input_parameters is not None
    assert record.properties.input_parameters["PIN_SET_ID"].hub_type == HubType.pin_set


def test_input_parameter_rejects_unknown_hub_type() -> None:
    with pytest.raises(ValidationError, match="hubType"):
        EodhNotebookRecord.model_validate(
            _notebook_with_input({"label": "Items", "type": "text", "hubType": "stac-items", "description": "Items"}),
        )


def test_input_parameter_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError, match="hubtype"):
        EodhNotebookRecord.model_validate(
            _notebook_with_input({"label": "Saved set", "type": "text", "hubtype": "pin-set", "description": "Set id"}),
        )
