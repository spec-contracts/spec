# Task spec-c001-spec A01 Plan

## Goal
Freeze v0.1-alpha conceptual model and schemas

## Description
Create a bounded implementation slice for `Freeze v0.1-alpha conceptual model and schemas for workspace change SPEC-C001: SPEC v0.1-alpha external review polish`. This plan is grounded by the task index preflight, but it is not authoritative; confirm predicted files and tests before making edits.

## Workspace Link
```yaml
workspace_id: spec-pdpp-kalo-evidence
workspace_root: "C:\\Users\\brenn\\go\\src\\github.com\\kalo-build\\spec-pdpp-kalo-evidence"
parent_change: SPEC-C001
repo_alias: spec
```

## Resources
- `A00-index.md`
- `A01-freeze-v0-1-alpha-conceptual-model-and-schemas-result.md`
- `task.json`
- `SPEC.md`

## Starting Context
### Files to Inspect First
- No pack-ranked files. Verify checkpoint leads below or search before editing.

### Tests to Inspect First
- No pack-ranked files. Verify checkpoint leads below or search before editing.

## Expected Change Surface
- `README.md`
- `SPEC.md`
- `STATUS.md`
- `GOVERNANCE-NOTES.md`
- `schemas/v0/`
- `examples/pdpp/`
- `fixtures/`
- `docs/pdpp-bridge.md`
- `tools/validate.py`

## Out-of-Scope Areas
- Replanning the whole thread unless evidence says this slice should split or be superseded.
- Broad pack-ranking changes unless they are necessary for this task.
- Treating the generated context as complete without verification.

## Risks
- Primary implementation surface is unknown.
- Relevant tests may be missing from the initial pack.
- Pack completeness is not high; verify the working set before editing.

## Success Criteria
- [ ] Canonical name is Semantic Protocol for Explicit Contracts.
- [ ] Generic primitives use resource-address terminology.
- [ ] Examples use one SPEC-owned SPECX namespace and preserve upstream identity separately.
- [ ] Descriptor digests are external; referenced artifacts have unambiguous exact-byte digests.
- [ ] No YAML/JSON canonicalization or other new protocol surface is introduced.
- [ ] The thin PDP-Connect bridge disclaimer and governance notes are reviewable.
- [ ] Schemas, examples, addresses, identities, and high-value negative fixtures validate.
- [ ] A checkpoint records actual files, tests, misses, noise, and decision.

## Tasks
- [ ] Update canonical naming and alpha status.
- [ ] Tighten address, identity, digest, implementation, and Receipt schemas/prose.
- [ ] Migrate the experiment examples to SPECX without claiming PDP-Connect authority.
- [ ] Add only the nine requested architectural negative cases.
- [ ] Run the independent validator and native Kalo catalog validation.
- [ ] Checkpoint and publish an immutable v0.1-alpha tag without moving v0.1.

## Decision Gates
- Promote: the workspace was useful enough and misses are actionable.
- Improve: useful start, but incomplete/noisy enough to require template or retrieval changes.
- Rework: task workspace feels like planning overhead or fails to capture useful evidence.
- Rollback: workspace creates false confidence or worsens agent performance.
- Block: external input or a missing prerequisite prevents useful progress.
