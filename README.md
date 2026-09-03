# SPEC

SPEC is an open protocol for defining addressable semantic contracts, binding
them to machine representations, and composing independently implemented
processing logic against those contracts.

> Explicit by default. Inferential by extension.

This repository contains the implementation-neutral SPEC v0.1 draft. Kalo is
expected to be its first production-grade host and experimental testbed, but
SPEC does not import, require, or prescribe Kalo.

## Status

SPEC v0.1 is an early design draft. Addresses and descriptors in this repository
are suitable for implementation experiments, not yet for stable publication.
See [STATUS.md](STATUS.md) for the external-review acceptance checklist.

Executable evidence is maintained separately in
[`kalo-build/kalo-pdpp-spec`](https://github.com/kalo-build/kalo-pdpp-spec).

## Repository map

- [`SPEC.md`](SPEC.md) — normative protocol draft
- [`schemas/v0/`](schemas/v0/) — JSON Schema 2020-12 descriptor grammars
- [`examples/pdpp/`](examples/pdpp/) — PDP-Connect synthetic commerce stress test
- [`fixtures/`](fixtures/) — conformance fixtures, beginning with address parsing
- [`docs/pdpp-bridge.md`](docs/pdpp-bridge.md) — deliberately narrow PDPP bridge
- [`docs/kalo-mapping.md`](docs/kalo-mapping.md) — non-normative Kalo mapping
- [`tools/validate.py`](tools/validate.py) — local schema and fixture validation

## Address examples

```text
KA:MO@1
KA:MO@1:YAML@1
ACME:NORMALIZE-INVOICE@1
```

Addresses are compact symbolic references. Immutable publication identity is
separately carried by namespace, family, and version IDs plus a content digest.

## Validate locally

```shell
python tools/validate.py
```

The validator uses Python 3 plus `PyYAML` and `jsonschema`. It checks every
schema, validates descriptor examples, tests address fixtures, and performs a
small set of cross-descriptor integrity checks.

## License

MIT. See [`LICENSE`](LICENSE).

## Design boundaries

SPEC v0 intentionally does not define a universal ontology, semantic DSL,
workflow language, storage API, registry, executable ABI, transaction model,
policy engine, or trust framework. Existing standards such as JSON Schema,
OpenAPI, WIT, Protobuf, SHACL, and AsyncAPI are referenced through bindings
rather than reimplemented.
