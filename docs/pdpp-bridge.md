# PDP-Connect ↔ SPEC bridge

Status: non-normative v0 integration design

> This profile is an independent experimental interoperability study and is
> not endorsed by or part of PDP-Connect unless stated otherwise.

## Boundary

The bridge is an adapter outside PDP-Connect Core. PDP-Connect remains
responsible for consent, grants, Personal Servers, Resource Servers,
authentication, collection, connector execution, and delivery of source data.
SPEC begins where a delivered source or stream is assigned an explicit semantic
Contract.

```text
PDP-Connect source/stream
        |
        | bridge association + source identity
        v
SPEC source Contract + Representation Binding
        |
        | declared Processor
        v
shared semantic Contract
```

The bridge has only four responsibilities.

## 1. Associate a PDPP source with a Contract

A bridge configuration records the PDPP source identifier, its source version
or immutable revision, and a SPEC Contract Version. Experimental Contract
addresses use the SPEC-owned `SPECX` namespace; they do not claim PDP-Connect
namespace authority. Amazon and DoorDash are separate semantic sources even if
portions of their JSON happen to have the same shape.

```yaml
source: amazon.orders
source_version: synthetic-v1
contract: SPECX:PDPP-AMAZON-ORDERS@1
contract_version_id: 1fe4eb16-ae6b-4f9b-8ae7-8ac5bd7a2b33
```

This association is deployment configuration. It does not modify the source
declaration in PDP-Connect Core.

## 2. Reuse the PDPP JSON Schema as a binding

The source Contract lists a Representation Binding such as
`SPECX:PDPP-AMAZON-ORDERS@1:JSON@1`. Its representation artifact points at the
existing or exported PDPP JSON Schema and records a digest. SPEC does not copy
the JSON Schema language or reinterpret structural validation as semantic
identity.

If the PDPP schema changes structurally without changing source semantics, a
new binding version may be sufficient. If source meaning changes, the bridge
must bind a new Contract Version.

## 3. Declare transformations

Each source normalization is a separate Processor:

```text
SPECX:PDPP-AMAZON-ORDERS@1   -> SPECX:PURCHASE@1
SPECX:PDPP-DOORDASH-ORDERS@1 -> SPECX:PURCHASE@1
SPECX:PDPP-SHOP-ORDERS@1     -> SPECX:PURCHASE@1
SPECX:PURCHASE@1      -> SPECX:SPEND-EVENT@1
```

Kalo may host implementations and derive routes, but the declarations do not
depend on Kalo. The downstream Purchase-to-SpendEvent Processor reads only the
Purchase Contract. Adding Shop therefore adds one source Contract, one binding,
and one normalization Processor; it does not change downstream logic.

## 4. Propagate provenance

At the bridge boundary, the first Receipt input includes:

- PDPP system and source name;
- source version or immutable revision;
- digest of the delivered source artifact;
- source Contract address and immutable version ID; and
- Representation Binding address and immutable binding version ID.

Processor and composition Receipts then retain the selected Processor versions,
implementation digests, input/output artifact digests, timestamps, and route.
The output digest of each stage is the input digest of the next. A composed
Receipt links the stage Receipts.

## Failure behavior

The bridge must fail explicitly when an address resolves to conflicting IDs,
the schema or data digest does not match, no accepted representation is shared,
a required extension is unknown, or host policy rejects state/effect behavior.
It must not fall back to structural similarity.

## Explicit exclusions

The bridge does not redefine PDPP consent, grants, Personal Servers, Resource
Servers, authentication, collection, source discovery, connector runtime
behavior, or authorization. SPEC Receipts supplement source provenance; they do
not replace PDPP audit or authorization records.
