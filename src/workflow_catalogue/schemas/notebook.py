"""Notebook schemas."""

from __future__ import annotations

from workflow_catalogue.schemas.base_record import BaseEodhCatalogueRecord
from workflow_catalogue.schemas.notebook_extension import NotebookExtension


class EodhNotebookRecord(BaseEodhCatalogueRecord, NotebookExtension):
    """EODH catalogue record for notebooks."""
