#!/usr/bin/env python3
"""Validate SPEC schemas, examples, address fixtures, and local graph integrity."""

from __future__ import annotations

import json
import re
import sys
import warnings
from collections import deque
from pathlib import Path
from typing import Any

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v0"
EXAMPLE_DIR = ROOT / "examples"
FIXTURE_DIR = ROOT / "fixtures" / "addresses"

TOKEN = r"[A-Z][A-Z0-9-]*"
VERSION = r"[0-9][A-Za-z0-9.-]*"
RESOURCE_RE = re.compile(
    rf"^(?P<namespace>{TOKEN}):(?P<name>{TOKEN})@(?P<version>{VERSION})$"
)
BINDING_RE = re.compile(
    rf"^(?P<namespace>{TOKEN}):(?P<name>{TOKEN})@(?P<version>{VERSION})"
    rf":(?P<binding>{TOKEN})@(?P<binding_version>{VERSION})$"
)


class ValidationFailure(Exception):
    pass


def parse_address(value: str) -> dict[str, str] | None:
    match = BINDING_RE.fullmatch(value)
    if match:
        return {"form": "binding", **match.groupdict()}
    match = RESOURCE_RE.fullmatch(value)
    if match:
        return {"form": "resource", **match.groupdict()}
    return None


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def check_schemas() -> int:
    count = 0
    paths = [
        *SCHEMA_DIR.glob("*.schema.json"),
        *EXAMPLE_DIR.rglob("*.schema.json"),
    ]
    for path in sorted(paths):
        jsonschema.Draft202012Validator.check_schema(load_json(path))
        count += 1
    return count


def validate_examples() -> list[tuple[Path, dict[str, Any]]]:
    descriptors: list[tuple[Path, dict[str, Any]]] = []
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    umbrella_path = SCHEMA_DIR / "descriptor.schema.json"
    umbrella_schema = load_json(umbrella_path)
    umbrella_resolver = jsonschema.RefResolver(
        base_uri=umbrella_path.as_uri(), referrer=umbrella_schema
    )
    umbrella_validator = jsonschema.Draft202012Validator(
        umbrella_schema,
        resolver=umbrella_resolver,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
    )

    for path in sorted(EXAMPLE_DIR.rglob("*.yaml")):
        document = load_yaml(path)
        if not isinstance(document, dict):
            raise ValidationFailure(f"{path}: descriptor must be a map")
        schema_ref = document.get("$schema")
        if not isinstance(schema_ref, str):
            raise ValidationFailure(f"{path}: missing string $schema")
        schema_path = (path.parent / schema_ref).resolve()
        if not schema_path.is_relative_to(ROOT) or not schema_path.is_file():
            raise ValidationFailure(f"{path}: unresolved local schema {schema_ref}")
        schema = load_json(schema_path)
        resolver = jsonschema.RefResolver(
            base_uri=schema_path.as_uri(), referrer=schema
        )
        validator = jsonschema.Draft202012Validator(
            schema,
            resolver=resolver,
            format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
        )
        errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
                for error in errors
            )
            raise ValidationFailure(f"{path}: {details}")
        umbrella_errors = sorted(
            umbrella_validator.iter_errors(document), key=lambda error: list(error.path)
        )
        if umbrella_errors:
            details = "; ".join(
                f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
                for error in umbrella_errors
            )
            raise ValidationFailure(f"{path} (descriptor envelope): {details}")
        descriptors.append((path, document))

    return descriptors


def check_address_fixtures() -> int:
    valid = load_json(FIXTURE_DIR / "valid.json")
    invalid = load_json(FIXTURE_DIR / "invalid.json")

    for fixture in valid:
        parsed = parse_address(fixture["address"])
        expected = {key: value for key, value in fixture.items() if key != "address"}
        if parsed != expected:
            raise ValidationFailure(
                f"valid address mismatch for {fixture['address']}: {parsed!r} != {expected!r}"
            )

    for fixture in invalid:
        if parse_address(fixture["address"]) is not None:
            raise ValidationFailure(
                f"invalid address was accepted: {fixture['address']} ({fixture['reason']})"
            )

    return len(valid) + len(invalid)


def require_unique(items: list[dict[str, Any]], field: str, label: str) -> None:
    values = [item[field] for item in items if field in item]
    if len(values) != len(set(values)):
        raise ValidationFailure(f"duplicate {label}: {field}")


