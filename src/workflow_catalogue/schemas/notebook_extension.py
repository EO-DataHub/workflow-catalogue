"""Notebook extension schema."""

from __future__ import annotations

from pydantic import AnyUrl, BaseModel, Field, constr

from workflow_catalogue.schemas.common import InputParameter, Link, OutputFormat, Rel


class JupyterKernelInfo(BaseModel):
    """Jupyter kernel configuration."""

    name: str = Field(..., description="Jupyter kernel name (e.g., python3)")
    python_version: float = Field(..., description="Python version number (e.g., 3.11)")
    env_file: AnyUrl | None = Field(None, description="URL to environment configuration file")


class NotebookProperties(BaseModel):
    """Additional properties of the notebook."""

    type: str = Field("notebook", frozen=True)
    input_parameters: dict[constr(regex=r"^[a-zA-Z0-9_-]+$"), InputParameter] | None = Field(
        None,
        alias="inputParameters",
        description="Input parameters for the notebook",
    )
    jupyter_kernel_info: JupyterKernelInfo | None = Field(None, description="Jupyter kernel configuration")
    application_type: str = Field(
        "jupyter-notebook",
        alias="application:type",
        frozen=True,
        description="Application type identifier",
    )
    application_container: bool | None = Field(
        None,
        alias="application:container",
        description="Whether the notebook runs in a container",
    )
    application_language: str | None = Field(
        None,
        alias="application:language",
        description="Primary programming language (e.g., Python)",
    )
    formats: list[OutputFormat] | None = Field(None, description="Supported output formats")


class JupyterKernel(BaseModel):
    """Jupyter kernel configuration."""

    name: str | None = None
    python_version: float | None = Field(None, alias="pythonVersion")
    env_file: AnyUrl | None = Field(None, alias="envFile")


class NotebookLink(Link):
    """Link to a related resource."""

    rel: Rel | None = None
    jupyter_kernel: JupyterKernel | None = Field(None, alias="jupyter:kernel")


class NotebookExtension(BaseModel):
    """Notebook extension schema."""

    properties: NotebookProperties
    links: list[NotebookLink] | None = Field(
        None,
        description="Must contain application-platform link for Jupyter Hub execution endpoint",
    )
