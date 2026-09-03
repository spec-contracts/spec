# SPEC v0.1-alpha — Semantic Protocol for Explicit Contracts

Status: Draft 0.1-alpha
Audience: implementers and technical reviewers

## 1. Scope

SPEC is an implementation-neutral protocol for:

1. defining stable, addressable semantic contracts;
2. binding contracts to one or more machine representations;
3. declaring processors that transform between semantic contracts;
4. mechanically composing compatible processors;
5. exposing material state dependencies and side-effect properties; and
6. preserving identity and provenance across transformations.

The normal interoperability path is nominal and explicit. It does not require
RDF, OWL, ontological reasoning, an AI model, a universal semantic language, or
network access. Optional profiles MAY add inferential behavior, but MUST NOT
change the meaning of Core declarations.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**,
and **MAY** are to be interpreted as described by RFC 2119 and RFC 8174 when,
and only when, they appear in all capitals.

## 2. Architecture invariants

Every conforming implementation MUST preserve these invariants:

1. Structural compatibility does not imply semantic compatibility.
2. One semantic Contract may have multiple physical representations.
3. A Processor declaration is distinct from each Processor implementation.
4. An execution mechanism does not determine semantic identity.
5. State dependencies that affect composition correctness are visible.
6. Symbolic names are not the sole source of immutable identity.
7. Published resources remain meaningful and usable offline.
8. SPEC remains useful without semantic inference.
9. Existing standards are reused rather than duplicated.
10. SPEC can be implemented without Kalo code.

## 3. Terms

**Namespace**  
An authority under which named resources are published. A namespace has a
human-friendly alias and an immutable identity.

**Contract Family**  
A stable semantic concept across versions, such as `KA:MO`.

**Contract Version**  
An immutable version of a semantic Contract, such as `KA:MO@1`.

**Representation Binding**  
A machine representation of a specific Contract Version, such as
`KA:MO@1:YAML@1`.

**Processor**  
An independently addressable, implementation-neutral processing boundary that
declares semantic inputs and outputs.

**Composition**  
A directed graph of compatible Processor boundaries.

**State Port**  
A named semantic state dependency exposed by a Processor.

**Receipt**  
A machine-readable record of one Processor execution or a composed execution.

**Resolver**  
A mechanism that resolves symbolic references to descriptors or artifacts.

## 4. Descriptor envelope and encoding

Core resources are represented by typed descriptors. A descriptor MUST contain
`spec` and `kind`. The v0 kinds are:

- `Namespace`
- `Contract`
- `RepresentationBinding`
- `Processor`
- `ProcessorImplementation`
- `Composition`
- `Receipt`

JSON is the data model used by the v0 schemas. A YAML document is conforming if
it resolves to the same JSON data model. Map keys MUST be strings. Publishers
MUST NOT rely on map ordering, YAML tags, anchors, aliases, duplicate keys,
comments, or non-JSON scalar types for semantics.

The schemas under `schemas/v0/` define the machine grammar. This document
defines semantics and takes precedence if a schema and prose disagree.

## 5. Symbolic addressing

### 5.1 Grammar

The Core address grammar is:

```abnf
namespace        = ALPHA *( ALPHA / DIGIT / "-" )
name             = ALPHA *( ALPHA / DIGIT / "-" )
version          = DIGIT *( ALPHA / DIGIT / "." / "-" )
binding          = ALPHA *( ALPHA / DIGIT / "-" )
resource-address = namespace ":" name "@" version
binding-address  = resource-address ":" binding "@" version
```

In v0, `namespace`, `name`, and `binding` tokens MUST be uppercase ASCII. Each
MUST start with `A-Z`; following characters are `A-Z`, `0-9`, or `-`. A version
MUST start with `0-9`; following characters are ASCII letters, digits, `.`, or
`-`. A namespace is limited to 63 characters and a name to 128 characters.

The separators have exactly one meaning: `:` separates named components and
`@` introduces their versions. Percent encoding, URL normalization, Unicode
normalization, and case folding MUST NOT be applied. An address containing
whitespace or extra components is invalid.

