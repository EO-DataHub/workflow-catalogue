"""Tests for publishing workflows in scripts/register.py."""

from __future__ import annotations

import importlib.util
import json
from typing import TYPE_CHECKING, Any

import pytest

from workflow_catalogue.consts import directories

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType

SCRIPT_PATH = directories.ROOT_DIR / "scripts" / "register.py"


class FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "") -> None:
        self.status_code = status_code
        self.text = text
        self.ok = status_code < 400  # noqa: PLR2004


@pytest.fixture
def register() -> ModuleType:
    spec = importlib.util.spec_from_file_location("register", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_record(path: Path, record_id: str, record_type: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"id": record_id, "properties": {"type": record_type}}), encoding="utf-8")


def test_collect_workflow_ids_lists_every_workflow_sorted(register: ModuleType, tmp_path: Path) -> None:
    _write_record(tmp_path / "col-a" / "workflows" / "ndwi.json", "ndwi-workflow", "workflow")
    _write_record(tmp_path / "col-a" / "workflows" / "clip.json", "clip-workflow", "workflow")
    _write_record(tmp_path / "col-b" / "workflows" / "ndvi.json", "ndvi-workflow", "workflow")
    _write_record(tmp_path / "col-a" / "notebooks" / "nb.json", "some-notebook", "notebook")

    assert register.collect_workflow_ids(tmp_path) == ["clip-workflow", "ndvi-workflow", "ndwi-workflow"]


def test_collect_workflow_ids_reads_the_real_catalogue(register: ModuleType) -> None:
    ids = register.collect_workflow_ids()

    assert "ndvi-workflow" in ids
    assert ids == sorted(ids)


def test_build_access_policy_makes_every_workflow_public(register: ModuleType) -> None:
    assert register.build_access_policy(["a", "b"]) == {
        "workflows": {"a": {"access": "public"}, "b": {"access": "public"}},
    }


def test_publish_workflows_uploads_one_policy_then_harvests_once(
    register: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EODH__BASE_URL", "https://hub.example/")
    monkeypatch.setenv("EODH__WORKSPACE_NAME", "pubws")
    calls: list[tuple[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        calls.append((url, kwargs.get("json")))
        return FakeResponse()

    monkeypatch.setattr(register.requests, "post", fake_post)

    assert register.publish_workflows(["clip-workflow", "ndvi-workflow"], "token") is True

    assert [url for url, _ in calls] == [
        "https://hub.example/api/workspaces/pubws/data-loader",
        "https://hub.example/workspaces/pubws/harvest",
    ]
    upload = calls[0][1]
    assert upload["fileName"] == "access-policy.json"
    assert json.loads(upload["fileContent"]) == {
        "workflows": {"clip-workflow": {"access": "public"}, "ndvi-workflow": {"access": "public"}},
    }


def test_publish_workflows_does_not_harvest_when_upload_fails(
    register: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EODH__BASE_URL", "https://hub.example")
    monkeypatch.setenv("EODH__WORKSPACE_NAME", "pubws")
    urls: list[str] = []

    def fake_post(url: str, **_: Any) -> FakeResponse:
        urls.append(url)
        return FakeResponse(status_code=500, text="boom")

    monkeypatch.setattr(register.requests, "post", fake_post)

    assert register.publish_workflows(["clip-workflow"], "token") is False
    assert urls == ["https://hub.example/api/workspaces/pubws/data-loader"]
