#!/usr/bin/env python3
"""Run the SPEC alpha oracle and verify implementation self-assessment reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import jsonschema
import yaml

import validate as spec_validate


ROOT = Path(__file__).resolve().parents[1]
SUITE_DIR = ROOT / "conformance" / "v0.1-alpha"
SUITE_PATH = SUITE_DIR / "suite.json"
SUITE_SCHEMA_PATH = SUITE_DIR / "suite.schema.json"
REPORT_SCHEMA_PATH = SUITE_DIR / "report.schema.json"
REQUIREMENTS_PATH = SUITE_DIR / "requirements.json"
REQUIREMENTS_SCHEMA_PATH = SUITE_DIR / "requirements.schema.json"
REQUIREMENTS_MARKDOWN_PATH = SUITE_DIR / "REQUIREMENTS.md"


class ConformanceFailure(Exception):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_document(document: Any, schema_path: Path) -> None:
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ConformanceFailure(details)


def resolve_fixture(relative: str) -> Path:
    path = (SUITE_DIR / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.exists():
        raise ConformanceFailure(f"fixture is missing or outside the repository: {relative}")
    return path


def load_suite() -> dict[str, Any]:
    suite = load_json(SUITE_PATH)
    validate_document(suite, SUITE_SCHEMA_PATH)

    classes = suite["classes"]
    tests = suite["tests"]
    class_names = [item["name"] for item in classes]
    test_ids = [item["id"] for item in tests]
    if len(class_names) != len(set(class_names)):
        raise ConformanceFailure("suite contains duplicate conformance classes")
    if len(test_ids) != len(set(test_ids)):
        raise ConformanceFailure("suite contains duplicate test IDs")

    known_classes = set(class_names)
    known_tests = set(test_ids)
    negative_cases = {
        item["id"] for item in load_json(ROOT / "fixtures" / "negative" / "cases.json")
    }
    for item in tests:
        if not set(item["classes"]).issubset(known_classes):
            raise ConformanceFailure(f"{item['id']}: references an unknown class")
        if item["mode"] == "automated":
            resolve_fixture(item["fixture"])
        if item.get("oracle") == "negative" and item.get("negative_case") not in negative_cases:
            raise ConformanceFailure(f"{item['id']}: unknown negative fixture")

    tests_by_id = {item["id"]: item for item in tests}
    for item in classes:
        required = set(item["required_tests"])
        if not required.issubset(known_tests):
            raise ConformanceFailure(f"{item['name']}: references an unknown required test")
        if item["coverage"] == "included" and not required:
            raise ConformanceFailure(f"{item['name']}: included class has no required tests")
        if item["coverage"] == "not-yet-covered" and required:
            raise ConformanceFailure(f"{item['name']}: uncovered class has required tests")
        for test_id in required:
            if item["name"] not in tests_by_id[test_id]["classes"]:
                raise ConformanceFailure(
                    f"{item['name']}: required test {test_id} does not name the class"
                )
    return suite


def load_requirements(suite: dict[str, Any]) -> dict[str, Any]:
    catalog = load_json(REQUIREMENTS_PATH)
    validate_document(catalog, REQUIREMENTS_SCHEMA_PATH)

    source_path = (SUITE_DIR / catalog["source"]["path"]).resolve()
    if not source_path.is_relative_to(ROOT) or not source_path.is_file():
        raise ConformanceFailure("requirements source is missing or outside the repository")
    source_text = source_path.read_text(encoding="utf-8")
    source_text = source_text.replace("\r\n", "\n").replace("\r", "\n")
    source_bytes = source_text.encode("utf-8")
    actual_digest = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    if actual_digest != catalog["source"]["sha256"]:
        raise ConformanceFailure("requirements source digest does not match spec.md")

    keywords = re.findall(r"\bMUST(?: NOT)?\b", source_text)
    if len(keywords) != catalog["source"]["normative_keyword_occurrences"]:
        raise ConformanceFailure("normative keyword occurrence count does not match spec.md")

    exclusions = catalog["excluded_occurrences"]
    requirements = catalog["requirements"]
    exclusion_occurrences = [item["source_occurrence"] for item in exclusions]
    requirement_occurrences = [item["source_occurrence"] for item in requirements]
    if len(exclusion_occurrences) != len(set(exclusion_occurrences)):
        raise ConformanceFailure("requirements catalog contains duplicate exclusions")
    if len(requirement_occurrences) != len(set(requirement_occurrences)):
        raise ConformanceFailure("requirements catalog maps one source occurrence more than once")
    if requirement_occurrences != sorted(requirement_occurrences):
        raise ConformanceFailure("requirements must be ordered by source occurrence")
    if set(exclusion_occurrences) & set(requirement_occurrences):
        raise ConformanceFailure("a normative occurrence cannot be both mapped and excluded")
    expected_occurrences = set(range(1, len(keywords) + 1))
    accounted = set(exclusion_occurrences) | set(requirement_occurrences)
    if accounted != expected_occurrences:
        missing = sorted(expected_occurrences - accounted)
        extra = sorted(accounted - expected_occurrences)
        raise ConformanceFailure(
            f"normative occurrence coverage mismatch; missing={missing}, extra={extra}"
        )

    ids = [item["id"] for item in requirements]
    if len(ids) != len(set(ids)):
        raise ConformanceFailure("requirements catalog contains duplicate requirement IDs")
    for item in [*exclusions, *requirements]:
        occurrence = item["source_occurrence"]
        if item["keyword"] != keywords[occurrence - 1]:
            raise ConformanceFailure(
                f"source occurrence {occurrence}: keyword does not match spec.md"
            )

    known_tests = {item["id"] for item in suite["tests"]}
    for item in requirements:
        unknown_tests = sorted(set(item["test_ids"]) - known_tests)
        if unknown_tests:
            raise ConformanceFailure(f"{item['id']}: unknown test IDs {unknown_tests}")
        if item["disposition"] == "tested" and not (
            item["test_ids"] or item["evidence"]
        ):
            raise ConformanceFailure(f"{item['id']}: tested requirement has no evidence")

    counts = Counter(item["disposition"] for item in requirements)
    expected_summary = {
        "total": len(requirements),
        "tested": counts["tested"],
        "partially_tested": counts["partially-tested"],
        "inspection_required": counts["inspection-required"],
        "deferred": counts["deferred"],
    }
    if catalog["summary"] != expected_summary:
        raise ConformanceFailure("requirements summary does not match its entries")
    return catalog


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_requirements(catalog: dict[str, Any], suite: dict[str, Any]) -> str:
    summary = catalog["summary"]
    lines = [
        "# SPEC v0.1-alpha normative requirements traceability",
        "",
        "Status: exercise; not a certification matrix or certification decision.",
        "",
        (
            f"This catalog accounts for all {catalog['source']['normative_keyword_occurrences']} "
            "uppercase `MUST`/`MUST NOT` occurrences in the pinned specification. Two "
            "occurrences define RFC keywords rather than protocol behavior, leaving "
            f"{summary['total']} normative requirements. A list introduced by one keyword "
            "is kept as one requirement and its complete list is part of the verification scope."
        ),
        "",
        "Disposition totals:",
        "",
        f"- Tested: {summary['tested']}",
        f"- Partially tested: {summary['partially_tested']}",
        f"- Inspection required: {summary['inspection_required']}",
        f"- Deferred coverage gap: {summary['deferred']}",
        "",
        "`Tested` means the present draft suite or its verifier has executable evidence. "
        "`Partially tested` means at least one normative subcondition remains uncovered. "
        "`Inspection required` defines a human review obligation. `Deferred` is an explicit "
        "suite gap and cannot support certification yet.",
        "",
        "## Class-level readiness",
        "",
        "Requirements that apply to multiple classes are counted in every relevant row. "
        "`All Conformance Classes` requirements are included in every row.",
        "",
        "| Class | Suite coverage | Requirements | Tested | Partial | Inspect | Deferred |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for class_item in suite["classes"]:
        applicable = [
            item
            for item in catalog["requirements"]
            if class_item["name"] in item["applies_to"]
            or "All Conformance Classes" in item["applies_to"]
        ]
        counts = Counter(item["disposition"] for item in applicable)
        lines.append(
            f"| {class_item['name']} | {class_item['coverage']} | {len(applicable)} | "
            f"{counts['tested']} | {counts['partially-tested']} | "
            f"{counts['inspection-required']} | {counts['deferred']} |"
        )
    lines.extend(
        [
            "",
            "## Requirement matrix",
            "",
        "| ID | Source | Requirement | Applies to | Disposition | Tests / evidence | Verification |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in catalog["requirements"]:
        references = [*item["test_ids"], *item["evidence"]]
        cells = [
            item["id"],
            f"§{item['section']} / occurrence {item['source_occurrence']}",
            item["requirement"],
            ", ".join(item["applies_to"]),
            item["disposition"],
            ", ".join(f"`{value}`" for value in references) or "—",
            item["verification"],
        ]
        lines.append("| " + " | ".join(markdown_cell(value) for value in cells) + " |")
    lines.extend(
        [
            "",
            "## Explicit exclusions",
            "",
        ]
    )
    for item in catalog["excluded_occurrences"]:
        lines.append(
            f"- Occurrence {item['source_occurrence']} (`{item['keyword']}`): {item['reason']}"
        )
    lines.extend(
        [
            "",
            "The UTF-8/LF-normalized source digest and occurrence accounting are checked mechanically by "
            "`python tools/conformance.py audit-requirements`. Any normative keyword edit "
            "requires an explicit matrix update.",
            "",
        ]
    )
    return "\n".join(lines)


def audit_requirements(suite: dict[str, Any], write: bool = False) -> dict[str, Any]:
    catalog = load_requirements(suite)
    rendered = render_requirements(catalog, suite)
    if write:
        REQUIREMENTS_MARKDOWN_PATH.write_text(rendered, encoding="utf-8")
    elif not REQUIREMENTS_MARKDOWN_PATH.is_file():
        raise ConformanceFailure("generated requirements matrix is missing")
    elif REQUIREMENTS_MARKDOWN_PATH.read_text(encoding="utf-8") != rendered:
        raise ConformanceFailure("generated requirements matrix is stale")
    return catalog


def execute_oracles() -> dict[str, tuple[bool, str]]:
    outcomes: dict[str, tuple[bool, str]] = {}

    def capture(name: str, operation: Any) -> None:
        try:
            detail = operation()
            outcomes[name] = (True, str(detail))
        except (
            spec_validate.ValidationFailure,
            jsonschema.SchemaError,
            jsonschema.ValidationError,
            yaml.YAMLError,
        ) as error:
            outcomes[name] = (False, str(error))

    capture("addresses", spec_validate.check_address_fixtures)
    capture("schemas", spec_validate.check_schemas)

    loaded: list[tuple[Path, dict[str, Any]]] = []

    def catalog() -> str:
        nonlocal loaded
        loaded = spec_validate.validate_examples()
        counts = spec_validate.check_descriptor_integrity(loaded)
        return ", ".join(f"{name}={count}" for name, count in counts.items())

    capture("catalog", catalog)

    def negative() -> int:
        if not loaded:
            raise spec_validate.ValidationFailure("canonical catalog did not load")
        return spec_validate.check_negative_fixtures(loaded)

    capture("negative", negative)
    return outcomes


def count_results(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(item["status"] for item in results)
    return {
        "pass": counts["pass"],
        "fail": counts["fail"],
        "not_run": counts["not-run"],
    }


def run_reference(
    suite: dict[str, Any], subject_name: str, subject_version: str
) -> dict[str, Any]:
    outcomes = execute_oracles()
    results: list[dict[str, Any]] = []
    for test in suite["tests"]:
        if test["mode"] == "implementation-evidence":
            results.append(
                {
                    "test_id": test["id"],
                    "status": "not-run",
                    "detail": "requires an implementation-specific adapter and evidence",
                }
            )
            continue
        passed, detail = outcomes[test["oracle"]]
        results.append(
            {
                "test_id": test["id"],
                "status": "pass" if passed else "fail",
                "detail": detail,
                "evidence": [test["fixture"]],
            }
        )
    return {
        "$schema": "report.schema.json",
        "suite_id": suite["suite_id"],
        "spec": suite["spec"],
        "subject": {"name": subject_name, "version": subject_version},
        "claims": [],
        "results": results,
        "summary": count_results(results),
    }


def verify_report(report: dict[str, Any], suite: dict[str, Any]) -> None:
    validate_document(report, REPORT_SCHEMA_PATH)
    if report["suite_id"] != suite["suite_id"] or report["spec"] != suite["spec"]:
        raise ConformanceFailure("report targets a different suite or SPEC version")

    expected_tests = {item["id"] for item in suite["tests"]}
    result_ids = [item["test_id"] for item in report["results"]]
    if len(result_ids) != len(set(result_ids)):
        raise ConformanceFailure("report contains duplicate test results")
    if set(result_ids) != expected_tests:
        missing = sorted(expected_tests - set(result_ids))
        extra = sorted(set(result_ids) - expected_tests)
        raise ConformanceFailure(f"report test coverage mismatch; missing={missing}, extra={extra}")
    if report["summary"] != count_results(report["results"]):
        raise ConformanceFailure("report summary does not match its results")

    results = {item["test_id"]: item for item in report["results"]}
    for result in report["results"]:
        if result["status"] == "pass" and not result.get("evidence"):
            raise ConformanceFailure(f"{result['test_id']}: passing result has no evidence")

    classes = {item["name"]: item for item in suite["classes"]}
    for claim in report["claims"]:
        item = classes.get(claim)
        if item is None:
            raise ConformanceFailure(f"report claims unknown class {claim}")
        if item["coverage"] != "included":
            raise ConformanceFailure(f"suite does not yet cover claimed class {claim}")
        failed = [
            test_id
            for test_id in item["required_tests"]
            if results[test_id]["status"] != "pass"
        ]
        if failed:
            raise ConformanceFailure(f"{claim} claim has non-passing tests: {failed}")


def write_report(report: dict[str, Any], output: str | None) -> None:
    text = json.dumps(report, indent=2) + "\n"
    if output is None or output == "-":
        sys.stdout.write(text)
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="run canonical automated cases")
    run.add_argument("--output", help="report path, or - for stdout")
    run.add_argument("--subject-name", default="SPEC reference conformance oracle")
    run.add_argument("--subject-version", default="0.1-alpha")

    verify = subparsers.add_parser("verify-report", help="verify a self-assessment report")
    verify.add_argument("report", help="path to the JSON report")

    requirements = subparsers.add_parser(
        "audit-requirements", help="verify normative requirement traceability"
    )
    requirements.add_argument(
        "--write", action="store_true", help="regenerate the human-readable matrix"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        suite = load_suite()
        if args.command == "run":
            report = run_reference(suite, args.subject_name, args.subject_version)
            verify_report(report, suite)
            write_report(report, args.output)
            print(
                f"OK: suite={suite['suite_id']}, pass={report['summary']['pass']}, "
                f"not_run={report['summary']['not_run']}, claims=0"
            )
            return 0
        if args.command == "audit-requirements":
            catalog = audit_requirements(suite, write=args.write)
            summary = catalog["summary"]
            print(
                f"OK: requirements={summary['total']}, tested={summary['tested']}, "
                f"partial={summary['partially_tested']}, "
                f"inspection={summary['inspection_required']}, deferred={summary['deferred']}"
            )
            return 0
        report = load_json(Path(args.report))
        verify_report(report, suite)
        print(
            f"OK: suite={suite['suite_id']}, subject={report['subject']['name']}, "
            f"claims={len(report['claims'])}"
        )
        return 0
    except (
        ConformanceFailure,
        FileNotFoundError,
        json.JSONDecodeError,
        jsonschema.SchemaError,
        yaml.YAMLError,
    ) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
