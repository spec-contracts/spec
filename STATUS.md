# SPEC v0 status

This checklist tracks readiness for external review. A checked item means the
repository contains a reviewable artifact or a verified experiment result; it
does not mean the protocol is final.

- [x] Core descriptor grammar exists.
- [x] Address parsing is deterministic.
- [x] Namespace and immutable identity behavior is defined.
- [x] Contract descriptor exists.
- [x] Representation Binding descriptor exists.
- [x] Processor descriptor exists.
- [x] Minimal effects and state vocabulary exists.
- [x] Composition compatibility rules exist.
- [x] Minimal Receipt exists.
- [x] Kalo can consume the descriptors through native `kalo spec` commands.
- [x] PDP-Connect experiment passes through the native Kalo path.
- [x] Held-out third source reuses the frozen downstream executable path.
- [x] PDPP bridge can be explained in no more than three pages.
- [x] The bridge design requires no PDPP Core modification.
- [x] No Kalo-specific concept is required by the standard.
- [x] A draft implementation-independent conformance self-assessment suite exists.
- [ ] At least one independent technical reviewer has reviewed the design.

## Current milestone

The repository is at the **v0.1-alpha conceptual freeze**. Native Kalo evidence
for Amazon and DoorDash was frozen first at
[`spec-v0.1-alpha-common-freeze`](https://github.com/kalo-build/kalo-pdpp-spec/tree/spec-v0.1-alpha-common-freeze).
Held-out Shop was then added at
[`spec-v0.1-alpha-pdpp-evidence`](https://github.com/kalo-build/kalo-pdpp-spec/tree/spec-v0.1-alpha-pdpp-evidence)
without changing the frozen Purchase-to-SpendEvent path. Kalo generated the
Receipts and an independent verifier checked all three routes. The remaining
gate is independent external technical review; implementation work stops here
until that feedback exists.

The draft conformance suite packages existing requirements and fixtures without
changing the frozen protocol model. It currently gates six capability classes
and marks four classes explicitly uncovered. Reports are self-assessments and
must not be represented as SPEC certification.
