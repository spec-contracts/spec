# SPEC v0.1-alpha conformance suite

This is a draft, implementation-independent self-assessment suite for the
existing SPEC v0.1-alpha conceptual model. It is not a certification program,
does not designate a certification authority, and adds no protocol resource or
descriptor field.

The suite separates two kinds of checks:

- `automated` checks run against canonical address, descriptor, graph, digest,
  and negative fixtures using the independent Python oracle;
- `implementation-evidence` checks must be performed by an implementation
  adapter against the implementation under test and cite inspectable evidence.

An implementation may claim an included conformance class only when every test
listed in that class's `required_tests` has status `pass`. Passing results must
carry at least one evidence reference. Classes marked `not-yet-covered` cannot
be claimed with this suite version.

## Run the canonical oracle

```shell
python tools/conformance.py run --output conformance-report.json
python tools/conformance.py verify-report conformance-report.json
```

The canonical oracle intentionally makes no implementation conformance claims:
implementation-evidence cases appear as `not-run`. This command checks the
suite, fixtures, schemas, and report machinery.

## Assess an implementation

An implementation-specific adapter should consume `suite.json`, execute or
otherwise demonstrate every applicable test, and emit a report conforming to
`report.schema.json`. The adapter belongs with the implementation or its
evidence—not in SPEC Core. Verify the resulting report with:

```shell
python tools/conformance.py verify-report path/to/report.json
```

Report verification checks structure, suite identity, complete test coverage,
summary counts, evidence presence for passing tests, and the all-required-tests
rule for every claimed class. It does not establish that cited evidence is
honest; external review remains necessary.

## Coverage

This draft includes claim gates for Core Consumer, Resolver, Representation
Handler, Processor Host, Planner, and Provenance Producer. Core Publisher,
Processor Descriptor Publisher, Composer, and State-Capable Host remain
explicitly uncovered rather than receiving weak placeholder tests.
