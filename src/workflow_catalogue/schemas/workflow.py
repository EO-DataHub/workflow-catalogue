"""Workflow schemas."""

from __future__ import annotations

from workflow_catalogue.schemas.base_record import BaseEodhCatalogueRecord
from workflow_catalogue.schemas.workflow_extension import WorkflowExtension


class EodhWorkflowRecord(BaseEodhCatalogueRecord, WorkflowExtension):
    """EODH catalogue record for workflows."""
