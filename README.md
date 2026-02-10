# workflow-catalogue

A catalogue with shared EODH-related workflow definitions and the CI/CD pipelines that validate, register, and publish them.

## Getting started

Create the environment:

```shell
make env
```

Run `pre-commit` hooks:

```shell
make pc
```

Validate all catalogue records:

```shell
make validate-catalogue
```

## Adding a workflow or notebook

1. Create a feature branch from `main`
2. Copy an existing record as a template:
   - Workflows: `catalogue/workflows/ndvi-workflow.json`
   - Notebooks: `catalogue/notebooks/ndvi_calculation.json`
3. Save your new file in the appropriate directory. The filename must match the `id` field (e.g. `my-workflow.json` with `"id": "my-workflow"`)
4. Set `properties.type` to `"workflow"` or `"notebook"`
5. Validate locally: `make validate-catalogue`
6. Push and open a PR targeting `main` — CI validates automatically
7. After review and merge, CD registers the record in the API

See the [full guide](docs/guides/adding-records.md) for field descriptions and examples.

## Dev LOG

See the [log](docs/dev-logs) of changes and experiment results. Best to view it via `mkdocs serve` command.

## Guides

Read more here:

- [Development env setup](docs/guides/setup-dev-env.md)
- [Contributing](docs/guides/contributing.md)
- [Adding records](docs/guides/adding-records.md)
- [QA testing](docs/guides/qa-testing.md)
- [Makefile usage](docs/guides/makefile-usage.md)
- [Running tests](docs/guides/tests.md)

## Docs

To build project documentation run:

```shell
make docs
```

and then:

```shell
mkdocs serve
```