Examples:

```text
KA:MO@1
KA:MO@1:YAML@1
ACME:AMAZON-TO-PURCHASE@1
```

The same `resource-address` syntax is used for Contract, Processor, and
Composition addresses. The
descriptor kind and resolution context determine resource type; the spelling
of the address does not.

### 5.2 Address properties

An address is a compact symbolic reference. It is not a URL, does not imply
HTTP, and can be parsed and compared offline. Exact byte-for-byte equality of
canonical address strings is the v0 symbolic equality rule.

## 6. Identity, publication, and immutability

A symbolic address MUST NOT be the sole source of hard identity. Published,
versioned resources carry:

- `namespace_id`: immutable UUID for the authority;
- `family_id`: immutable UUID for the resource family;
- `version_id`: immutable UUID for this published version.

Representation Bindings additionally carry `binding_id` and
`binding_version_id` because the binding has a version lineage distinct from
its parent Contract Version.

The tuple `(namespace_id, family_id, version_id)` identifies a published
resource version. A resolver MUST reject a result when those IDs do not match
the requester's constraints. Once published, a Contract Version, Processor
Version, or Representation Binding Version MUST be immutable.

A publisher MUST NOT silently retarget a symbolic address to a semantically
different immutable version. Corrections that change normative meaning require
a new address and `version_id`. Mirrors MAY serve identical content under the
same identity.

Core descriptors do not contain a digest of their own serialized bytes. A
catalog, manifest, or publication record MAY identify a descriptor with the
SHA-256 digest of its exact published bytes. That external record MUST also make
the serialization or media type clear. Core deliberately defines no cross-YAML/
JSON canonicalization algorithm.

An `artifact.digest` hashes the exact bytes of the resource named by
`artifact.ref`. If the reference contains a URI fragment, the digest still
hashes the complete resource bytes with the fragment removed; the fragment is
applied only after digest verification to select a subresource. A `definition`
digest has the same exact-byte meaning and is valid only with `definition.ref`.
ProcessorImplementation descriptors MUST digest their executable artifact.
Representation artifacts support the same mechanism. Receipts MAY digest exact
input and output value bytes. SHA-256 is the only Core v0 algorithm.

## 7. Namespaces and resolution

A Namespace descriptor contains a human-friendly `alias` and immutable
`namespace_id`. It MAY include authority metadata and resolver hints. The alias
is convenient routing input; the ID is the stable authority identity.

Identity, authority, and resolution are separate concerns. Resolution is
pluggable and MAY use embedded manifests, local registries, filesystems, Git,
HTTP, enterprise registries, signed catalogs, or DNS-assisted discovery. Core
mandates neither a central registry nor DNS. A resolver SHOULD support pinned
IDs and digests, offline catalogs, dependency traversal, and stale-result
detection.

Global alias registration, ownership proof, and delegation are outside v0.
Private aliases can therefore collide. A resolver MUST surface an ambiguous
alias rather than silently choose an authority.

## 8. Contracts

A Contract is a named semantic boundary, not merely a structural schema. Its
definition MAY contain normative prose, formal assertions, external-standard
references, examples, fixtures, test vectors, dependencies, and compatibility
relations.

A Contract descriptor MUST contain:

- `address`;
- `namespace_id`;
- `family_id`;
- `version_id`;
- `version`; and
- a normative `definition` body or reference.

It SHOULD contain a description. It MAY list Representation Bindings,
dependencies, relationships, and conformance material.

The `version` field MUST equal the version token in `address`. All versions of
one Contract Family MUST retain the same `namespace_id` and `family_id`, while
each immutable version MUST have a distinct `version_id`.

Two schemas with identical shape do not become semantically interchangeable.
For example, `ACME:MONEY@1` and `BANK:BALANCE@1` remain distinct unless their
identity or an explicit relationship/Processor connects them.

## 9. Representation Bindings

