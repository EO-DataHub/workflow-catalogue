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

5. **Open a PR** targeting `main`. CI runs schema validation, STAC URL checks, CWL syntax validation and a check of `inputParameters` against the CWL inputs.

6. **After merge**, CD registers the record in the API and publishes it.

## Workflow record fields

| Field                              | Required | Description                                              |
| ---------------------------------- | -------- | -------------------------------------------------------- |
| `id`                               | Yes      | Unique identifier, must match filename                   |
| `type`                             | Yes      | Always `"Feature"`                                       |
| `geometry`                         | Yes      | GeoJSON geometry or `null` for global                    |
| `conformsTo`                       | Yes      | `["http://www.opengis.net/doc/IS/ogcapi-records-1/1.0"]` |
| `properties.type`                  | Yes      | `"workflow"`                                             |
| `properties.title`                 | Yes      | Human-readable title                                     |
| `properties.description`           | Yes      | What the workflow does                                   |
| `properties.keywords`              | Yes      | List of searchable keywords                              |
| `properties.language`              | Yes      | Language code, e.g. `"en"`                               |
| `properties.license`               | Yes      | SPDX license identifier, e.g. `"Apache-2.0"`             |
| `properties.created`               | Yes      | ISO 8601 datetime                                        |
| `properties.updated`               | Yes      | ISO 8601 datetime                                        |
| `properties.applicableCollections` | Yes      | List of STAC collection URLs this workflow operates on   |
| `properties.contacts`              | Yes      | At least one contact with name, organization, and roles  |
| `properties.inputParameters`       | Yes      | Map of parameter name to an input object. See below      |
| `properties.application:type`      | Yes      | `"cwl"`                                                  |
| `properties.application:container` | Yes      | `true`                                                   |
| `properties.application:language`  | Yes      | `"CWL"`                                                  |
| `properties.extent`                | No       | Spatial and temporal extent                              |

## Notebook record fields

Notebooks share most fields with workflows, with these differences:

| Field                              | Value                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------- |
| `properties.type`                  | `"notebook"`                                                              |
| `properties.application:type`      | `"jupyter-notebook"`                                                      |
| `properties.application:container` | `false`                                                                   |
| `properties.application:language`  | `"Python"`                                                                |
| `properties.jupyter_kernel_info`   | Kernel name, Python version, environment file URL                         |
| `properties.formats`               | `[{"name": "Jupyter Notebook", "mediaType": "application/x-ipynb+json"}]` |

Notebooks do not require `license`.

## Links

Every record should include the following links:

| `rel`                  | Purpose                                                         |
| ---------------------- | --------------------------------------------------------------- |
| `root`                 | `"../catalog.json"` — points to the root catalogue              |
| `parent`               | `"../catalog.json"` — points to the parent catalogue            |
| `self`                 | Canonical URL for this record                                   |
| `application`          | URL to the CWL file (workflows) or Jupyter notebook (notebooks) |
| `application-platform` | ADES or JupyterHub endpoint for execution                       |
| `vcs`                  | Source code repository                                          |

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

| Field         | Required       | Description                                                                           |
| ------------- | -------------- | ------------------------------------------------------------------------------------- |
| `label`       | Yes            | Display label for the parameter                                                       |
| `type`        | Yes            | Parameter type: `"text"`, `"date"`, `"bbox"`, `"raster"`, `"number"`                  |
| `description` | Yes            | What the parameter is for                                                             |
| `default`     | No             | Default value                                                                         |
| `placeholder` | No             | Placeholder text for UI input fields                                                  |
| `required`    | No             | Set to `false` if the user can leave the input empty                                  |
| `hubType`     | No             | What the Hub fills the input with at launch. Leave it out if the user types the value |
| `cwlType`     | Workflows only | The CWL type of the workflow input, without the optional marker `?`                   |
| `staging`     | No             | How much stage-in fetches for a `Directory` input: `"assets"` or `"metadata"`         |
| `variableRef` | No             | Deprecated. The old platform variable name. Use `hubType` for new records             |

Each input object accepts only the fields in this table. A record with any other field fails validation.

### Set `hubType`

`hubType` tells the Hub what to put in the input when a user runs the workflow or opens the notebook. rc-ui still reads `variableRef` until it moves to `hubType`, so keep `variableRef` on inputs that already have it.

