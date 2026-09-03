#!/usr/bin/env python3
"""Validate SPEC schemas, examples, address fixtures, and local graph integrity."""

from __future__ import annotations

import json
import hashlib
import re
import sys
import warnings
from copy import deepcopy
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v0"
EXAMPLE_DIR = ROOT / "examples"
FIXTURE_DIR = ROOT / "fixtures" / "addresses"
NEGATIVE_FIXTURE_PATH = ROOT / "fixtures" / "negative" / "cases.json"

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


def unique_index(
    descriptors: list[dict[str, Any]], kind: str, key: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in descriptors:
        if item["kind"] != kind:
            continue
        value = item[key]
        if value in result:
            if kind == "Namespace" and result[value]["namespace_id"] != item["namespace_id"]:
                raise ValidationFailure(f"ambiguous namespace identity: {value}")
            raise ValidationFailure(f"duplicate {kind} {key}: {value}")
        result[value] = item
    return result


def resolve_local_ref(descriptor_path: Path, ref: str) -> tuple[Path, str]:
    parsed = urlsplit(ref)
    if parsed.scheme:
        raise ValidationFailure(f"{descriptor_path}: non-local artifact ref {ref}")
    path = (descriptor_path.parent / parsed.path).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValidationFailure(f"{descriptor_path}: unresolved artifact ref {ref}")
    return path, parsed.fragment


def verify_exact_digest(path: Path, expected: str, label: str) -> None:
    actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValidationFailure(f"{label}: expected {expected}, got {actual}")


def check_descriptor_integrity(
    loaded: list[tuple[Path, dict[str, Any]]]
) -> dict[str, int]:
    descriptors = [document for _, document in loaded]
    paths = {id(document): path for path, document in loaded}
    namespaces = unique_index(descriptors, "Namespace", "alias")
    contracts = unique_index(descriptors, "Contract", "address")
    bindings = unique_index(descriptors, "RepresentationBinding", "address")
    processors = unique_index(descriptors, "Processor", "address")
    compositions = unique_index(descriptors, "Composition", "address")
    implementations = unique_index(descriptors, "ProcessorImplementation", "implementation_id")
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

    for item in descriptors:
        required = item.get("required_extensions", [])
        if required:
            raise ValidationFailure(
                f"{item['kind']} requires unsupported extension {required[0]}"
            )

    for item in [*contracts.values(), *processors.values(), *compositions.values()]:
        parsed = parse_address(item["address"])
        if not parsed or parsed["form"] != "resource":
            raise ValidationFailure(f"invalid resource address: {item['address']}")
        if parsed["version"] != item["version"]:
            raise ValidationFailure(f"address/version mismatch: {item['address']}")
        namespace = namespaces.get(parsed["namespace"])
        if namespace is None or namespace["namespace_id"] != item["namespace_id"]:
            raise ValidationFailure(f"namespace identity mismatch: {item['address']}")
        definition = item.get("definition")
        if definition and definition.get("ref"):
            path, _ = resolve_local_ref(paths[id(item)], definition["ref"])
            if definition.get("digest"):
                verify_exact_digest(path, definition["digest"], f"{item['address']} definition")

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
        if artifact:
            artifact_path, _ = resolve_local_ref(paths[id(binding)], artifact["ref"])
            if artifact.get("digest"):
                verify_exact_digest(artifact_path, artifact["digest"], address)

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

    for implementation_id, implementation in implementations.items():
        processor = processors.get(implementation["processor"])
        if processor is None or processor["version_id"] != implementation["processor_version_id"]:
            raise ValidationFailure(
                f"{implementation_id}: unresolved ProcessorImplementation target"
            )
        artifact = implementation["artifact"]
        artifact_path, fragment = resolve_local_ref(paths[id(implementation)], artifact["ref"])
        if fragment:
            raise ValidationFailure(f"{implementation_id}: executable ref has a fragment")
        verify_exact_digest(artifact_path, artifact["digest"], implementation_id)

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
    receipts_by_id = {receipt["receipt_id"]: receipt for receipt in receipts}
    for receipt in receipts:
        subject = receipt["subject"]
        if "processor" in subject and subject["processor"] not in processors:
            raise ValidationFailure(f"receipt references missing Processor {subject['processor']}")
        if "composition" in subject and subject["composition"] not in compositions:
            raise ValidationFailure(f"receipt references missing Composition {subject['composition']}")
        for parent in receipt.get("parent_receipts", []):
            if parent not in receipt_ids:
                raise ValidationFailure(f"receipt references missing parent {parent}")
        if "processor" in subject and len(receipt.get("parent_receipts", [])) == 1:
            parent = receipts_by_id[receipt["parent_receipts"][0]]
            if parent["outputs"][0]["artifact_digest"] != receipt["inputs"][0]["artifact_digest"]:
                raise ValidationFailure("malformed Receipt chain: adjacent digests differ")
        if "composition" in subject and receipt.get("route"):
            route_receipts = [receipts_by_id[node["receipt_id"]] for node in receipt["route"]]
            for previous, current in zip(route_receipts, route_receipts[1:]):
                if previous["outputs"][0]["artifact_digest"] != current["inputs"][0]["artifact_digest"]:
                    raise ValidationFailure("malformed Receipt route: adjacent digests differ")
            if receipt["inputs"][0]["artifact_digest"] != route_receipts[0]["inputs"][0]["artifact_digest"]:
                raise ValidationFailure("malformed Receipt route input")
            if receipt["outputs"][0]["artifact_digest"] != route_receipts[-1]["outputs"][0]["artifact_digest"]:
                raise ValidationFailure("malformed Receipt route output")

    check_pdpp_routes(processors)

    return {
        "namespaces": len(namespaces),
        "contracts": len(contracts),
        "bindings": len(bindings),
        "processors": len(processors),
        "compositions": len(compositions),
        "implementations": len(implementations),
        "receipts": len(receipts),
    }


def check_pdpp_routes(processors: dict[str, dict[str, Any]]) -> None:
    edges: dict[str, list[tuple[str, str]]] = {}
    for processor in processors.values():
        if any(port.get("required", True) for port in processor.get("state", [])):
            continue
        effects = processor.get("effects")
        if effects is None or not effects["safe"] or effects["open_world"]:
            continue
        if len(processor["inputs"]) == 1 and len(processor["outputs"]) == 1:
            source = processor["inputs"][0]["contract"]
            target = processor["outputs"][0]["contract"]
            edges.setdefault(source, []).append((target, processor["address"]))

    expected_sources = {
        "SPECX:PDPP-AMAZON-ORDERS@1",
        "SPECX:PDPP-DOORDASH-ORDERS@1",
        "SPECX:PDPP-SHOP-ORDERS@1",
    }
    destination = "SPECX:SPEND-EVENT@1"
    expected_downstream = "SPECX:PURCHASE-TO-SPEND-EVENT@1"

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


def check_negative_fixtures(
    loaded: list[tuple[Path, dict[str, Any]]]
) -> int:
    fixtures = load_json(NEGATIVE_FIXTURE_PATH)

    def documents() -> list[tuple[Path, dict[str, Any]]]:
        return [(path, deepcopy(document)) for path, document in loaded]

    def find(items: list[tuple[Path, dict[str, Any]]], kind: str, key: str, value: str) -> dict[str, Any]:
        return next(document for _, document in items if document["kind"] == kind and document.get(key) == value)

    def same_structure_wrong_contract(items: list[tuple[Path, dict[str, Any]]]) -> None:
        processor = find(items, "Processor", "address", "SPECX:PDPP-AMAZON-TO-PURCHASE@1")
        processor["outputs"][0]["contract"] = "SPECX:PURCHASE-SHAPE-CLONE@1"

    def missing_required_binding(items: list[tuple[Path, dict[str, Any]]]) -> None:
        items[:] = [
            pair for pair in items
            if pair[1].get("address") != "SPECX:PURCHASE@1:JSON@1"
        ]

    def incompatible_processor_edge(items: list[tuple[Path, dict[str, Any]]]) -> None:
        processor = find(items, "Processor", "address", "SPECX:PURCHASE-TO-SPEND-EVENT@1")
        processor["inputs"][0]["contract"] = "SPECX:SPEND-EVENT@1"

    def unknown_required_extension(items: list[tuple[Path, dict[str, Any]]]) -> None:
        processor = find(items, "Processor", "address", "SPECX:PURCHASE-TO-SPEND-EVENT@1")
        processor["required_extensions"] = ["SPECX:UNKNOWN"]

    def unresolved_implementation(items: list[tuple[Path, dict[str, Any]]]) -> None:
        items.append((NEGATIVE_FIXTURE_PATH, {
            "kind": "ProcessorImplementation",
            "implementation_id": "c0bb9521-13af-4d7c-bf50-dcf544f360d0",
            "processor": "SPECX:MISSING-PROCESSOR@1",
            "processor_version_id": "42c0e967-4c64-43ca-900f-4a6b237a81fc",
            "artifact": {"ref": "missing.wasm", "digest": "sha256:" + "0" * 64},
        }))

    def unsupported_required_state(items: list[tuple[Path, dict[str, Any]]]) -> None:
        processor = find(items, "Processor", "address", "SPECX:PDPP-AMAZON-TO-PURCHASE@1")
        processor["state"] = [{
            "name": "case",
            "contract": "SPECX:PURCHASE@1",
            "contract_version_id": "cf44e72f-08af-4c7b-a732-68c8078352d4",
            "access": "read",
        }]

    def malformed_receipt_chain(items: list[tuple[Path, dict[str, Any]]]) -> None:
        receipt = find(items, "Receipt", "receipt_id", "7c6c4e0a-9e54-4ef5-b3c0-8ef941c33b5b")
        receipt["inputs"][0]["artifact_digest"] = "sha256:" + "0" * 64

    def mutated_immutable_version(items: list[tuple[Path, dict[str, Any]]]) -> None:
        contract = find(items, "Contract", "address", "SPECX:PURCHASE@1")
        duplicate = deepcopy(contract)
        duplicate["definition"]["body"] += " Mutated after publication."
        items.append((NEGATIVE_FIXTURE_PATH, duplicate))

    def ambiguous_namespace(items: list[tuple[Path, dict[str, Any]]]) -> None:
        namespace = find(items, "Namespace", "alias", "SPECX")
        duplicate = deepcopy(namespace)
        duplicate["namespace_id"] = "a9ff6572-76ad-4083-b999-ac55f5f5db44"
        items.append((NEGATIVE_FIXTURE_PATH, duplicate))

    mutations = {
        "same-structure-wrong-contract": same_structure_wrong_contract,
        "missing-required-binding": missing_required_binding,
        "incompatible-processor-edge": incompatible_processor_edge,
        "unknown-required-extension": unknown_required_extension,
        "unresolved-processor-implementation": unresolved_implementation,
        "unsupported-required-state": unsupported_required_state,
        "malformed-receipt-chain": malformed_receipt_chain,
        "mutated-immutable-contract-version": mutated_immutable_version,
        "ambiguous-namespace-identity": ambiguous_namespace,
    }
    fixture_ids = [fixture["id"] for fixture in fixtures]
    if len(fixtures) != 9 or set(fixture_ids) != set(mutations):
        raise ValidationFailure("negative fixture manifest must contain exactly the nine v0.1-alpha cases")
    for fixture in fixtures:
        case = documents()
        mutations[fixture["id"]](case)
        try:
            check_descriptor_integrity(case)
        except ValidationFailure:
            continue
        raise ValidationFailure(f"negative fixture was accepted: {fixture['id']}")
    return len(fixtures)


def main() -> int:
    try:
        schema_count = check_schemas()
        fixture_count = check_address_fixtures()
        descriptors = validate_examples()
        counts = check_descriptor_integrity(descriptors)
        negative_count = check_negative_fixtures(descriptors)
    except (ValidationFailure, jsonschema.SchemaError, jsonschema.ValidationError, yaml.YAMLError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    summary = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(
        f"OK: schemas={schema_count}, address_fixtures={fixture_count}, "
        f"negative_fixtures={negative_count}, descriptors={len(descriptors)} ({summary})"
    )
    print("OK: Amazon, DoorDash, and Shop each derive a two-stage route through SPECX:PURCHASE@1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
