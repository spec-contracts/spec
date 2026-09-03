# Contributing to SPEC

SPEC is developed from interoperable use cases, with Kalo as the first testbed,
while remaining implementable by independent systems.

## Change expectations

A protocol change should include:

1. the interoperability problem and a concrete example;
2. the smallest proposed normative change;
3. effects on identities, offline use, composition, and security;
4. schema and conformance-fixture updates where applicable; and
5. evidence from an implementation experiment when the change affects runtime
   behavior.

Proposals should reuse an established external standard when it already solves
the problem. Optional or inferential behavior belongs in a profile unless it is
required for the explicit Core path.

## Compatibility discipline

Published Contract Versions are immutable. Do not edit an example in a way that
pretends an already-published semantic version changed in place. During this
pre-publication draft phase, breaking edits are allowed but must be called out
in review notes.

Run the local checks before submitting a change:

```shell
python tools/validate.py
```

No contribution may introduce a normative dependency on Kalo or PDPP Core.

