"""Notebook schemas."""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from workflow_catalogue.schemas.base_record import BaseEodhCatalogueRecord, Properties
from workflow_catalogue.schemas.notebook_extension import NotebookExtension, NotebookProperties


class EodhNotebookProperties(Properties, NotebookProperties):  # type: ignore[misc]  # both define `type`; the MRO keeps the base record's
    """Base record properties plus the notebook extension properties."""


class EodhNotebookRecord(BaseEodhCatalogueRecord, NotebookExtension):
    """EODH catalogue record for notebooks."""

    # Without this, the base record's `properties` wins and the extension fields are never validated.
    properties: EodhNotebookProperties

    @model_validator(mode="after")  # type: ignore[misc]  # mypy runs without pydantic installed
    def check_inputs_have_no_cwl_fields(self) -> Self:
        """Check that no input has cwlType or staging, which only apply to workflows."""
        for name, param in (self.properties.input_parameters or {}).items():
            if param.cwl_type is not None:
                msg = f"notebook input {name!r} cannot have a cwlType"
                raise ValueError(msg)
            if param.staging is not None:
                msg = f"notebook input {name!r} cannot have staging"
                raise ValueError(msg)
        return self
