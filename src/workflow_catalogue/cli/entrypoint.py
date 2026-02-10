"""CLI entrypoint."""

from __future__ import annotations

import click

from workflow_catalogue.cli.catalogue.validate import validate_catalogue
from workflow_catalogue.cli.workflow.validate import validate_workflow_schema


@click.group()
def cli() -> None:
    """CLI entrypoint."""


@cli.group()
def workflow() -> None:
    """Workflow management commands."""


@cli.group()
def catalogue() -> None:
    """Catalogue management commands."""


workflow.add_command(validate_workflow_schema)
catalogue.add_command(validate_catalogue)

if __name__ == "__main__":
    cli()
