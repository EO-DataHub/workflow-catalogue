# Adding records to the catalogue

This guide explains how to add a new workflow or notebook record to the catalogue.

## Directory structure

Records are organised by collection. Each collection has its own directory under `catalogue/`:

```
catalogue/
└── eodh-workflows-notebooks/    # collection ID
    ├── catalog.json              # collection metadata
    ├── workflows/                # workflow records
    │   └── my-workflow.json
    └── notebooks/                # notebook records
        └── my_notebook.json
```

To add a new collection, create a new directory under `catalogue/` with a `catalog.json` describing the collection. The directory name becomes the collection ID. On merge, the CD pipeline will automatically create the collection in the API if it does not exist yet.

## Step by step

1. **Copy a template** from the appropriate directory:
    - Workflow: `catalogue/eodh-workflows-notebooks/workflows/ndvi-workflow.json`
    - Notebook: `catalogue/eodh-workflows-notebooks/notebooks/ndvi_calculation.json`

2. **Rename the file** to match the record ID. The filename stem must equal the `id` field:
    - `my-workflow.json` → `"id": "my-workflow"`
    - `my_notebook.json` → `"id": "my_notebook"`

3. **Fill in the fields** (see sections below).

4. **Validate locally**:

    ```shell
    make validate-catalogue
    ```

5. **Open a PR** targeting `main`. CI runs schema validation, STAC URL checks, and CWL syntax validation automatically.

6. **After merge**, CD registers the record in the API and publishes it.

## Workflow record fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier, must match filename |
| `type` | Yes | Always `"Feature"` |
| `geometry` | Yes | GeoJSON geometry or `null` for global |
| `conformsTo` | Yes | `["http://www.opengis.net/doc/IS/ogcapi-records-1/1.0"]` |
| `properties.type` | Yes | `"workflow"` |
| `properties.title` | Yes | Human-readable title |
| `properties.description` | Yes | What the workflow does |
| `properties.keywords` | Yes | List of searchable keywords |
| `properties.language` | Yes | Language code, e.g. `"en"` |
| `properties.license` | Yes | SPDX license identifier, e.g. `"Apache-2.0"` |
| `properties.created` | Yes | ISO 8601 datetime |
| `properties.updated` | Yes | ISO 8601 datetime |
| `properties.applicableCollections` | Yes | List of STAC collection URLs this workflow operates on |
| `properties.contacts` | Yes | At least one contact with name, organization, and roles |
| `properties.inputParameters` | Yes | Map of parameter name to `{label, type, description}` |
| `properties.application:type` | Yes | `"cwl"` |
| `properties.application:container` | Yes | `true` |
| `properties.application:language` | Yes | `"CWL"` |
| `properties.extent` | No | Spatial and temporal extent |

## Notebook record fields

Notebooks share most fields with workflows, with these differences:

| Field | Value |
|-------|-------|
| `properties.type` | `"notebook"` |
| `properties.application:type` | `"jupyter-notebook"` |
| `properties.application:container` | `false` |
| `properties.application:language` | `"Python"` |
| `properties.jupyter_kernel_info` | Kernel name, Python version, environment file URL |
| `properties.formats` | `[{"name": "Jupyter Notebook", "mediaType": "application/x-ipynb+json"}]` |

Notebooks do not require `license`.

## Links

Every record should include the following links:

| `rel` | Purpose |
|--------|---------|
| `root` | `"../catalog.json"` — points to the root catalogue |
| `parent` | `"../catalog.json"` — points to the parent catalogue |
| `self` | Canonical URL for this record |
| `application` | URL to the CWL file (workflows) or Jupyter notebook (notebooks) |
| `application-platform` | ADES or JupyterHub endpoint for execution |
| `vcs` | Source code repository |

## Finding STAC collection URLs

Browse the EODH catalogue to find the STAC collection URLs for `applicableCollections`:

```
https://eodatahub.org.uk/api/catalogue/stac/catalogs/public/catalogs/ceda-stac-catalogue/collections
```

Each collection URL should be the full path, e.g.:

```
https://eodatahub.org.uk/api/catalogue/stac/catalogs/public/catalogs/ceda-stac-catalogue/collections/sentinel2_ard
```

## Input parameters

The `inputParameters` field maps parameter names to objects with:

| Field | Required | Description |
|-------|----------|-------------|
| `label` | Yes | Display label for the parameter |
| `type` | Yes | Parameter type: `"text"`, `"date"`, `"bbox"`, `"raster"`, `"number"` |
| `description` | Yes | What the parameter is for |
| `default` | No | Default value |
| `placeholder` | No | Placeholder text for UI input fields |
