# SPEC — Semantic Protocol for Explicit Contracts

Addressable semantic contracts and composable processing boundaries.

SPEC is an open protocol for defining those contracts, binding them to machine
representations, and composing independently implemented processing logic
against them.

> Explicit by default. Inferential by extension.

This repository contains the implementation-neutral SPEC v0.1-alpha draft.
Kalo provides the first experimental native host, but SPEC does not import,
require, or prescribe Kalo.

## Status

SPEC v0.1-alpha is an early design draft. Addresses and descriptors in this repository
are suitable for implementation experiments, not yet for stable publication.
See [STATUS.md](STATUS.md) for the external-review acceptance checklist.

Executable evidence is maintained separately in
[`kalo-build/kalo-pdpp-spec`](https://github.com/kalo-build/kalo-pdpp-spec).

## Repository map

- [`SPEC.md`](SPEC.md) — normative protocol draft
- [`schemas/v0/`](schemas/v0/) — JSON Schema 2020-12 descriptor grammars
- [`examples/pdpp/`](examples/pdpp/) — PDP-Connect synthetic commerce stress test
- [`fixtures/`](fixtures/) — conformance fixtures, beginning with address parsing
- [`conformance/v0.1-alpha/`](conformance/v0.1-alpha/) — draft self-assessment suite and report format
- [`conformance/v0.1-alpha/REQUIREMENTS.md`](conformance/v0.1-alpha/REQUIREMENTS.md) — normative requirement-to-evidence matrix
- [`docs/pdpp-bridge.md`](docs/pdpp-bridge.md) — deliberately narrow PDPP bridge
- [`docs/kalo-mapping.md`](docs/kalo-mapping.md) — non-normative Kalo mapping
- [`tools/validate.py`](tools/validate.py) — local schema and fixture validation

## Address examples

```text
KA:MO@1
KA:MO@1:YAML@1
ACME:NORMALIZE-INVOICE@1
```

Addresses are compact symbolic references. Immutable semantic identity is
separately carried by namespace, family, and version IDs. Exact-byte digests
identify referenced artifacts and execution values; a catalog or publication
record may separately digest descriptor bytes.

## Validate locally

```shell
python tools/validate.py
python tools/conformance.py run --output conformance-report.json
python tools/conformance.py verify-report conformance-report.json
python tools/conformance.py audit-requirements
```

The validator uses Python 3 plus `PyYAML` and `jsonschema`. It checks every
schema, validates descriptor examples and exact artifact digests, tests address
fixtures, and rejects the nine focused architectural negative fixtures.

The draft conformance runner packages those checks into a machine-readable
report and enforces all-required-tests gates for claimed capability classes.
Implementation behavior that the canonical oracle cannot execute is reported
as `not-run`, never inferred as passing. This is self-assessment tooling, not a
certification program.

The requirements audit pins the normative source digest, accounts for every
uppercase `MUST` and `MUST NOT`, validates all referenced test IDs, and rejects
a stale generated matrix. Deferred and partially tested requirements remain
visible certification-readiness gaps.

## License

MIT. See [`LICENSE`](LICENSE).

## Design boundaries

SPEC v0 intentionally does not define a universal ontology, semantic DSL,
workflow language, storage API, registry, executable ABI, transaction model,
policy engine, or trust framework. Existing standards such as JSON Schema,
OpenAPI, WIT, Protobuf, SHACL, and AsyncAPI are referenced through bindings
rather than reimplemented.
