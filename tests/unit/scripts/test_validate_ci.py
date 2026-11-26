"""Tests for the CWL input checks in scripts/validate_ci.py."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from typing import TYPE_CHECKING, Any

import pytest
import requests

from workflow_catalogue.consts import directories

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType

SCRIPT_PATH = directories.ROOT_DIR / "scripts" / "validate_ci.py"
TEST_DATA_DIR = directories.TESTS_DIR / "test_data"
CWL_DIR = TEST_DATA_DIR / "cwl"
CWL_URL = "https://example.com/cwl/workflow.cwl"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status_code
        self.ok = status_code < 400  # noqa: PLR2004

    def raise_for_status(self) -> None:
        if not self.ok:
            msg = f"HTTP {self.status_code}"
            raise requests.HTTPError(msg)


@pytest.fixture
def validate_ci() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_ci", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cwltool_passes(validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(validate_ci.subprocess, "run", fake_run)


def _serve_cwl(validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, cwl_file: str) -> None:
    text = (CWL_DIR / cwl_file).read_text(encoding="utf-8")

    def fake_get(url: str, **_: Any) -> FakeResponse:
        assert url == CWL_URL
        return FakeResponse(text)

    monkeypatch.setattr(validate_ci.requests, "get", fake_get)


def _write_record(tmp_path: Path, input_parameters: dict[str, Any]) -> Path:
    data = json.loads((TEST_DATA_DIR / "workflows" / "ndvi-workflow.json").read_text(encoding="utf-8"))
    data["links"] = [
        link for link in data["links"] if not (link.get("rel") == "application" and "cwl" in link.get("type", ""))
    ]
    data["links"].append({
        "rel": "application",
        "href": CWL_URL,
        "type": "application/cwl+yaml",
        "title": "CWL Application Package",
    })
    data["properties"]["inputParameters"] = input_parameters
    path = tmp_path / f"{data['id']}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _graph_inputs() -> dict[str, Any]:
    return {
        "stac_item": {
            "label": "STAC item",
            "type": "raster",
            "hubType": "stac-item",
            "cwlType": "Directory",
            "staging": "assets",
            "description": "STAC item",
        },
        "bbox": {
            "label": "Bounding box",
            "type": "bbox",
            "hubType": "bbox",
            "cwlType": "string",
            "required": False,
            "description": "xmin,ymin,xmax,ymax in EPSG:4326",
        },
        "dates": {
            "label": "Dates",
            "type": "date",
            "hubType": "date-range",
            "cwlType": "string[]",
            "description": "Start and end dates",
        },
    }


@pytest.mark.usefixtures("cwltool_passes")
def test_matching_record_passes(validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _serve_cwl(validate_ci, monkeypatch, "graph_workflow.cwl")
    record = _write_record(tmp_path, _graph_inputs())

    assert validate_ci.check_cwl_links([record]) == []


@pytest.mark.usefixtures("cwltool_passes")
def test_input_not_in_cwl_fails(validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _serve_cwl(validate_ci, monkeypatch, "graph_workflow.cwl")
    inputs = _graph_inputs()
    inputs["not_in_cwl"] = {"label": "Extra", "type": "text", "cwlType": "string", "description": "Not in the CWL"}
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) != []


@pytest.mark.usefixtures("cwltool_passes")
@pytest.mark.parametrize(
    ("name", "cwl_type"),
    [("stac_item", "string"), ("bbox", "Directory"), ("dates", "string")],
)
def test_cwl_type_mismatch_fails(
    validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str, cwl_type: str
) -> None:
    _serve_cwl(validate_ci, monkeypatch, "graph_workflow.cwl")
    inputs = _graph_inputs()
    inputs[name]["cwlType"] = cwl_type
    inputs[name].pop("staging", None)
    inputs[name].pop("hubType", None)
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) != []


@pytest.mark.usefixtures("cwltool_passes")
@pytest.mark.parametrize("bbox_overrides", [{}, {"required": True}], ids=["unset", "true"])
def test_optional_cwl_input_needs_required_false(
    validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, bbox_overrides: dict[str, Any]
) -> None:
    _serve_cwl(validate_ci, monkeypatch, "graph_workflow.cwl")
    inputs = _graph_inputs()
    del inputs["bbox"]["required"]
    inputs["bbox"].update(bbox_overrides)
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) != []


@pytest.mark.usefixtures("cwltool_passes")
def test_graph_tool_input_names_are_not_compared(
    validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _serve_cwl(validate_ci, monkeypatch, "graph_workflow.cwl")
    inputs = _graph_inputs()
    inputs["stac_item_dir"] = inputs.pop("stac_item")
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) != []


@pytest.mark.usefixtures("cwltool_passes")
def test_file_without_graph_uses_top_level_process(
    validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _serve_cwl(validate_ci, monkeypatch, "single_workflow.cwl")
    inputs = {
        "message": {"label": "Message", "type": "text", "cwlType": "string", "description": "Message"},
        "count": {"label": "Count", "type": "number", "cwlType": "int", "required": False, "description": "Count"},
    }
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) == []


@pytest.mark.usefixtures("cwltool_passes")
def test_file_without_graph_ignores_embedded_tool_inputs(
    validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _serve_cwl(validate_ci, monkeypatch, "single_workflow.cwl")
    inputs = {
        "text": {"label": "Text", "type": "text", "cwlType": "string", "description": "Tool input"},
    }
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) != []


@pytest.mark.usefixtures("cwltool_passes")
def test_fetch_error_only_warns(
    validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_get(url: str, **_: Any) -> FakeResponse:
        raise requests.ConnectionError(url)

    monkeypatch.setattr(validate_ci.requests, "get", fake_get)
    inputs = _graph_inputs()
    inputs["not_in_cwl"] = {"label": "Extra", "type": "text", "cwlType": "string", "description": "Not in the CWL"}
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) == []
    assert "WARN" in capsys.readouterr().out


@pytest.mark.usefixtures("cwltool_passes")
def test_fetch_bad_status_only_warns(
    validate_ci: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(validate_ci.requests, "get", lambda *_, **__: FakeResponse("Not found", status_code=404))
    inputs = _graph_inputs()
    inputs["not_in_cwl"] = {"label": "Extra", "type": "text", "cwlType": "string", "description": "Not in the CWL"}
    record = _write_record(tmp_path, inputs)

    assert validate_ci.check_cwl_links([record]) == []
    assert "WARN" in capsys.readouterr().out
