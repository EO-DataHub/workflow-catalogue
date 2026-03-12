# Workflow and Notebook Inputs

This guide is for users **creating or editing workflow and notebook
records in the catalogue** so they work correctly with the EO Data Hub
user interface.

It explains:

-   how `inputParameters` are defined in catalogue records
-   how they are matched to **platform context variables**
-   how those values are passed to workflows or notebooks as the
    `variables` payload

---

# 1. Platform variables

Workflows and notebooks can access a shared set of **platform
variables**.
These variables are automatically derived from the launch context in the
EO Data Hub UI.

Common examples include:

### `STAC_ITEM_LINK`

-   **Value:** URL of the STAC Item `self` link.
-   **Use when:** the backend expects a direct URL to the STAC item.

---

### `STAC_COLLECTION_NAME`

-   **Value:** `item.collection` (the string ID of the item's
    collection).
-   **Use when:** the backend expects a collection identifier.

---

### `AOI`

-   **Value:** AOI geometry from the finder, serialized as a **GeoJSON
    string**.
-   **Only set when:**
    -   `includeAoi` is `true`, and
    -   an AOI is present in the launch context.
-   **Use when:** the backend expects an AOI geometry parameter.

---

### Important

If a parameter refers to a name that is **not a recognised platform
variable**, it will **not be automatically populated**.

Support for **manual parameter input in the UI** may be added in the
future.

---

# 2. How parameters are resolved

The EO Data Hub UI builds a `variables` payload when launching a
workflow or notebook.

Each parameter defined in `inputParameters` is checked to see if it can
be resolved from the launch context.

If a value can be resolved, it is included in the payload sent to the
backend.

The resolution process differs slightly for **notebooks** and
**workflows**.

---

# 3. Notebooks: matching by parameter key

For notebooks, the **parameter key itself must match the platform
variable name**.

## Resolution rules

When launching a notebook:

1.  The UI reads parameter keys from `properties.inputParameters` in the
    notebooks JSON file.
2.  For each key:
    -   The system looks for a resolver with the **same name as the
        key**.
    -   If a resolver exists, it is called using the launch context.
3.  If the resolver returns a value that is **not**:
    -   `null`
    -   `undefined`
    -   an empty string

    then the parameter is added to the `variables` payload.

---

### Example notebook configuration

``` json
"inputParameters": {
  "STAC_ITEM_LINK": {
    "label": "STAC item link"
  },
  "STAC_COLLECTION_NAME": {
    "label": "Collection ID"
  },
  "AOI": {
    "label": "Area of interest"
  }
}
```

### Notes

-   Parameter keys **must match platform variable names exactly**.
-   Fields such as `label` and `description` are **only used for
    display**.
-   Keys without a matching resolver are currently **ignored**.

---

# 4. Workflows: matching via `variableRef`

Workflow inputs support an additional mapping layer using `variableRef`.

This allows you to:

-   expose **backend-specific parameter names** in the workflow record
-   map those names to **platform variables** used by the UI

For example, your backend might expect parameters like:

-   `input_uri`
-   `collection`
-   `aoi_geojson`

These can be mapped to platform variables.

---

### Example workflow configuration

``` json
"inputParameters": {
  "input_uri": {
    "label": "Input STAC item",
    "variableRef": "STAC_ITEM_LINK"
  },
  "collection": {
    "label": "Collection ID",
    "variableRef": "STAC_COLLECTION_NAME"
  },
  "aoi_geojson": {
    "label": "AOI (GeoJSON)",
    "variableRef": "AOI"
  }
}
```

In this example:

  Workflow parameter   Platform variable
  -------------------- ------------------------
  `input_uri`          `STAC_ITEM_LINK`
  `collection`         `STAC_COLLECTION_NAME`
  `aoi_geojson`        `AOI`

The backend receives parameters using the **workflow key names**, while
values are derived from **platform variables**.
