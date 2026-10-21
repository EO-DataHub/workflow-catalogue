"""Workflow schemas."""

from __future__ import annotations

from workflow_catalogue.schemas.base_record import BaseEodhCatalogueRecord, Properties
from workflow_catalogue.schemas.workflow_extension import Properties as WorkflowProperties, WorkflowExtension


class EodhWorkflowProperties(Properties, WorkflowProperties):
    """Base record properties plus the workflow extension properties."""


class EodhWorkflowRecord(BaseEodhCatalogueRecord, WorkflowExtension):
    """EODH catalogue record for workflows."""

    # Without this, the base record's `properties` wins and the extension fields are never validated.
    properties: EodhWorkflowProperties
