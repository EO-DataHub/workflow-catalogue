"""Workflow extension schema."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from workflow_catalogue.schemas.common import InputParameter, Link  # noqa: TC001


class Spatial(BaseModel):
    """Spatial extent of the workflow."""

    bbox: list[list[float]] | None = Field(None, description="Bounding box coordinates [minX, minY, maxX, maxY]")
    crs: str | None = Field(None, description="Coordinate reference system")


class Temporal(BaseModel):
    """Temporal extent of the workflow."""

    interval: list[list[str | None]] | None = Field(None, description="Temporal intervals [start, end]")
    trs: str | None = Field(None, description="Temporal reference system")


class Extent(BaseModel):
    """Spatial and temporal extent of the workflow."""

    spatial: Spatial | None = None
    temporal: Temporal | None = None


class Properties(BaseModel):
    """Additional properties of the workflow."""

    type: str = Field("workflow", frozen=True)
    input_parameters: dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]+$")], InputParameter] | None = Field(
        None,
        alias="inputParameters",
        description="Input parameters for the workflow",
    )
    application_type: str = Field(
        "cwl",
        alias="application:type",
        frozen=True,
        description="Application type identifier",
    )
    application_container: bool | None = Field(
        None,
        alias="application:container",
        description="Whether the workflow runs in a container",
    )
    application_language: str = Field(
        "CWL",
        alias="application:language",
        frozen=True,
        description="Workflow definition language",
    )
    extent: Extent | None = Field(None, description="Spatial and temporal extent of the workflow")


class WorkflowExtension(BaseModel):
    """Workflow extension schema."""

    properties: Properties
    links: list[Link] | None = Field(
        None,
        description="Must contain application-platform link for ADES execution endpoint",
    )
