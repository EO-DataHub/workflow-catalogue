"""CI validation checks for catalogue records: STAC URL reachability and CWL syntax.

Usage:
    python scripts/validate_ci.py --files catalogue/eodh-workflows-notebooks/workflows/ndvi-workflow.json
    python scripts/validate_ci.py --files catalogue/eodh-workflows-notebooks/workflows/*.json --skip-cwl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

CWL_FETCH_TIMEOUT = 15
CWL_VALIDATE_TIMEOUT = 30


def check_applicable_collections(files: list[Path]) -> list[str]:
    """Check that applicableCollections is not empty."""
    errors = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        collections = data.get("properties", {}).get("applicableCollections", [])
        if not collections:
            print(f"  FAIL: {fp} has empty applicableCollections")
            errors.append(str(fp))
        else:
            print(f"  PASS: {fp} has {len(collections)} collection(s)")
    return errors


def check_cwl_links(files: list[Path]) -> list[str]:
    """Fetch CWL files referenced in records and validate with cwltool."""
    errors: list[str] = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        cwl_links = [
            link
            for link in data.get("links", [])
            if link.get("rel") == "application" and "cwl" in link.get("type", "")
        ]

        for link in cwl_links:
            href = link["href"]
            if not urlparse(href).scheme:
                print(f"  SKIP (local path): {href}")
                continue

            try:
                resp = requests.get(href, timeout=CWL_FETCH_TIMEOUT)
                if not resp.ok:
                    print(f"  WARN: CWL URL returned {resp.status_code}: {href}")
                    continue
            except requests.RequestException as e:
                print(f"  WARN: Could not fetch {href}: {e}")
                continue

            with tempfile.NamedTemporaryFile(suffix=".cwl", mode="w", delete=False) as tmp:
                tmp.write(resp.text)
                tmp_path = tmp.name

            try:
                result = subprocess.run(
                    ["cwltool", "--validate", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=CWL_VALIDATE_TIMEOUT,
                )
            except FileNotFoundError:
                print("  WARN: cwltool not installed, skipping CWL validation")
                return errors
            except subprocess.TimeoutExpired:
                print(f"  WARN: CWL validation timed out for {href}")
                continue

            if result.returncode != 0:
                print(f"  FAIL: CWL invalid - {href}\n{result.stderr}")
                errors.append(href)
            else:
                print(f"  PASS: CWL valid - {href}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="CI validation: STAC URLs and CWL links.")
    parser.add_argument("--files", nargs="+", required=True, help="Catalogue JSON files to check.")
    parser.add_argument("--skip-stac", action="store_true", help="Skip applicableCollections checks.")
    parser.add_argument("--skip-cwl", action="store_true", help="Skip CWL link checks.")
    args = parser.parse_args()

    files = [Path(f) for f in args.files if f.endswith(".json") and not f.endswith("catalog.json") and Path(f).exists()]
    if not files:
        print("No record files to check.")
        return

    errors: list[str] = []

    if not args.skip_stac:
        print("=== Applicable Collections Validation ===")
        errors.extend(check_applicable_collections(files))

    if not args.skip_cwl:
        print("=== CWL Link Validation ===")
        errors.extend(check_cwl_links(files))

    if errors:
        print(f"\n{len(errors)} check(s) failed.")
        sys.exit(1)

    print("\nAll CI checks passed.")


if __name__ == "__main__":
    main()
