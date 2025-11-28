"""Base record schema."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from enum import Enum

from geojson_pydantic.geometries import Geometry  # noqa: TC002
from pydantic import AnyUrl, BaseModel, Field

from workflow_catalogue.schemas.common import Link, Role  # noqa: TC001


class Type(Enum):
    """Type of catalogue record."""

    workflow = "workflow"
    notebook = "notebook"


class Contact(BaseModel):
    """Contact information for the workflow/notebook authors."""

    name: str = Field(..., description="Contact person or organization name")
    organization: str | None = Field(None, description="Organization name")
    roles: list[Role] = Field(..., description="Roles of the contact")
    links: list[Link] | None = None


class Properties(BaseModel):
    """Additional properties of the workflow/notebook."""

    created: datetime = Field(..., description="Creation timestamp in ISO 8601 format")
    updated: datetime = Field(..., description="Last update timestamp in ISO 8601 format")
    type: Type = Field(..., description="Type of catalogue record")
    title: str = Field(..., description="Human-readable title", min_length=1)
    description: str = Field(..., description="Detailed description of the workflow or notebook")
    keywords: list[str] = Field(..., description="Keywords for discovery and categorization", min_length=1)
    language: str = Field(pattern=r"^[a-z]{2}(-[A-Z]{2})?$", description="Language code (ISO 639-1)")
    license: str | None = Field(None, description="License identifier (e.g., Apache-2.0, MIT, proprietary)")
    applicable_collections: list[AnyUrl] = Field(
        ...,
        alias="applicableCollections",
        description="Array of STAC collection URLs that this workflow/notebook can process",
    )
    contacts: list[Contact] | None = Field(
        default_factory=list,
        description="Contact information for the workflow/notebook",
        min_length=0,
    )


class BaseEodhCatalogueRecord(BaseModel):
    """Base model for EODH catalogue records."""

    id: str = Field(..., description="Unique identifier for the record", pattern=r"^[a-zA-Z0-9_-]+$")
    type: str = Field("Feature", frozen=True, description="OGC Records Feature type")
    geometry: Geometry | None = Field(
        ...,
        description="Spatial geometry - typically null for workflow/notebook definitions",
    )
    conforms_to: list[str] = Field(..., alias="conformsTo", description="OGC API conformance classes")
    properties: Properties
    links: list[Link] | None = Field(None, description="Links to related resources")
