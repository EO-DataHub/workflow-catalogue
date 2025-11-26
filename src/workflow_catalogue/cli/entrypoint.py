"""CLI entrypoint."""

from __future__ import annotations

import click

from workflow_catalogue.cli.workflow.validate import validate_workflow_schema


@click.group()
def cli() -> None:
    """CLI entrypoint."""


@cli.group()
def workflow() -> None:
    """Workflow management commands."""


workflow.add_command(validate_workflow_schema)

if __name__ == "__main__":
    cli()
