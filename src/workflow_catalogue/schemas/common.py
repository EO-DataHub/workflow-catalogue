"""Common schemas."""

from __future__ import annotations

from enum import Enum
from pathlib import Path  # noqa: TC003
from typing import Any, Self

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, model_validator


class Rel(Enum):
    """Link relation types."""

    root = "root"
    parent = "parent"
    self = "self"
    alternate = "alternate"
    application = "application"
    application_platform = "application-platform"
    vcs = "vcs"
    documentation = "documentation"
    about = "about"
    item = "item"
    asset = "asset"
    data = "data"


class Link(BaseModel):
    """Link to a related resource."""

    href: AnyUrl | Path
    rel: Rel
    type: str | None = None
    title: str | None = None


class ParameterType(Enum):
    """Parameter data types."""

    raster = "raster"
    vector = "vector"
    collection = "collection"
    catalog = "catalog"
    netcdf = "netcdf"
    geotiff = "geotiff"
    wms = "wms"
    wfs = "wfs"
    bbox = "bbox"
    date = "date"
    text = "text"
    number = "number"
    boolean = "boolean"


class HubType(Enum):
    """What the Hub fills an input with at launch."""

    stac_item = "stac-item"
    stac_items = "stac-items"
    pin_set = "pin-set"
    stac_search = "stac-search"
    aoi = "aoi"
    bbox = "bbox"
    date = "date"
    date_range = "date-range"


class Staging(Enum):
    """How much of a STAC item stage-in fetches for a Directory input."""

    assets = "assets"
    metadata = "metadata"


# An empty set means the hub type cannot be used with any cwlType, so only notebooks can use it.
ALLOWED_CWL_TYPES: dict[HubType, set[str]] = {
    HubType.stac_item: {"Directory", "string"},
    HubType.stac_items: {"Directory", "string[]"},
    HubType.stac_search: {"string"},
    HubType.aoi: {"string"},
    HubType.bbox: {"string"},
    HubType.date: {"string"},
    HubType.date_range: {"string[]"},
    HubType.pin_set: set(),
}


class InputParameter(BaseModel):
    """Input parameter definition."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., description="Human-readable parameter label", min_length=1)
    type: ParameterType = Field(..., description="Parameter data type")
    description: str = Field(..., description="Parameter description", min_length=1)
    default: Any | None = Field(None, description="Default value for the parameter")
    placeholder: str | None = Field(None, description="Placeholder text for UI forms")
    required: bool | None = Field(None, description="Whether the parameter is required")
    min: float | None = Field(None, description="Minimum value for numeric parameters")
    max: float | None = Field(None, description="Maximum value for numeric parameters")
    pattern: str | None = Field(None, description="Regex pattern for text parameters")
    enum: list[str | int | float] | None = Field(None, description="Allowed values for the parameter")
    hub_type: HubType | None = Field(
        None,
        alias="hubType",
        description="What the Hub fills this input with at launch. Unset means the user enters the value",
    )
    variable_ref: str | None = Field(
        None,
        alias="variableRef",
        description="Deprecated: platform variable name used before hubType. Kept until clients read hubType",
    )
    cwl_type: str | None = Field(
        None,
        alias="cwlType",
        description="CWL type of the workflow input, without the optional marker (e.g. Directory, string, string[])",
    )
    staging: Staging | None = Field(
        None,
        description="How much stage-in fetches for a Directory input: the item with its assets, or the metadata only",
    )

    @model_validator(mode="after")  # type: ignore[misc]  # mypy runs without pydantic installed
    def check_cwl_type(self) -> Self:
        """Check that staging and hubType fit cwlType."""
        if self.staging is not None and self.cwl_type is not None and self.cwl_type != "Directory":
            msg = f"staging needs cwlType 'Directory', got {self.cwl_type!r}"
            raise ValueError(msg)
        if self.hub_type is None or self.cwl_type is None:
            return self
        if self.hub_type == HubType.stac_search and self.cwl_type == "Directory":
            msg = "hubType 'stac-search' cannot have cwlType 'Directory'. Use hubType 'stac-items' to stage the results"
            raise ValueError(msg)
        allowed = ALLOWED_CWL_TYPES[self.hub_type]
        if self.cwl_type not in allowed:
            if not allowed:
                msg = f"hubType {self.hub_type.value!r} is for notebooks only and cannot have a cwlType"
            else:
                msg = f"hubType {self.hub_type.value!r} needs cwlType in {sorted(allowed)}, got {self.cwl_type!r}"
            raise ValueError(msg)
        return self


class OutputFormat(BaseModel):
    """Supported output format."""

    name: str = Field(..., description="Format name")
    media_type: str = Field(..., alias="mediaType", description="MIME type for the format")


class Role(Enum):
    """Roles of the contact."""

    author = "author"
    publisher = "publisher"
    point_of_contact = "pointOfContact"
    principal_investigator = "principalInvestigator"
    processor = "processor"
    custodian = "custodian"
    distributor = "distributor"
    originator = "originator"
    resource_provider = "resourceProvider"
