from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import pytest
from pydantic import ValidationError

from workflow_catalogue.consts import directories
from workflow_catalogue.schemas.catalogue import EodhCatalogue
from workflow_catalogue.schemas.common import HubType, InputParameter
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
            _notebook_with_input({
                "label": "Items",
                "type": "text",
                "hubType": "stac-collection",
                "description": "Items",
            }),
        )


def test_input_parameter_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError, match="hubtype"):
        EodhNotebookRecord.model_validate(
            _notebook_with_input({"label": "Saved set", "type": "text", "hubtype": "pin-set", "description": "Set id"}),
        )


def _workflow_with_input(param: dict[str, object]) -> dict[str, object]:
    data = json.loads((TEST_DATA_DIR / "workflows/ndvi-workflow.json").read_text(encoding="utf-8"))
    data["properties"]["inputParameters"] = {"stac_item": param}
    return cast("dict[str, object]", data)


def _workflow_param(**fields: object) -> dict[str, object]:
    return {"label": "Input", "type": "text", "description": "An input", **fields}


def _value(field: object) -> object:
    return getattr(field, "value", field)


@pytest.mark.parametrize(
    ("hub_type", "cwl_type"),
    [
        ("stac-item", "Directory"),
        ("stac-item", "string"),
        ("stac-items", "Directory"),
        ("stac-items", "string[]"),
        ("stac-search", "string"),
        ("aoi", "string"),
        ("bbox", "string"),
        ("date", "string"),
        ("date-range", "string[]"),
    ],
)
def test_workflow_input_accepts_allowed_hub_type_and_cwl_type(hub_type: str, cwl_type: str) -> None:
    record = EodhWorkflowRecord.model_validate(
        _workflow_with_input(_workflow_param(hubType=hub_type, cwlType=cwl_type)),
    )
    assert record.properties.input_parameters is not None
    param = record.properties.input_parameters["stac_item"]
    assert param.hub_type == HubType(hub_type)
    assert param.cwl_type == cwl_type


def test_hub_type_has_stac_items() -> None:
    assert HubType("stac-items") == HubType.stac_items


def test_workflow_input_accepts_cwl_type_without_hub_type() -> None:
    record = EodhWorkflowRecord.model_validate(_workflow_with_input(_workflow_param(cwlType="string")))
    assert record.properties.input_parameters is not None
    assert record.properties.input_parameters["stac_item"].hub_type is None
    assert record.properties.input_parameters["stac_item"].cwl_type == "string"


@pytest.mark.parametrize("staging", ["assets", "metadata"])
def test_workflow_input_accepts_staging_on_directory(staging: str) -> None:
    record = EodhWorkflowRecord.model_validate(
        _workflow_with_input(_workflow_param(hubType="stac-item", cwlType="Directory", staging=staging)),
    )
    assert record.properties.input_parameters is not None
    assert _value(record.properties.input_parameters["stac_item"].staging) == staging


def test_input_parameter_rejects_unknown_staging() -> None:
    with pytest.raises(ValidationError, match="staging"):
        EodhWorkflowRecord.model_validate(
            _workflow_with_input(_workflow_param(hubType="stac-item", cwlType="Directory", staging="everything")),
        )


def test_workflow_input_requires_cwl_type() -> None:
    with pytest.raises(ValidationError, match="cwlType"):
        EodhWorkflowRecord.model_validate(_workflow_with_input(_workflow_param(hubType="stac-item")))


def test_workflow_input_without_hub_type_requires_cwl_type() -> None:
    with pytest.raises(ValidationError, match="cwlType"):
        EodhWorkflowRecord.model_validate(_workflow_with_input(_workflow_param()))


def test_notebook_input_rejects_cwl_type() -> None:
    with pytest.raises(ValidationError, match="cwlType"):
        EodhNotebookRecord.model_validate(
            _notebook_with_input({
                "label": "Item",
                "type": "text",
                "hubType": "stac-item",
                "cwlType": "string",
                "description": "Item",
            }),
        )


def test_notebook_input_rejects_staging() -> None:
    with pytest.raises(ValidationError, match="staging"):
        EodhNotebookRecord.model_validate(
            _notebook_with_input({
                "label": "Item",
                "type": "text",
                "hubType": "stac-item",
                "staging": "assets",
                "description": "Item",
            }),
        )


@pytest.mark.parametrize("cwl_type", ["string", "string[]", "File"])
def test_input_parameter_rejects_staging_without_directory(cwl_type: str) -> None:
    with pytest.raises(ValidationError, match="staging"):
        InputParameter.model_validate(_workflow_param(hubType="stac-item", cwlType=cwl_type, staging="assets"))


def test_workflow_input_rejects_staging_without_directory() -> None:
    with pytest.raises(ValidationError, match="staging"):
        EodhWorkflowRecord.model_validate(
            _workflow_with_input(_workflow_param(hubType="stac-item", cwlType="string", staging="metadata")),
        )


