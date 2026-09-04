from __future__ import annotations

import copy
import unittest

import conformance


class ConformanceSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = conformance.load_suite()
        cls.report = conformance.run_reference(
            cls.suite, "SPEC reference conformance oracle", "test"
        )

    def test_reference_report_is_valid_and_makes_no_claims(self) -> None:
        conformance.verify_report(self.report, self.suite)
        self.assertEqual([], self.report["claims"])
        self.assertEqual(0, self.report["summary"]["fail"])
        self.assertGreater(self.report["summary"]["not_run"], 0)

    def test_claim_requires_every_class_test_to_pass(self) -> None:
        report = copy.deepcopy(self.report)
        report["claims"] = ["Core Consumer"]
        with self.assertRaisesRegex(conformance.ConformanceFailure, "non-passing"):
            conformance.verify_report(report, self.suite)

    def test_claim_passes_when_every_required_test_has_evidence(self) -> None:
        report = copy.deepcopy(self.report)
        required = next(
            item["required_tests"]
            for item in self.suite["classes"]
            if item["name"] == "Core Consumer"
        )
        results = {item["test_id"]: item for item in report["results"]}
        for test_id in required:
            results[test_id]["status"] = "pass"
            results[test_id]["evidence"] = ["implementation:test-output"]
        report["claims"] = ["Core Consumer"]
        report["summary"] = conformance.count_results(report["results"])
        conformance.verify_report(report, self.suite)

    def test_uncovered_class_cannot_be_claimed(self) -> None:
        report = copy.deepcopy(self.report)
        report["claims"] = ["Composer"]
        with self.assertRaisesRegex(conformance.ConformanceFailure, "does not yet cover"):
            conformance.verify_report(report, self.suite)

    def test_passing_result_requires_evidence(self) -> None:
        report = copy.deepcopy(self.report)
        passing = next(item for item in report["results"] if item["status"] == "pass")
        passing.pop("evidence")
        with self.assertRaisesRegex(conformance.ConformanceFailure, "has no evidence"):
            conformance.verify_report(report, self.suite)

    def test_report_must_cover_every_suite_test_once(self) -> None:
        report = copy.deepcopy(self.report)
        report["results"].pop()
        report["summary"] = conformance.count_results(report["results"])
        with self.assertRaisesRegex(conformance.ConformanceFailure, "coverage mismatch"):
            conformance.verify_report(report, self.suite)

    def test_normative_requirements_are_fully_accounted(self) -> None:
        catalog = conformance.audit_requirements(self.suite)
        self.assertEqual(41, catalog["summary"]["total"])
        self.assertEqual(43, catalog["source"]["normative_keyword_occurrences"])

    def test_requirements_reject_unknown_suite_test(self) -> None:
        catalog = conformance.load_json(conformance.REQUIREMENTS_PATH)
        catalog["requirements"][0]["test_ids"] = ["CV-NOT-REAL"]
        original = conformance.load_json
        try:
            conformance.load_json = lambda path: (
                catalog if path == conformance.REQUIREMENTS_PATH else original(path)
            )
            with self.assertRaisesRegex(conformance.ConformanceFailure, "unknown test IDs"):
                conformance.load_requirements(self.suite)
        finally:
            conformance.load_json = original

    def test_requirements_reject_incorrect_summary(self) -> None:
        catalog = conformance.load_json(conformance.REQUIREMENTS_PATH)
        catalog["summary"]["tested"] += 1
        original = conformance.load_json
        try:
            conformance.load_json = lambda path: (
                catalog if path == conformance.REQUIREMENTS_PATH else original(path)
            )
            with self.assertRaisesRegex(conformance.ConformanceFailure, "summary"):
                conformance.load_requirements(self.suite)
        finally:
            conformance.load_json = original

    def test_requirements_reject_unaccounted_normative_occurrence(self) -> None:
        catalog = conformance.load_json(conformance.REQUIREMENTS_PATH)
        catalog["requirements"].pop()
        original = conformance.load_json
        try:
            conformance.load_json = lambda path: (
                catalog if path == conformance.REQUIREMENTS_PATH else original(path)
            )
            with self.assertRaisesRegex(conformance.ConformanceFailure, "coverage mismatch"):
                conformance.load_requirements(self.suite)
        finally:
            conformance.load_json = original


if __name__ == "__main__":
    unittest.main()
