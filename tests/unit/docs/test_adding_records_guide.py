"""Tests for the adding-records guide."""

from __future__ import annotations

import pytest

from workflow_catalogue.consts import directories

GUIDE_PATH = directories.ROOT_DIR / "docs" / "guides" / "adding-records.md"


@pytest.mark.parametrize("field", ["hubType", "cwlType", "staging"])
def test_guide_describes_input_field(field: str) -> None:
    assert f"`{field}`" in GUIDE_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "hub_type",
    ["stac-item", "stac-items", "stac-search", "pin-set", "aoi", "bbox", "date", "date-range"],
)
def test_guide_has_example_for_hub_type(hub_type: str) -> None:
    assert f'"hubType": "{hub_type}"' in GUIDE_PATH.read_text(encoding="utf-8")