def test_input_parameter_rejects_stac_search_directory_and_suggests_stac_items() -> None:
    with pytest.raises(ValidationError, match="stac-items"):
        InputParameter.model_validate(_workflow_param(hubType="stac-search", cwlType="Directory"))


@pytest.mark.parametrize(
    ("hub_type", "cwl_type"),
    [
        ("stac-item", "string[]"),
        ("stac-item", "File"),
        ("stac-items", "string"),
        ("stac-items", "File"),
        ("stac-search", "string[]"),
        ("aoi", "Directory"),
        ("aoi", "string[]"),
        ("bbox", "Directory"),
        ("bbox", "string[]"),
        ("date", "string[]"),
        ("date-range", "string"),
        ("date-range", "Directory"),
        ("pin-set", "string"),
        ("pin-set", "Directory"),
    ],
)
def test_input_parameter_rejects_hub_type_that_does_not_fit_cwl_type(hub_type: str, cwl_type: str) -> None:
    with pytest.raises(ValidationError, match="cwlType"):
        InputParameter.model_validate(_workflow_param(hubType=hub_type, cwlType=cwl_type))


def test_workflow_record_rejects_hub_type_that_does_not_fit_cwl_type() -> None:
    with pytest.raises(ValidationError, match="cwlType"):
        EodhWorkflowRecord.model_validate(_workflow_with_input(_workflow_param(hubType="date-range", cwlType="string")))


def test_workflow_input_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError, match="cwltype"):
        EodhWorkflowRecord.model_validate(_workflow_with_input(_workflow_param(cwlType="string", cwltype="string")))


def test_input_parameter_accepts_variable_ref() -> None:
    record = EodhWorkflowRecord.model_validate(
        _workflow_with_input(_workflow_param(hubType="bbox", cwlType="string", variableRef="AOI")),
    )
    assert record.properties.input_parameters is not None
    assert record.properties.input_parameters["stac_item"].variable_ref == "AOI"


def test_variable_ref_is_described_as_deprecated() -> None:
    description = InputParameter.model_fields["variable_ref"].description
    assert description is not None
    assert "deprecated" in description.lower()


# Record content checks


WORKFLOWS_NOTEBOOKS_DIR = CATALOGUE_DIR / "eodh-workflows-notebooks"


@pytest.mark.parametrize(
    "workflow_definition_path",
    [p for p in (TEST_DATA_DIR / "workflows").glob("*.json") if "inputParameters" in p.read_text(encoding="utf-8")],
    ids=lambda p: p.stem,
)
def test_workflow_fixture_inputs_have_cwl_type(workflow_definition_path: Path) -> None:
    data = json.loads(workflow_definition_path.read_text(encoding="utf-8"))
    for name, param in data["properties"]["inputParameters"].items():
        assert "cwlType" in param, name


@pytest.mark.parametrize("record_id", ["ndvi-workflow", "ndwi-workflow", "clip-workflow"])
def test_catalogue_stac_item_workflow_inputs(record_id: str) -> None:
    data = json.loads((WORKFLOWS_NOTEBOOKS_DIR / "workflows" / f"{record_id}.json").read_text(encoding="utf-8"))
    params = data["properties"]["inputParameters"]

    stac_item = params["stac_item"]
    assert stac_item["hubType"] == "stac-item"
    assert stac_item["cwlType"] == "Directory"
    assert stac_item["staging"] == "assets"

    bbox = params["bbox"]
    assert bbox["hubType"] == "bbox"
    assert bbox["cwlType"] == "string"
    assert bbox["required"] is False
    assert "xmin,ymin,xmax,ymax" in bbox["description"]
    assert "EPSG:4326" in bbox["description"]
    assert bbox["variableRef"] == "AOI"


@pytest.mark.parametrize(
    "record_id",
    ["ndvi_notebook", "ndwi_notebook", "landcover-classification-notebook"],
)
def test_catalogue_stac_item_notebook_inputs(record_id: str) -> None:
    data = json.loads((WORKFLOWS_NOTEBOOKS_DIR / "notebooks" / f"{record_id}.json").read_text(encoding="utf-8"))
    params = data["properties"]["inputParameters"]

    assert params["STAC_ITEM_LINK"]["hubType"] == "stac-item"
    assert params["STAC_ITEM_LINK"]["type"] == "text"
    assert params["AOI"]["hubType"] == "aoi"
    assert params["AOI"]["type"] == "text"


def test_catalogue_pin_set_starter_inputs() -> None:
    path = WORKFLOWS_NOTEBOOKS_DIR / "notebooks" / "pin_set_starter.json"
    assert path.exists()
    params = json.loads(path.read_text(encoding="utf-8"))["properties"]["inputParameters"]

    assert params["PIN_SET_ID"]["hubType"] == "pin-set"
    assert params["PIN_SET_ID"]["type"] == "text"
