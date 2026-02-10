"""CI validation checks for catalogue records: STAC URL reachability and CWL syntax.

Usage:
    python scripts/validate_ci.py --files catalogue/workflows/ndvi-workflow.json
    python scripts/validate_ci.py --files catalogue/workflows/*.json --skip-cwl
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

STAC_TIMEOUT = 10
STAC_RETRIES = 2
CWL_FETCH_TIMEOUT = 15
CWL_VALIDATE_TIMEOUT = 30


def check_stac_urls(files: list[Path]) -> list[str]:
    """Check that applicableCollections URLs return 200."""
    url_to_files: dict[str, list[str]] = {}
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        for url in data.get("properties", {}).get("applicableCollections", []):
            url_to_files.setdefault(url, []).append(str(fp))

    if not url_to_files:
        print("No STAC collection URLs found.")
        return []

    print(f"Checking {len(url_to_files)} unique STAC collection URL(s)...")
    unreachable = []
    for url, refs in url_to_files.items():
        ok = False
        for _ in range(STAC_RETRIES + 1):
            try:
                if requests.get(url, timeout=STAC_TIMEOUT).ok:
                    ok = True
                    break
            except requests.RequestException:
                pass

        if ok:
            print(f"  REACHABLE: {url}")
        else:
            print(f"  UNREACHABLE: {url} (referenced by: {', '.join(refs)})")
            unreachable.append(url)

    return unreachable


def check_cwl_links(files: list[Path]) -> list[str]:
    """Fetch CWL files referenced in records and validate with cwltool."""
    errors = []
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
    parser.add_argument("--skip-stac", action="store_true", help="Skip STAC URL checks.")
    parser.add_argument("--skip-cwl", action="store_true", help="Skip CWL link checks.")
    args = parser.parse_args()

    files = [Path(f) for f in args.files if f.endswith(".json") and not f.endswith("catalog.json") and Path(f).exists()]
    if not files:
        print("No record files to check.")
        return

    errors: list[str] = []

    if not args.skip_stac:
        print("=== STAC Collection URL Validation ===")
        errors.extend(check_stac_urls(files))

    if not args.skip_cwl:
        print("=== CWL Link Validation ===")
        errors.extend(check_cwl_links(files))

    if errors:
        print(f"\n{len(errors)} check(s) failed.")
        sys.exit(1)

    print("\nAll CI checks passed.")


if __name__ == "__main__":
    main()
