# Task spec-c004-requirements-traceability C01 Plan

## Goal
Inventory normative MUST requirements and verify coverage

## Description
Create a bounded implementation slice for `Create SPEC v0.1-alpha normative requirements traceability matrix and omission checker`. This plan is grounded by the task index preflight, but it is not authoritative; confirm predicted files and tests before making edits.

## Resources
- `C00-index.md`
- `C01-inventory-atomic-must-requirements-and-verify-co-result.md`
- `task.json`
- `tools/conformance.py`
- `tools/test_conformance.py#L17`
- `spec.md`
- `conformance/v0.1-alpha/suite.json`

## Starting Context
### Files to Inspect First
- `tools/conformance.py`
- `spec.md`
- `conformance/v0.1-alpha/suite.json`

### Tests to Inspect First
- `tools/test_conformance.py#L17`

## Expected Change Surface
- `tools/conformance.py`
- `tools/test_conformance.py`
- `conformance/v0.1-alpha/requirements.json`
- `conformance/v0.1-alpha/requirements.schema.json`
- `conformance/v0.1-alpha/REQUIREMENTS.md`
- `.github/workflows/validate.yml`
- conformance documentation

## Out-of-Scope Areas
- New descriptor fields, resources, or normative protocol behavior.
- Converting the draft suite or Kalo self-assessment into certification.
- Filling every identified gap in this exercise.

## Risks
- Pack completeness is not high; verify the working set before editing.

## Success Criteria
- [x] Primary implementation surface is verified before edits.
- [x] All 43 uppercase MUST/MUST NOT occurrences are mapped or explicitly excluded.
- [x] Every normative entry has a stable ID, applicability, disposition, and verification path.
- [x] Referenced suite tests and summary totals are mechanically checked.
- [x] A stale source digest or generated matrix fails the audit.
- [x] Per-class readiness counts expose partial, inspection, and deferred gaps.
- [x] Normative protocol files and descriptor schemas remain unchanged.
- [x] Changes stay inside the bounded conformance traceability slice.
- [x] A checkpoint records actual files, tests, misses, noise, and decision.

## Tasks
- [x] Inspect the normative specification, suite, runner, and runner tests.
- [x] Refine the slice to a machine catalog plus generated human matrix.
- [x] Classify all normative keyword occurrences without inventing passes.
- [x] Add omission, source-digest, test-reference, summary, and staleness checks.
- [x] Add CI enforcement and documentation.
- [x] Run the full validator, conformance oracle, unit tests, and requirements audit.
- [x] Update `C01-inventory-atomic-must-requirements-and-verify-co-result.md` or run `ds task checkpoint`.

## Decision Gates
- Promote: the workspace was useful enough and misses are actionable.
- Improve: useful start, but incomplete/noisy enough to require template or retrieval changes.
- Rework: task workspace feels like planning overhead or fails to capture useful evidence.
- Rollback: workspace creates false confidence or worsens agent performance.
- Block: external input or a missing prerequisite prevents useful progress.
