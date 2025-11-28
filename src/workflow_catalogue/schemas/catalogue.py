"""Catalogue schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import AnyUrl, BaseModel, Field

from workflow_catalogue.schemas.common import Link, Role  # noqa: TC001


class Concept(BaseModel):
    """Concept in a thematic classification."""

    id: str
    title: str


class Theme(BaseModel):
    """Thematic classification."""

    concepts: list[Concept]
    scheme: AnyUrl


class Contact(BaseModel):
    """Contact information for the catalog."""

    name: str = Field(..., description="Contact person or organization name")
    organization: str | None = Field(None, description="Organization name")
    roles: list[Role] = Field(..., description="Roles of the contact")
    links: list[Link] | None = None


class EodhCatalogue(BaseModel):
    """EODH catalogue schema."""

    id: str = Field(..., description="Unique identifier for the catalog", pattern=r"^[a-zA-Z0-9_-]+$")
    type: str = Field("Collection", frozen=True, description="OGC Records Collection type")
    item_type: str = Field(
        "record",
        alias="itemType",
        frozen=True,
        description="Type of items in this collection",
    )
    conforms_to: list[str] = Field(..., alias="conformsTo", description="OGC API conformance classes")
    title: str = Field(..., description="Human-readable catalog title", min_length=1)
    description: str = Field(..., description="Detailed description of the catalog", min_length=1)
    keywords: list[str] = Field(..., description="Keywords for discovery and categorization", min_length=1)
    themes: list[Theme] = Field(..., description="Thematic categorization")
    language: str = Field(..., description="Language code (ISO 639-1)", pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    created: datetime = Field(..., description="Creation timestamp in ISO 8601 format")
    updated: datetime = Field(..., description="Last update timestamp in ISO 8601 format")
    contacts: list[Contact] = Field(..., description="Contact information for the catalog", min_length=1)
    license: str = Field(..., description="License identifier (e.g., Apache-2.0, MIT, proprietary)")
    links: list[Link] = Field(..., description="Links to related resources")