A semantic Contract Version MAY have multiple Representation Bindings. A
binding descriptor MUST identify:

- its binding address;
- its parent Contract address and `version_id`;
- its binding name and binding version;
- immutable binding identity; and
- a representation descriptor, schema, or artifact.

It SHOULD identify media type and syntax version. A referenced representation
artifact SHOULD carry its exact-byte digest. The binding version belongs to the
Contract-to-representation binding. `YAML@1` means "the first YAML binding for
this Contract," not "YAML specification version 1."

Bindings MAY reference JSON Schema, XML Schema, RDF/SHACL, Protobuf, OpenAPI,
AsyncAPI, WIT, ODCS, PDPP schemas, UNTP models, or other standards. SPEC MUST
NOT duplicate features adequately defined by those standards.

Representation conversion is itself semantic processing when it can affect
meaning. A Composer MUST NOT invent an implicit conversion merely because two
bindings use structurally compatible schemas.

## 10. Dependencies and relationships

Contract dependencies MUST be explicit symbolic references. A resolver MAY
resolve them transitively. Dependency cycles are invalid in Core unless a
future profile gives those cycles semantics.

Core relation names are deliberately small:

- `equivalent-to`
- `compatible-with`
- `extends`
- `specializes`
- `supersedes`
- `derived-from`

`equivalent-to` is symmetric. `compatible-with` is directional from the
declaring Contract to the target unless `direction: both` is present.
`extends`, `specializes`, `supersedes`, and `derived-from` are descriptive and
MUST NOT alone authorize substitution in v0.

Version numbers do not imply compatibility. A Composer MAY use only exact
immutable Contract identity, an applicable explicit `equivalent-to` or
`compatible-with` relation, an explicit adapting Processor, or a compatibility
mechanism enabled by an optional profile.

## 11. Processors and implementations

A Processor is an independently addressable, implementation-neutral semantic
processing boundary. Its descriptor MUST declare `inputs` and `outputs`; at
least one of the two lists MUST be non-empty. Each port references a semantic
Contract and MAY constrain accepted Representation Bindings.

```yaml
spec: "0.1-alpha"
kind: Processor
address: ACME:NORMALIZE@1
inputs:
  - name: source
    contract: ACME:RAW-INVOICE@1
outputs:
  - name: invoice
    contract: SPECX:INVOICE@1
```

For SPEC purposes, the declaration is one atomic processing unit. "Atomic"
describes the declared boundary only. It does not promise database
transactionality, rollback, exactly-once delivery, isolation, or distributed
atomicity.

An implementation is a separate descriptor bound to a Processor Version. It
MAY be a Wasm/WIT component, function, native binary, HTTP service, MCP tool,
container, SQL statement, AI agent, policy engine, workflow node, or generated
code. A host selects an implementation whose declared capabilities satisfy the
Processor, data binding, state, effect, trust, and locality constraints.

Resolving a Processor declaration never authorizes resolving or executing one
of its implementations.

## 12. State ports, effects, and transactions

### 12.1 State ports

Material state dependencies MUST be visible at the Processor boundary. A State
Port has a name, semantic Contract, and access mode. Core access modes are:

- `read`
- `write`
- `read-write`

The optional v0 modes `append` and `delete` are also reserved. A host MAY report
them as unsupported. Storage implementation is outside SPEC. A runtime can bind
a port to memory, a Kalo Store, PostgreSQL, Redis, an event log, or a remote
service without changing the Processor's semantic declaration.

### 12.2 Effects

A Processor SHOULD declare:

- `safe`: execution is intended not to change externally observable semantic
  state;
- `idempotent`: repeated execution with the same semantic inputs is intended to
  have the same semantic effect as one execution; and
- `open_world`: execution can materially affect resources outside declared
  outputs and State Ports.

Absence means unknown, not `false`. These properties describe intended semantic
effects, not incidental implementation activity such as metrics or logging.
Sending email, charging a card, and modifying an undeclared remote resource are
open-world effects. Planners and hosts SHOULD require explicit policy approval
for unknown or open-world effects.

