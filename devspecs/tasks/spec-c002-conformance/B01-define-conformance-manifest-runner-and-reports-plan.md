# Task spec-c002-conformance B01 Plan

## Goal
Define conformance manifest runner and reports

## Description
Create a bounded implementation slice for `Add implementation-independent SPEC v0.1-alpha self-assessed conformance suite without changing protocol surface`. This plan is grounded by the task index preflight, but it is not authoritative; confirm predicted files and tests before making edits.

## Resources
- `B00-index.md`
- `B01-define-conformance-manifest-runner-and-reports-result.md`
- `task.json`
- `SPEC.md`
- `README.md`
- `docs/pdpp-bridge.md`
- `examples/pdpp/README.md`
- `examples/pdpp/bindings/amazon-orders-json.yaml`

## Starting Context
### Files to Inspect First
- No pack-ranked files. Verify checkpoint leads below or search before editing.

### Tests to Inspect First
- No pack-ranked files. Verify checkpoint leads below or search before editing.

### Checkpoint Leads
Verify these prior checkpoint facts before widening search. They are not files the initial pack ranked as primary.
- `README.md` [prior-edited-source] - Verify this prior source lead before choosing an edit target.
  Evidence: task spec-c001-spec checkpoint cp_20260903T142916Z_a01_validated edited `README.md`
- `SPEC.md` [prior-edited-source] - Verify this prior source lead before choosing an edit target.
  Evidence: task spec-c001-spec checkpoint cp_20260903T142916Z_a01_validated edited `SPEC.md`; task spec-c001-spec checkpoint cp_20260903T142916Z_a01_validated learned: Descriptor publication digests live outside self-describing YAML/JSON; artifact fragments select only after whole-resource byte verification
- `docs/pdpp-bridge.md` [prior-edited-source] - Verify this prior source lead before choosing an edit target.
  Evidence: task spec-c001-spec checkpoint cp_20260903T142916Z_a01_validated edited `docs/pdpp-bridge.md`
- `examples/pdpp/README.md` [prior-edited-source] - Verify this prior source lead before choosing an edit target.
  Evidence: task spec-c001-spec checkpoint cp_20260903T142916Z_a01_validated edited `examples/pdpp/README.md`
- `examples/pdpp/bindings/amazon-orders-json.yaml` [prior-edited-source] - Verify this prior source lead before choosing an edit target.
  Evidence: task spec-c001-spec checkpoint cp_20260903T142916Z_a01_validated edited `examples/pdpp/bindings/amazon-orders-json.yaml`

## Expected Change Surface
- `conformance/v0.1-alpha/**` for non-normative suite metadata and report schemas
- `tools/conformance.py` and `tools/test_conformance.py` for the independent runner
- `.github/workflows/validate.yml` for suite self-test coverage
- `README.md` and `STATUS.md` for precise self-assessment language
- `devspecs/tasks/spec-c002-conformance/**` for planning and evidence

## Out-of-Scope Areas
- Replanning the whole thread unless evidence says this slice should split or be superseded.
- Broad pack-ranking changes unless they are necessary for this task.
- Treating the generated context as complete without verification.
- New SPEC resource kinds, fields, execution mechanisms, or certification authority.
- Claiming full coverage for conformance classes without executable tests.

## Risks
- Primary implementation surface is unknown.
- Relevant tests may be missing from the initial pack.
- Pack completeness is not high; verify the working set before editing.

## Success Criteria
- [x] Primary implementation surface is verified before edits.
- [x] Existing validation and executable evidence are mapped to current classes.
- [x] A versioned manifest names every test and its applicable class.
- [x] A runner emits and verifies schema-valid JSON self-assessment reports.
- [x] Claims fail unless every required class test passes.
- [x] Unautomated behaviors are explicit rather than silently counted as passes.
- [x] CI runs suite self-tests without changing protocol schemas or `SPEC.md`.
- [x] Documentation distinguishes conformance self-assessment from certification.
- [x] A checkpoint records actual files, tests, misses, noise, and decision.

## Tasks
- [x] Inspect the normative conformance classes and existing validator/fixtures.
- [x] Refine the slice around tooling rather than protocol changes.
- [x] Add the suite manifest and suite/report schemas.
- [x] Implement report generation, verification, and focused unit tests.
- [x] Add CI and concise usage/claim-boundary documentation.
- [x] Run focused and full validation.
- [x] Checkpoint the completed slice; publish after final verification.

## Decision Gates
- Promote: the workspace was useful enough and misses are actionable.
- Improve: useful start, but incomplete/noisy enough to require template or retrieval changes.
- Rework: task workspace feels like planning overhead or fails to capture useful evidence.
- Rollback: workspace creates false confidence or worsens agent performance.
- Block: external input or a missing prerequisite prevents useful progress.
