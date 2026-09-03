# PDPP synthetic commerce stress test

This non-normative example models three independent source Contracts and one
shared downstream route:

```text
PDPP:AMAZON-ORDERS@1   --\
                            >-- COMMON:PURCHASE@1 --> COMMON:SPEND-EVENT@1
PDPP:DOORDASH-ORDERS@1 --/

PDPP:SHOP-ORDERS@1     ----/    (third-source extension)
```

The source JSON Schemas intentionally differ. Each source has one normalization
Processor. `COMMON:PURCHASE-TO-SPEND-EVENT@1` contains no source-specific input
port or binding. A host can therefore add Shop by registering the Shop source
Contract, JSON binding, and normalization Processor without modifying the
downstream declaration.

The files are descriptor and route fixtures, not executable transformations.
Executable Kalo integration and proof that PDP-Connect Core remains unchanged
are tracked as open items in the repository status.

All UUIDs and digests are synthetic test identities.

