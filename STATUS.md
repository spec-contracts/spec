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
- [ ] Kalo can consume the descriptors.
- [x] PDPP experiment passes in an executable host.
- [x] Third-source descriptor demonstrates downstream route reuse.
- [x] PDPP bridge can be explained in no more than three pages.
- [x] The bridge design requires no PDPP Core modification.
- [x] No Kalo-specific concept is required by the standard.
- [ ] At least one independent technical reviewer has reviewed the design.

## Current milestone

The repository is at the **v0.1 descriptor-design baseline**. Executable Kalo
evidence for the Amazon, DoorDash, and held-out Shop routes is preserved in
[`kalo-build/kalo-pdpp-spec`](https://github.com/kalo-build/kalo-pdpp-spec).
The next milestone is a native Kalo adapter that loads the example catalog,
derives the two-stage routes, and emits receipts without changing PDP-Connect
Core.
