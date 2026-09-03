# PDP-Connect synthetic commerce stress test

This non-normative example models three independent source Contracts and one
shared downstream route:

```text
SPECX:PDPP-AMAZON-ORDERS@1   --\
                            >-- SPECX:PURCHASE@1 --> SPECX:SPEND-EVENT@1
SPECX:PDPP-DOORDASH-ORDERS@1 --/

SPECX:PDPP-SHOP-ORDERS@1     ----/    (third-source extension)
```

The source JSON Schemas intentionally differ. Each source has one normalization
Processor. `SPECX:PURCHASE-TO-SPEND-EVENT@1` contains no source-specific input
port or binding. A host can therefore add Shop by registering the Shop source
Contract, JSON binding, and normalization Processor without modifying the
downstream declaration.

The files are descriptor and route fixtures, not executable transformations.
Executable Kalo integration and proof that PDP-Connect Core remains unchanged
are tracked as open items in the repository status.

The `SPECX` namespace and UUIDs are experimental SPEC-owned identities. The
representation artifact digests hash the exact example schema bytes. This
canonical example is illustrative; byte-pinned upstream PDP-Connect material
and executable proof live in the evidence repository.