### 12.3 Transactions

An implementation MAY attach a coarse local-state transaction declaration, but
Core does not standardize distributed transactions, locks, MVCC, two-phase
commit, isolation levels, rollback mechanisms, or exactly-once execution.

## 13. Composition and planning

Composition is a first-class directed acyclic graph. A node references a
Processor; an edge connects one declared output port to one declared input port
and records the semantic Contract at that boundary. A linear route is the
smallest DAG. Core does not require the term "pipeline."

Given `P1: A -> B` and `P2: B -> C`, a Composer MAY derive
`A -> P1 -> B -> P2 -> C` only if every compatibility check succeeds.

For each proposed edge, a Composer MUST verify:

1. the output and input have exact immutable Contract identity, or an explicit
   relation/profile authorizes substitution in the required direction;
2. a concrete binding accepted by both ports exists, or an explicit Processor
   performs representation conversion;
3. every required State Port can be bound with sufficient access;
4. effect declarations are known and permitted by host policy;
5. a selected implementation satisfies required mechanism, media type,
   capability, trust, and locality constraints; and
6. no descriptor constraint is contradicted.

Structural similarity alone MUST NOT satisfy step 1 or 2. Unknown information
MUST NOT be treated as compatible; a Composer returns an inspectable
incompatibility instead.

Core supports linear graphs, DAG graphs, and transitive route discovery.
Planner algorithms are outside v0. A planner MAY rank valid routes using cost,
latency, trust, determinism, locality, provenance quality, policy, accuracy, or
implementation preferences. The chosen route SHOULD be serializable,
inspectable, pinned to immutable identities, and reproducible.

## 14. Receipts and provenance

A Receipt records one execution or a composed execution without depending on a
runtime. It MUST identify the receipt and subject and MUST record input and
output semantic identities. It SHOULD include:

- Processor address and version identity;
- implementation identity and executable artifact digest when one was used;
- input and output Contract identities, bindings, and artifact digests;
- start and end timestamps;
- execution status;
- State Port interactions at an appropriate disclosure level;
- parent receipt IDs; and
- the selected route for a composition.

Receipts for stages MAY be linked by `parent_receipts` and collected under a
composition Receipt. An output artifact digest from one stage SHOULD reappear
as the input artifact digest of the consuming stage. A Receipt is evidence of a
claim, not proof that the claim is honest; signing and evidence profiles are
future work.

## 15. Capabilities and conformance

An implementation is not required to support every SPEC feature. Core defines
these conformance classes:

- **Core Consumer** — parses, validates, and preserves Core descriptors;
- **Core Publisher** — publishes immutable, identified Core resources;
- **Resolver** — resolves symbolic references with identity checks;
- **Representation Handler** — reads or writes declared bindings;
- **Processor Descriptor Publisher** — publishes Processor declarations;
- **Processor Host** — invokes selected implementations;
- **Composer** — validates and executes declared compositions;
- **Planner** — discovers valid transitive routes;
- **State-Capable Host** — binds named State Ports;
- **Provenance Producer** — emits conforming Receipts.

Implementations SHOULD advertise version and capabilities, for example:

```yaml
spec: "0.1-alpha"
capabilities:
  core: true
  resolution: true
  processing: true
  composition: true
  planning: false
  state: false
  provenance: true
```

An implementation MUST reject a descriptor whose Core version it cannot
process safely. It MAY support a strict subset through declared conformance
classes, but MUST NOT claim a class whose required behavior it lacks.

## 16. Extensions

Extensions live under the `extensions` map and use keys of the form
`NAMESPACE:NAME`. Unknown optional extensions SHOULD be preserved and ignored.
`required_extensions` lists extension keys whose semantics are required.

If an implementation does not understand a listed required extension, it MUST
report explicit incompatibility and MUST NOT execute or republish the resource
as if fully understood. Extensions MUST NOT redefine Core fields or weaken Core
security and identity requirements.