def check_descriptor_integrity(
    loaded: list[tuple[Path, dict[str, Any]]]
) -> dict[str, int]:
    descriptors = [document for _, document in loaded]
    namespaces = {item["alias"]: item for item in descriptors if item["kind"] == "Namespace"}
    contracts = {item["address"]: item for item in descriptors if item["kind"] == "Contract"}
    bindings = {
        item["address"]: item
        for item in descriptors
        if item["kind"] == "RepresentationBinding"
    }
    processors = {item["address"]: item for item in descriptors if item["kind"] == "Processor"}
    compositions = {
        item["address"]: item for item in descriptors if item["kind"] == "Composition"
    }
    receipts = [item for item in descriptors if item["kind"] == "Receipt"]

    for collection in (contracts, bindings, processors, compositions):
        if len(collection) == 0:
            raise ValidationFailure("expected non-empty example descriptor collection")

    versioned_resources = [
        *contracts.values(),
        *processors.values(),
        *compositions.values(),
    ]
    require_unique(versioned_resources, "version_id", "version identity")
    require_unique(receipts, "receipt_id", "receipt identity")

    for item in [*contracts.values(), *processors.values(), *compositions.values()]:
        parsed = parse_address(item["address"])
        if not parsed or parsed["form"] != "resource":
            raise ValidationFailure(f"invalid resource address: {item['address']}")
        if parsed["version"] != item["version"]:
            raise ValidationFailure(f"address/version mismatch: {item['address']}")
        namespace = namespaces.get(parsed["namespace"])
        if namespace is None or namespace["namespace_id"] != item["namespace_id"]:
            raise ValidationFailure(f"namespace identity mismatch: {item['address']}")

    for address, binding in bindings.items():
        parsed = parse_address(address)
        parent = contracts.get(binding["parent"])
        if not parsed or parsed["form"] != "binding" or parent is None:
            raise ValidationFailure(f"invalid binding parent/address: {address}")
        if f"{parsed['namespace']}:{parsed['name']}@{parsed['version']}" != binding["parent"]:
            raise ValidationFailure(f"binding address does not extend parent: {address}")
        if parsed["binding"] != binding["binding"] or parsed["binding_version"] != binding["binding_version"]:
            raise ValidationFailure(f"binding token mismatch: {address}")
        for field in ("namespace_id", "family_id", "version_id"):
            if binding[field] != parent[field]:
                raise ValidationFailure(f"binding {field} mismatch: {address}")
        artifact = binding["representation"].get("artifact")
        if artifact and not (Path(next(path for path, doc in loaded if doc is binding)).parent / artifact["ref"]).resolve().is_file():
            raise ValidationFailure(f"binding artifact is missing: {address}")

    for address, contract in contracts.items():
        for binding_address in contract.get("bindings", []):
            if binding_address not in bindings:
                raise ValidationFailure(f"{address}: missing binding {binding_address}")
        for dependency in contract.get("dependencies", []):
            if dependency["contract"] not in contracts:
                raise ValidationFailure(f"{address}: missing dependency {dependency['contract']}")
        for relation in contract.get("relationships", []):
            if relation["target"] not in contracts:
                raise ValidationFailure(f"{address}: missing relation target {relation['target']}")

    for address, processor in processors.items():
        port_names: set[tuple[str, str]] = set()
        for direction in ("inputs", "outputs"):
            for port in processor[direction]:
                key = (direction, port["name"])
                if key in port_names:
                    raise ValidationFailure(f"{address}: duplicate {direction} port {port['name']}")
                port_names.add(key)
                contract = contracts.get(port["contract"])
                if contract is None:
                    raise ValidationFailure(f"{address}: missing Contract {port['contract']}")
                if port.get("contract_version_id") not in (None, contract["version_id"]):
                    raise ValidationFailure(f"{address}: Contract identity mismatch on {port['name']}")
                for binding_address in port.get("bindings", []):
                    binding = bindings.get(binding_address)
                    if binding is None or binding["parent"] != port["contract"]:
                        raise ValidationFailure(f"{address}: invalid binding {binding_address}")

    for address, composition in compositions.items():
        nodes = {node["id"]: node for node in composition["nodes"]}
        if len(nodes) != len(composition["nodes"]):
            raise ValidationFailure(f"{address}: duplicate node ID")
        for node in nodes.values():
            processor = processors.get(node["processor"])
            if processor is None or processor["version_id"] != node["processor_version_id"]:
                raise ValidationFailure(f"{address}: unresolved Processor node {node['id']}")

        adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes}
        indegree = {node_id: 0 for node_id in nodes}
        for edge in composition["edges"]:
            source = edge["from"]
            target = edge["to"]
            if source["node"] not in nodes or target["node"] not in nodes:
                raise ValidationFailure(f"{address}: edge references an unknown node")
            source_processor = processors[nodes[source["node"]]["processor"]]
            target_processor = processors[nodes[target["node"]]["processor"]]
            source_port = next(
                (port for port in source_processor["outputs"] if port["name"] == source["port"]),
                None,
            )
            target_port = next(
                (port for port in target_processor["inputs"] if port["name"] == target["port"]),
                None,
            )
            if source_port is None or target_port is None:
                raise ValidationFailure(f"{address}: edge references an unknown port")
            contract = contracts.get(edge["contract"])
            if (
                contract is None
                or edge["contract_version_id"] != contract["version_id"]
                or source_port["contract"] != edge["contract"]
                or target_port["contract"] != edge["contract"]
            ):
                raise ValidationFailure(f"{address}: incompatible semantic edge")
            if edge.get("binding"):
                accepted_source = source_port.get("bindings", [edge["binding"]])
                accepted_target = target_port.get("bindings", [edge["binding"]])
                if edge["binding"] not in accepted_source or edge["binding"] not in accepted_target:
                    raise ValidationFailure(f"{address}: incompatible representation edge")
            if target["node"] not in adjacency[source["node"]]:
                adjacency[source["node"]].add(target["node"])
                indegree[target["node"]] += 1

        queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            node_id = queue.popleft()
            visited += 1
            for target in adjacency[node_id]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        if visited != len(nodes):
            raise ValidationFailure(f"{address}: composition contains a cycle")

    receipt_ids = {receipt["receipt_id"] for receipt in receipts}
    for receipt in receipts:
        subject = receipt["subject"]
        if "processor" in subject and subject["processor"] not in processors:
            raise ValidationFailure(f"receipt references missing Processor {subject['processor']}")
        if "composition" in subject and subject["composition"] not in compositions:
            raise ValidationFailure(f"receipt references missing Composition {subject['composition']}")
        for parent in receipt.get("parent_receipts", []):
            if parent not in receipt_ids:
                raise ValidationFailure(f"receipt references missing parent {parent}")

    check_pdpp_routes(processors)

    return {
        "namespaces": len(namespaces),
        "contracts": len(contracts),
        "bindings": len(bindings),
        "processors": len(processors),
        "compositions": len(compositions),
        "receipts": len(receipts),
    }


