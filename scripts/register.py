"""CD script: register catalogue records in wf-catalogue-service and publish to ADES.

Usage:
    python scripts/register.py --files catalogue/workflows/ndvi-workflow.json
    python scripts/register.py --files catalogue/workflows/*.json --skip-ades
    python scripts/register.py --deleted-ids ndvi-workflow echo

Environment variables:
    WF_CATALOGUE_API_URL                        - wf-catalogue-service base URL
    EODH__BASE_URL                              - EODH platform base URL
    EODH__REALM                                 - Keycloak realm
    EODH__USERNAME                              - Service account username
    EODH__PASSWORD                              - Service account password
    EODH__CLIENT_ID                             - OAuth2 client ID
    EODH__WORKSPACE_SERVICES_ENDPOINT_PATH      - Workspace services API path
    EODH__ADES_ENDPOINT_PATH                    - ADES API path
    EODH__WORKSPACE_NAME                        - Publishing workspace name
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests

TIMEOUT = 30
OGC_PROCESSES_PATH = "ogc-api/processes"


def get_keycloak_token() -> str:
    """Get Keycloak access token via password grant."""
    base_url = os.environ["EODH__BASE_URL"]
    realm = os.environ["EODH__REALM"]
    token_url = urljoin(base_url, f"/keycloak/realms/{realm}/protocol/openid-connect/token")

    resp = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": os.environ["EODH__CLIENT_ID"],
            "username": os.environ["EODH__USERNAME"],
            "password": os.environ["EODH__PASSWORD"],
            "grant_type": "password",
            "scope": "openid",
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_workspace_token(keycloak_token: str, workspace: str) -> str:
    """Exchange Keycloak token for a workspace-scoped session token."""
    base_url = os.environ["EODH__BASE_URL"]
    ws_path = os.environ["EODH__WORKSPACE_SERVICES_ENDPOINT_PATH"]
    sessions_url = urljoin(base_url, f"{ws_path}/{workspace}/me/sessions")

    resp = requests.post(
        sessions_url,
        headers={
            "Authorization": f"Bearer {keycloak_token}",
            "Accept": "application/json",
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["access"]


def register_record(file_path: Path, token: str) -> bool:
    """Register a single record via POST /register. On 409 Conflict, DELETE and re-POST."""
    api_url = os.environ["WF_CATALOGUE_API_URL"].rstrip("/")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.loads(file_path.read_text(encoding="utf-8"))
    record_id = data["id"]

    resp = requests.post(f"{api_url}/api/v1.0/register", json=data, headers=headers, timeout=TIMEOUT)

    if resp.status_code == 409:
        print(f"  Record '{record_id}' already exists, deleting and re-registering...")
        del_resp = requests.delete(f"{api_url}/api/v1.0/register/{record_id}", headers=headers, timeout=TIMEOUT)
        if del_resp.status_code not in (204, 404):
            print(f"  FAIL: Could not delete '{record_id}': {del_resp.status_code} {del_resp.text}")
            return False
        resp = requests.post(f"{api_url}/api/v1.0/register", json=data, headers=headers, timeout=TIMEOUT)

    if resp.status_code == 201:
        print(f"  OK: Registered '{record_id}'")
        return True

    print(f"  FAIL: Could not register '{record_id}': {resp.status_code} {resp.text}")
    return False


def delete_record(record_id: str, token: str) -> bool:
    """Delete a record via DELETE /register/{record_id}."""
    api_url = os.environ["WF_CATALOGUE_API_URL"].rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.delete(f"{api_url}/api/v1.0/register/{record_id}", headers=headers, timeout=TIMEOUT)

    if resp.status_code == 204:
        print(f"  OK: Deleted '{record_id}'")
        return True
    if resp.status_code == 404:
        print(f"  SKIP: '{record_id}' not found (already deleted)")
        return True

    print(f"  FAIL: Could not delete '{record_id}': {resp.status_code} {resp.text}")
    return False


def register_ades_process(file_path: Path, workspace_token: str) -> bool:
    """Register CWL process in ADES for a workflow record."""
    data = json.loads(file_path.read_text(encoding="utf-8"))

    if data.get("properties", {}).get("type") != "workflow":
        return True

    cwl_links = [
        link for link in data.get("links", []) if link.get("rel") == "application" and "cwl" in link.get("type", "")
    ]

    if not cwl_links:
        print(f"  SKIP ADES: No CWL application link in {file_path.name}")
        return True

    base_url = os.environ["EODH__BASE_URL"]
    ades_path = os.environ["EODH__ADES_ENDPOINT_PATH"]
    workspace = os.environ["EODH__WORKSPACE_NAME"]
    ades_url = urljoin(base_url, ades_path).rstrip("/")
    processes_url = f"{ades_url}/{workspace}/{OGC_PROCESSES_PATH}"

    headers = {
        "Authorization": f"Bearer {workspace_token}",
        "Content-Type": "application/cwl+yaml",
        "Accept": "application/json",
    }

    record_id = data["id"]
    ok = True

    for link in cwl_links:
        href = link["href"]
        print(f"  Fetching CWL: {href}")

        try:
            cwl_resp = requests.get(href, timeout=TIMEOUT)
            cwl_resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  FAIL: Could not fetch CWL {href}: {e}")
            ok = False
            continue

        # Unregister existing process (ADES returns 403 for non-existent)
        del_resp = requests.delete(f"{processes_url}/{record_id}", headers=headers, timeout=TIMEOUT)
        if del_resp.status_code not in (200, 204, 403, 404):
            print(f"  WARN: Unregister returned {del_resp.status_code} for '{record_id}'")

        reg_resp = requests.post(processes_url, headers=headers, data=cwl_resp.content, timeout=TIMEOUT)

        if reg_resp.status_code in (200, 201):
            print(f"  OK: ADES process registered for '{record_id}'")
        elif reg_resp.status_code == 409:
            print(f"  WARN: ADES process '{record_id}' already exists (409 after unregister)")
        else:
            print(f"  FAIL: ADES registration failed for '{record_id}': {reg_resp.status_code} {reg_resp.text}")
            ok = False

    return ok


def publish_workflow(record_id: str, workspace_token: str) -> bool:
    """Publish workflow by uploading access policy and triggering harvest."""
    base_url = os.environ["EODH__BASE_URL"].rstrip("/")
    workspace = os.environ["EODH__WORKSPACE_NAME"]
    headers = {
        "Authorization": f"Bearer {workspace_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    policy = json.dumps({"workflows": {record_id: {"access": "public"}}})
    policy_resp = requests.post(
        f"{base_url}/api/workspaces/{workspace}/data-loader",
        json={"fileContent": policy, "fileName": "access-policy.json"},
        headers=headers,
        timeout=TIMEOUT,
    )

    if not policy_resp.ok:
        print(f"  WARN: Access policy upload failed for '{record_id}': {policy_resp.status_code} {policy_resp.text}")
        return False

    harvest_resp = requests.post(
        f"{base_url}/workspaces/{workspace}/harvest",
        headers=headers,
        timeout=TIMEOUT,
    )

    if not harvest_resp.ok:
        print(f"  WARN: Harvest trigger failed for '{record_id}': {harvest_resp.status_code} {harvest_resp.text}")
        return False

    print(f"  OK: Published '{record_id}'")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="CD: register records and publish to ADES.")
    parser.add_argument("--files", nargs="*", default=[], help="Catalogue JSON files to register.")
    parser.add_argument("--deleted-ids", nargs="*", default=[], help="Record IDs to delete (from removed files).")
    parser.add_argument("--skip-ades", action="store_true", help="Skip ADES process registration.")
    parser.add_argument("--skip-publish", action="store_true", help="Skip access policy publishing.")
    args = parser.parse_args()

    files = [Path(f) for f in args.files if f.endswith(".json") and not f.endswith("catalog.json") and Path(f).exists()]

    if not files and not args.deleted_ids:
        print("Nothing to do.")
        return

    errors: list[str] = []

    print("=== Authenticating ===")
    try:
        keycloak_token = get_keycloak_token()
        print("  OK: Keycloak token obtained")
    except Exception as e:
        print(f"  FAIL: Could not get Keycloak token: {e}")
        sys.exit(1)

    workspace_token = None
    needs_workspace_token = (not args.skip_ades or not args.skip_publish) and files
    if needs_workspace_token:
        workspace = os.environ.get("EODH__WORKSPACE_NAME", "")
        if workspace:
            try:
                workspace_token = get_workspace_token(keycloak_token, workspace)
                print("  OK: Workspace token obtained")
            except Exception as e:
                print(f"  WARN: Could not get workspace token: {e}")
                print("  ADES registration and publishing will be skipped.")

    if files:
        print(f"\n=== Registering {len(files)} record(s) in wf-catalogue-service ===")
        for fp in files:
            if not register_record(fp, keycloak_token):
                errors.append(f"register:{fp}")

    if args.deleted_ids:
        print(f"\n=== Deleting {len(args.deleted_ids)} record(s) from wf-catalogue-service ===")
        for record_id in args.deleted_ids:
            if not delete_record(record_id, keycloak_token):
                errors.append(f"delete:{record_id}")

    if files and not args.skip_ades and workspace_token:
        print("\n=== Registering CWL processes in ADES ===")
        for fp in files:
            if not register_ades_process(fp, workspace_token):
                errors.append(f"ades:{fp}")

    if files and not args.skip_publish and workspace_token:
        print("\n=== Publishing workflows ===")
        for fp in files:
            data = json.loads(fp.read_text(encoding="utf-8"))
            if data.get("properties", {}).get("type") == "workflow":
                record_id = data["id"]
                if not publish_workflow(record_id, workspace_token):
                    errors.append(f"publish:{record_id}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("\nAll CD steps completed successfully.")


if __name__ == "__main__":
    main()
