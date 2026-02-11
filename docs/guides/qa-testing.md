# QA testing guide

This guide covers end-to-end testing of the catalogue CI/CD pipeline and API verification.

Replace `{API_URL}` with the actual wf-catalogue-service URL for your environment.

All API endpoints require a Bearer token. Set it once:

```shell
TOKEN="your-access-token"
```

## 1. CI validation (pull request)

When a PR is opened that changes files under `catalogue/`, the **Validate Catalogue** workflow runs automatically.

**What it checks:**

- JSON schema validation against Pydantic models (all records in `catalogue/`)
- STAC collection URL reachability (changed files only)
- CWL syntax validation via `cwltool` (changed files only)

**How to verify:**

1. Go to the PR on GitHub
2. Scroll to the checks section at the bottom
3. Click "Validate Catalogue" to see the workflow run
4. All steps should show green checkmarks

**Expected failures:**

- Missing required fields in JSON → schema validation fails
- Invalid STAC collection URL → STAC URL check fails
- Malformed CWL file → CWL validation fails
- Filename does not match `id` field → schema validation fails

## 2. CD registration (merge to main)

When a PR is merged, the **Register Catalogue** workflow runs automatically.

**What it does:**

1. Detects which catalogue files were added, modified, or deleted
2. Registers new/updated records in wf-catalogue-service via `POST /api/v1.0/register`
3. Registers CWL processes in ADES (workflows only)
4. Publishes workflows with access policy and triggers harvest
5. Deletes removed records via `DELETE /api/v1.0/register/{record_id}`

**How to verify:**

1. Go to the repository's Actions tab on GitHub
2. Find the "Register Catalogue" workflow run triggered by the merge commit
3. Check that all steps completed successfully
4. Verify records in the API (see section 3)

## 3. API verification

### Health check

```shell
curl {API_URL}/health
```

Expected: `200 OK` with `{"status": "ok"}`

### List catalogues

```shell
curl -H "Authorization: Bearer $TOKEN" {API_URL}/api/v1.0/collections
```

Expected: `200 OK` with a list containing the `eodh-workflows-notebooks` catalogue.

### Create a new collection

```shell
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"id": "my-collection", "title": "My Collection", "description": "Test collection"}' \
  {API_URL}/api/v1.0/collections
```

Expected: `201 Created`. Sending the same request again returns `409 Conflict`.

### Delete a collection

```shell
curl -X DELETE -H "Authorization: Bearer $TOKEN" {API_URL}/api/v1.0/collections/my-collection
```

Expected: `204 No Content`. Returns `404` if the collection does not exist, `409` if it still has records.

### List all records

```shell
curl -H "Authorization: Bearer $TOKEN" "{API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items"
```

Expected: `200 OK` with paginated response:

```json
{
  "items": [...],
  "total_items": 9,
  "page": 1,
  "total_pages": 1,
  "page_size": 10
}
```

### Filter by type

```shell
curl -H "Authorization: Bearer $TOKEN" "{API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items?type=workflow"
curl -H "Authorization: Bearer $TOKEN" "{API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items?type=notebook"
```

### Search by text

```shell
curl -H "Authorization: Bearer $TOKEN" "{API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items?q=ndvi"
```

### Filter by keyword

```shell
curl -H "Authorization: Bearer $TOKEN" "{API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items?keywords=vegetation"
```

### Pagination

```shell
curl -H "Authorization: Bearer $TOKEN" "{API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items?page=1&page_size=5"
```

### Get a specific record

```shell
curl -H "Authorization: Bearer $TOKEN" {API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items/ndvi-workflow
```

Expected: `200 OK` with the full record. Verify that the response fields match the JSON file that was merged (title, description, keywords, links, inputParameters, etc.).

### Get catalogue metadata

```shell
curl -H "Authorization: Bearer $TOKEN" {API_URL}/api/v1.0/collections/eodh-workflows-notebooks
```

Expected: `200 OK` with catalogue details (title, description, themes, contacts, links).

### Verify auth is required

```shell
curl {API_URL}/api/v1.0/collections
```

Expected: `403 Forbidden` (no Bearer token).

## 4. Testing a new record

1. Create a feature branch and add a new JSON file to `catalogue/{collection-id}/workflows/` or `catalogue/{collection-id}/notebooks/`
2. Open a PR — verify CI passes
3. Merge the PR — verify CD runs
4. Query the API to confirm the new record appears:

    ```shell
    curl -H "Authorization: Bearer $TOKEN" {API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items/{new-record-id}
    ```

5. Verify the record data matches the JSON file

## 5. Testing record update

1. Modify an existing JSON file (e.g. change the description)
2. Open a PR, merge it
3. Query the API and verify the updated field is reflected

## 6. Testing record deletion

1. Delete a JSON file from `catalogue/`
2. Open a PR, merge it
3. Query the API and verify the record returns `404`:

    ```shell
    curl -H "Authorization: Bearer $TOKEN" {API_URL}/api/v1.0/collections/eodh-workflows-notebooks/items/{deleted-record-id}
    ```

## 7. Expected record IDs

After the initial deployment, these records should exist:

**Workflows:**

| ID | Title |
|----|-------|
| `ndvi-workflow` | NDVI Calculation |
| `bbox-workflow` | BBox Spatial Filter |
| `lst-min-max` | Land Surface Temperature (LST) - Monthly (avg), Day & Night |
| `echo` | Echo |
| `token-access-2` | Token Access v2 |

**Notebooks:**

| ID | Title |
|----|-------|
| `ndvi_calculation` | NDVI Calculation Notebook |
| `cog_preview` | COG Preview Notebook |
| `stats_look` | Statistics Look Notebook |
| `mean_value_calculation` | Mean Value Calculation Notebook |