def check_pdpp_routes(processors: dict[str, dict[str, Any]]) -> None:
    edges: dict[str, list[tuple[str, str]]] = {}
    for processor in processors.values():
        if len(processor["inputs"]) == 1 and len(processor["outputs"]) == 1:
            source = processor["inputs"][0]["contract"]
            target = processor["outputs"][0]["contract"]
            edges.setdefault(source, []).append((target, processor["address"]))

    expected_sources = {
        "PDPP:AMAZON-ORDERS@1",
        "PDPP:DOORDASH-ORDERS@1",
        "PDPP:SHOP-ORDERS@1",
    }
    destination = "COMMON:SPEND-EVENT@1"
    expected_downstream = "COMMON:PURCHASE-TO-SPEND-EVENT@1"

    for source in expected_sources:
        queue: deque[tuple[str, list[str]]] = deque([(source, [])])
        seen = {source}
        route: list[str] | None = None
        while queue:
            current, processors_used = queue.popleft()
            if current == destination:
                route = processors_used
                break
            for target, processor_address in edges.get(current, []):
                if target not in seen:
                    seen.add(target)
                    queue.append((target, [*processors_used, processor_address]))
        if route is None or len(route) != 2 or route[-1] != expected_downstream:
            raise ValidationFailure(f"no reusable two-stage PDPP route from {source}")


def main() -> int:
    try:
        schema_count = check_schemas()
        fixture_count = check_address_fixtures()
        descriptors = validate_examples()
        counts = check_descriptor_integrity(descriptors)
    except (ValidationFailure, jsonschema.SchemaError, jsonschema.ValidationError, yaml.YAMLError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    summary = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(
        f"OK: schemas={schema_count}, address_fixtures={fixture_count}, "
        f"descriptors={len(descriptors)} ({summary})"
    )
    print("OK: Amazon, DoorDash, and Shop each derive a two-stage route through COMMON:PURCHASE@1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
