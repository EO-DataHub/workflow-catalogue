"""Notebook schemas."""

from __future__ import annotations

from workflow_catalogue.schemas.base_record import BaseEodhCatalogueRecord, Properties
from workflow_catalogue.schemas.notebook_extension import NotebookExtension, NotebookProperties


class EodhNotebookProperties(Properties, NotebookProperties):
    """Base record properties plus the notebook extension properties."""


class EodhNotebookRecord(BaseEodhCatalogueRecord, NotebookExtension):
    """EODH catalogue record for notebooks."""

    # Without this, the base record's `properties` wins and the extension fields are never validated.
    properties: EodhNotebookProperties