## 17. Security considerations

Resolving a Contract does not grant permission to execute code associated with
it. Contract trust, Namespace trust, Processor trust, implementation trust,
execution authorization, and data authorization are independent decisions.

Implementations MUST account for:

- namespace spoofing and alias collision;
- malicious or misleading Processor descriptors;
- malicious executable implementations and arbitrary code execution;
- dependency substitution and confused-deputy resolution;
- poisoned registries and compromised resolver hints;
- stale resources and revoked trust;
- forged, replayed, or selectively incomplete Receipts;
- undeclared or unsafe side effects;
- digest target confusion and canonicalization mismatch; and
- denial of service through resolution graphs, schemas, or execution.

Resolvers SHOULD pin immutable IDs and digests, impose traversal and size
limits, detect dependency cycles, and retain source provenance. Hosts SHOULD
sandbox implementations, use least authority, validate bindings, enforce state
and effect policy, and require separate user or policy authorization before
open-world execution. Receipt consumers SHOULD verify signatures when a signing
profile is in use and MUST NOT treat an unsigned Receipt as inherently trusted.

## 18. Relationship to WIT and WebAssembly Components

SPEC describes the semantic boundary and transformation claim. WIT describes
an executable component interface and ABI. A Wasm component is one executable
implementation. The layers are complementary:

```text
SPEC semantic Contract and Processor declaration
                     |
WIT executable component interface
                     |
WebAssembly component
```

SPEC MUST NOT duplicate WIT. Hosts, including Kalo, MAY select WIT/Wasm as an
implementation mechanism while retaining runtime-neutral SPEC identity.

## 19. Relationship to semantic-web reasoning

Core composition is nominal and explicit: a Processor declares `A -> B`, a
second declares `B -> C`, and a Composer may derive `A -> C`. Core does not
require OWL-S-, WSMO-, or AI-style inferential composition.

Optional future profiles MAY add ontology-driven compatibility, inferred
subtyping, formal preconditions, normative or legal semantics, or semantic
mediation. Such profiles must remain optional and must identify every inference
used in an inspectable plan or Receipt.

## 20. Integration boundaries

### 20.1 PDP-Connect

A PDPP bridge is external to PDPP Core. It associates a PDPP source, stream, or
schema with a Contract; references the PDPP JSON Schema through a Representation
Binding; declares semantic transformations; and propagates source identity,
version, and digest into Receipts. It does not redefine PDPP consent, grants,
servers, authentication, collection, or connector runtime behavior.

The v0 stress test has independent Amazon and DoorDash source Contracts, both
normalizing to `SPECX:PURCHASE@1`, followed by
`SPECX:PURCHASE@1 -> SPECX:SPEND-EVENT@1`. A Shop source proves that adding a
source requires one new source-to-Purchase Processor and no downstream change.

### 20.2 Kalo

Kalo concepts map approximately to SPEC as follows, but this mapping is not
normative:

| Kalo | SPEC |
| --- | --- |
| Spec | Contract |
| Format | Representation Binding |
| Plugin | Processor implementation |
| Pipeline | Composition implementation |
| Store | State Port runtime binding |
| runtime | Processor Host and Composer |

No conforming implementation needs to import Kalo code.

## 21. v0 non-goals

Core v0 does not define a universal ontology or semantic DSL, central registry,
DNS protocol, Processor marketplace, mandatory Wasm runtime, workflow language,
storage API, query language, distributed transaction standard, policy engine,
trust framework, billing system, AI-agent framework, mandatory formal
reasoning, or normative/legal logic language.

## 22. Minimum useful implementations

The smallest useful Core implementation supports Namespace descriptors,
Contract identity and addresses, immutable Contract versions, Representation
Bindings, SHA-256 digest verification, and descriptor parsing.

The first useful processing implementation additionally supports Processor
descriptors, inputs and outputs, State Ports, effects, compatibility checking,
linear and DAG composition, transitive route discovery, and Receipts.
