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
- [ ] PDP-Connect experiment passes through the native Kalo path.
- [ ] Held-out third source reuses the frozen downstream executable path.
- [x] PDPP bridge can be explained in no more than three pages.
- [x] The bridge design requires no PDPP Core modification.
- [x] No Kalo-specific concept is required by the standard.
- [ ] At least one independent technical reviewer has reviewed the design.

## Current milestone

The repository is at the **v0.1-alpha conceptual freeze**. Native Kalo evidence
for the Amazon, DoorDash, and held-out Shop routes is being rebuilt in
[`kalo-build/kalo-pdpp-spec`](https://github.com/kalo-build/kalo-pdpp-spec).
The next gate is to freeze the Amazon and DoorDash common path, add Shop only
after that freeze, and independently verify Kalo-generated Receipts without
changing PDP-Connect Core.
