"""Common schemas."""

from __future__ import annotations

from enum import Enum
from pathlib import Path  # noqa: TC003
from typing import Any

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


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
    pin_set = "pin-set"
    stac_search = "stac-search"
    aoi = "aoi"
    bbox = "bbox"
    date = "date"
    date_range = "date-range"


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