| `hubType`     | What the Hub sends                                    | Allowed `cwlType`         |
| ------------- | ----------------------------------------------------- | ------------------------- |
| `stac-item`   | One STAC item                                         | `Directory` or `string`   |
| `stac-items`  | A list of STAC items                                  | `Directory` or `string[]` |
| `stac-search` | A STAC search, as a string                            | `string`                  |
| `pin-set`     | The ID of a saved set. Notebooks only                 | None                      |
| `aoi`         | An area of interest, as a GeoJSON string              | `string`                  |
| `bbox`        | A bounding box, as `xmin,ymin,xmax,ymax` in EPSG:4326 | `string`                  |
| `date`        | One date                                              | `string`                  |
| `date-range`  | A start date and an end date                          | `string[]`                |

If the `hubType` and `cwlType` do not fit this table, the record fails validation. A `stac-search` input cannot be a `Directory`. To stage the results of a search, use `stac-items`.

### Set `cwlType`

Every input in a workflow record needs a `cwlType`. Copy the type from the input of the `Workflow` process in the CWL file, and remove the `?` from the end. For example, the CWL type `string?` becomes `"cwlType": "string"`. If the CWL file has a `$graph`, use the inputs of the `Workflow`, not the inputs of a `CommandLineTool`.

Notebook inputs must not have `cwlType` or `staging`.

If an input is optional in the CWL (its type ends with `?`), set `"required": false` on the input. If you leave `required` out, CI fails the record.

CI fetches the CWL file and compares it with `inputParameters`. The record fails if:

- an `inputParameters` key is not an input of the CWL `Workflow`
- a `cwlType` is not the same as the CWL input type, after the `?` is removed
- an input is optional in the CWL and `required` is not `false`

`make validate-catalogue` does not do this check. To run it locally, use:

```shell
uv run python scripts/validate_ci.py --files catalogue/eodh-workflows-notebooks/workflows/my-workflow.json
```

### Set `staging`

`staging` applies only to a `Directory` input. It tells stage-in how much of each STAC item to fetch:

- `"assets"`: the item and its asset files. Use this if the workflow reads the data.
- `"metadata"`: the item JSON only. Use this if the workflow reads only the item properties or asset links.

If you set `staging` and `cwlType` is not `Directory`, the record fails validation.

### Examples

A single STAC item, staged with its assets (workflow, CWL type `Directory`):

```json
"stac_item": {
    "label": "STAC Item",
    "type": "raster",
    "description": "STAC item to calculate NDVI from",
    "hubType": "stac-item",
    "cwlType": "Directory",
    "staging": "assets"
}
```

A list of STAC items, staged as metadata only (workflow, CWL type `Directory`):

```json
"stac_items": {
    "label": "STAC Items",
    "type": "raster",
    "description": "STAC items to build the mosaic from",
    "hubType": "stac-items",
    "cwlType": "Directory",
    "staging": "metadata"
}
```

A STAC search that the workflow runs itself (workflow, CWL type `string`):

```json
"search": {
    "label": "STAC Search",
    "type": "text",
    "description": "STAC search request, as a JSON string",
    "hubType": "stac-search",
    "cwlType": "string"
}
```

A saved set (notebook, so no `cwlType`):

```json
"PIN_SET_ID": {
    "label": "Pin Set ID",
    "type": "text",
    "description": "ID of the saved set to load",
    "hubType": "pin-set"
}
```

An area of interest (notebook, so no `cwlType`):

```json
"AOI": {
    "label": "AOI",
    "type": "text",
    "description": "AOI in GeoJSON format",
    "hubType": "aoi"
}
```

An optional bounding box (workflow, CWL type `string?`):

```json
"bbox": {
    "label": "Bounding Box",
    "type": "bbox",
    "description": "Area to clip to, as xmin,ymin,xmax,ymax in EPSG:4326",
    "hubType": "bbox",
    "cwlType": "string",
    "required": false
}
```

A single date (workflow, CWL type `string`):

```json
"date": {
    "label": "Date",
    "type": "date",
    "description": "Date to process, as YYYY-MM-DD",
    "hubType": "date",
    "cwlType": "string"
}
```

A date range (workflow, CWL type `string[]`):

```json
"date_range": {
    "label": "Date Range",
    "type": "date",
    "description": "Start and end dates, as YYYY-MM-DD",
    "hubType": "date-range",
    "cwlType": "string[]"
}
```
