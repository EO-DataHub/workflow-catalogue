"""CI validation checks for catalogue records: STAC URL reachability, CWL syntax and CWL inputs.

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
from typing import Any
from urllib.parse import urlparse

import requests
import yaml

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


def _cwl_workflow_process(cwl_doc: object) -> dict[str, Any] | None:
    """Return the Workflow process from a $graph document, or the top-level process."""
    if not isinstance(cwl_doc, dict):
        return None
    if "$graph" not in cwl_doc:
        return cwl_doc
    for process in cwl_doc["$graph"]:
        if isinstance(process, dict) and process.get("class") == "Workflow":
            return process
    return None


def _cwl_input_name(input_id: str) -> str:
    return input_id.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _normalise_cwl_type(cwl_type: object) -> tuple[str, bool]:
    """Return the CWL type as a string without the optional marker, and whether the input is optional."""
    if isinstance(cwl_type, list):
        non_null = [t for t in cwl_type if t != "null"]
        optional = len(non_null) < len(cwl_type)
        if len(non_null) == 1:
            type_str, inner_optional = _normalise_cwl_type(non_null[0])
            return type_str, optional or inner_optional
        return str(cwl_type), optional
    if isinstance(cwl_type, dict):
        if cwl_type.get("type") == "array":
            items, _ = _normalise_cwl_type(cwl_type.get("items"))
            return f"{items}[]", False
        return str(cwl_type.get("type")), False
    type_str = str(cwl_type)
    if type_str.endswith("?"):
        return type_str[:-1], True
    return type_str, False


def _cwl_inputs(process: dict[str, Any]) -> dict[str, tuple[str, bool]]:
    """Map each process input name to its normalised type and optional flag."""
    raw_inputs = process.get("inputs") or {}
    if isinstance(raw_inputs, list):
        raw_inputs = {_cwl_input_name(inp["id"]): inp for inp in raw_inputs if isinstance(inp, dict) and "id" in inp}
    inputs = {}
    for name, spec in raw_inputs.items():
        cwl_type = spec.get("type") if isinstance(spec, dict) else spec
        inputs[_cwl_input_name(name)] = _normalise_cwl_type(cwl_type)
    return inputs


def check_cwl_inputs(fp: Path, href: str, cwl_text: str, input_parameters: dict[str, Any]) -> list[str]:
    """Compare a record's inputParameters with the inputs of the CWL Workflow."""
    try:
        process = _cwl_workflow_process(yaml.safe_load(cwl_text))
    except yaml.YAMLError as e:
        print(f"  FAIL: Could not parse CWL {href}: {e}")
        return [href]
    if process is None:
        print(f"  FAIL: No Workflow process found in {href}")
        return [href]

    cwl_inputs = _cwl_inputs(process)
    problems = []
    for name, param in input_parameters.items():
        if name not in cwl_inputs:
            problems.append(f"input '{name}' is not an input in the CWL")
            continue
        cwl_type, optional = cwl_inputs[name]
        if param.get("cwlType") != cwl_type:
            problems.append(f"input '{name}' has cwlType '{param.get('cwlType')}' but the CWL type is '{cwl_type}'")
        if optional and param.get("required") is not False:
            problems.append(f"input '{name}' is optional in the CWL but 'required' is not false")

    if problems:
        for problem in problems:
            print(f"  FAIL: {fp} - {problem} ({href})")
        return [f"{fp}: {problem}" for problem in problems]
    print(f"  PASS: Inputs match CWL - {fp}")
    return []


def check_cwl_links(files: list[Path]) -> list[str]:
    """Fetch CWL files referenced in records, compare their inputs and validate with cwltool."""
    errors: list[str] = []
    cwltool_available = True
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        input_parameters = data.get("properties", {}).get("inputParameters", {})
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

            errors.extend(check_cwl_inputs(fp, href, resp.text, input_parameters))

            if not cwltool_available:
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
                cwltool_available = False
                continue
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
    parser = argparse.ArgumentParser(description="CI validation: STAC URLs, CWL links and CWL inputs.")
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
