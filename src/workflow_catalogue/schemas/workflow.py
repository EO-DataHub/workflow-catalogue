"""Workflow schemas."""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from workflow_catalogue.schemas.base_record import BaseEodhCatalogueRecord, Properties
from workflow_catalogue.schemas.workflow_extension import Properties as WorkflowProperties, WorkflowExtension


class EodhWorkflowProperties(Properties, WorkflowProperties):
    """Base record properties plus the workflow extension properties."""


class EodhWorkflowRecord(BaseEodhCatalogueRecord, WorkflowExtension):
    """EODH catalogue record for workflows."""

    # Without this, the base record's `properties` wins and the extension fields are never validated.
    properties: EodhWorkflowProperties

    @model_validator(mode="after")
    def check_inputs_have_cwl_type(self) -> Self:
        """Check that every input says which CWL type the workflow receives."""
        missing = [name for name, param in (self.properties.input_parameters or {}).items() if param.cwl_type is None]
        if missing:
            msg = f"workflow inputs need a cwlType: {', '.join(missing)}"
            raise ValueError(msg)
        return self
