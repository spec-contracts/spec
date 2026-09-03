# Kalo mapping

Status: non-normative implementation note

Kalo is the first intended production host and experimental testbed. The
mapping is approximate because SPEC declarations and Kalo runtime objects have
different responsibilities.

| Kalo concept | SPEC concept | Boundary |
| --- | --- | --- |
| Kalo Spec | Contract | Kalo resolves and validates the semantic declaration. |
| Kalo Format | Representation Binding | A format handler reads or writes one declared binding. |
| Kalo Plugin | Processor implementation | The plugin implements, but does not define, Processor identity. |
| Kalo Pipeline | Composition implementation | A pipeline may execute an inspected, pinned Composition route. |
| Kalo Store | State Port runtime binding | Storage mechanics remain a Kalo concern. |
| Kalo runtime | Processor Host / Composer | The runtime enforces compatibility and emits Receipts. |

## Adapter responsibilities

The first adapter should:

1. parse the v0 descriptors without importing semantics from legacy Kalo names;
2. index Contract and Processor identities separately from symbolic aliases;
3. treat a Kalo format as support for a specific Representation Binding;
4. register Kalo plugins as implementations of declared Processor Versions;
5. reject shape-only composition;
6. expose state requirements and effect policy before execution;
7. serialize the selected route with pinned IDs and digests; and
8. emit stage and composition Receipts.

The adapter may translate existing Kalo manifests at the boundary. Those
translated fields are not part of SPEC Core unless independently standardized.

## Commercial boundary

SPEC changes should be justified by concrete interoperability value and tested
through real Kalo use cases. The protocol repository should not turn every
possible integration request into an obligation for the Kalo implementation.

