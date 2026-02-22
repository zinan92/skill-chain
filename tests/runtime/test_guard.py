"""Unit tests for core/helpers/guard.py — transition guard checks.

Tests all 6 guard functions with valid, invalid, and edge-case inputs.
Covers invariants: commit gate, verify gate, guard-fail-blocks-transition.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

# Add project root to path so we can import guard
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core", "helpers"))
import guard

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


class TestCheckTriage(unittest.TestCase):
    """Guard: triage step must produce valid weight + type + summary."""

    def setUp(self):
        self._orig_dir = guard.WORKFLOW_DIR
        guard.WORKFLOW_DIR = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(guard.WORKFLOW_DIR, ignore_errors=True)
        guard.WORKFLOW_DIR = self._orig_dir

    def test_valid_triage_passes(self):
        data = load_fixture("valid_triage.json")
        result = guard.check_triage(data)
        self.assertEqual(result["weight"], "Medium")
        self.assertEqual(result["type"], "feat")

    def test_valid_light_triage_passes(self):
        data = load_fixture("valid_triage_light.json")
        result = guard.check_triage(data)
        self.assertEqual(result["weight"], "Light")

    def test_valid_heavy_triage_passes(self):
        data = load_fixture("valid_triage_heavy.json")
        result = guard.check_triage(data)
        self.assertEqual(result["weight"], "Heavy")

    def test_invalid_weight_fails(self):
        data = {"type": "feat", "weight": "Extreme", "summary": "A valid summary"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_weight_fails(self):
        data = {"type": "feat", "summary": "A valid summary"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_empty_weight_fails(self):
        data = {"type": "feat", "weight": "", "summary": "A valid summary"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_invalid_type_fails(self):
        data = {"type": "", "weight": "Light", "summary": "A valid summary"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_short_type_fails(self):
        data = {"type": "x", "weight": "Light", "summary": "A valid summary"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_type_fails(self):
        data = {"weight": "Light", "summary": "A valid summary"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_short_summary_fails(self):
        data = {"type": "feat", "weight": "Light", "summary": "Hi"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_summary_fails(self):
        data = {"type": "feat", "weight": "Light"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_triage(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_saves_checkpoint(self):
        data = load_fixture("valid_triage.json")
        guard.check_triage(data)
        cp = guard.load_checkpoint("triage")
        self.assertIsNotNone(cp)
        self.assertEqual(cp["weight"], "Medium")


class TestCheckRoute(unittest.TestCase):
    """Guard: route must carry triage; plan required for Medium/Heavy."""

    def setUp(self):
        self._orig_dir = guard.WORKFLOW_DIR
        guard.WORKFLOW_DIR = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(guard.WORKFLOW_DIR, ignore_errors=True)
        guard.WORKFLOW_DIR = self._orig_dir

    def test_light_without_plan_passes(self):
        data = {
            "triage": load_fixture("valid_triage_light.json"),
            "plan": None,
            "context": "Light task"
        }
        result = guard.check_route(data)
        self.assertIsNone(result["plan"])

    def test_medium_with_plan_passes(self):
        data = {
            "triage": load_fixture("valid_triage.json"),
            "plan": {"files_to_modify": [{"path": "a.py", "action": "modify", "description": "change"}]},
            "context": "Medium task"
        }
        result = guard.check_route(data)
        self.assertIsNotNone(result["plan"])

    def test_heavy_with_plan_passes(self):
        data = {
            "triage": load_fixture("valid_triage_heavy.json"),
            "plan": {"files_to_modify": [{"path": "a.py", "action": "create", "description": "new file"}]},
            "context": "Heavy task"
        }
        result = guard.check_route(data)
        self.assertIsNotNone(result["plan"])

    def test_medium_without_plan_fails(self):
        """INVARIANT: Medium/Heavy must not bypass planning."""
        data = {
            "triage": load_fixture("valid_triage.json"),
            "plan": None,
            "context": "Medium task"
        }
        with self.assertRaises(SystemExit) as ctx:
            guard.check_route(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_heavy_without_plan_fails(self):
        """INVARIANT: Medium/Heavy must not bypass planning."""
        data = {
            "triage": load_fixture("valid_triage_heavy.json"),
            "plan": None,
            "context": "Heavy task"
        }
        with self.assertRaises(SystemExit) as ctx:
            guard.check_route(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_triage_fails(self):
        data = {"plan": None, "context": "No triage"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_route(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_medium_with_error_fails(self):
        data = {
            "triage": load_fixture("valid_triage.json"),
            "plan": None,
            "error": "Planning subprocess crashed",
            "context": "Medium task"
        }
        with self.assertRaises(SystemExit) as ctx:
            guard.check_route(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_saves_checkpoint(self):
        data = {
            "triage": load_fixture("valid_triage_light.json"),
            "plan": None,
            "context": "Light"
        }
        guard.check_route(data)
        cp = guard.load_checkpoint("route")
        self.assertIsNotNone(cp)


class TestCheckImplement(unittest.TestCase):
    """Guard: implementation must produce files and a summary."""

    def setUp(self):
        self._orig_dir = guard.WORKFLOW_DIR
        guard.WORKFLOW_DIR = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(guard.WORKFLOW_DIR, ignore_errors=True)
        guard.WORKFLOW_DIR = self._orig_dir

    def test_valid_implement_passes(self):
        data = load_fixture("valid_implement.json")
        result = guard.check_implement(data)
        self.assertIn("src/form.py", result["files_changed"])

    def test_files_created_only_passes(self):
        data = {
            "summary": "Created new module",
            "files_changed": [],
            "files_created": ["src/new_module.py"]
        }
        result = guard.check_implement(data)
        self.assertEqual(result["files_created"], ["src/new_module.py"])

    def test_no_files_fails(self):
        data = {"summary": "Did nothing", "files_changed": [], "files_created": []}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_implement(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_files_keys_fails(self):
        data = {"summary": "Did something"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_implement(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_summary_fails(self):
        data = {"files_changed": ["a.py"], "files_created": []}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_implement(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_error_field_fails(self):
        data = {
            "summary": "Partial work",
            "files_changed": ["a.py"],
            "files_created": [],
            "error": "Compilation failed"
        }
        with self.assertRaises(SystemExit) as ctx:
            guard.check_implement(data)
        self.assertEqual(ctx.exception.code, 1)


class TestCheckReview(unittest.TestCase):
    """Guard: INVARIANT — review.verdict != approved must block commit."""

    def setUp(self):
        self._orig_dir = guard.WORKFLOW_DIR
        guard.WORKFLOW_DIR = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(guard.WORKFLOW_DIR, ignore_errors=True)
        guard.WORKFLOW_DIR = self._orig_dir

    def test_approved_passes(self):
        data = load_fixture("valid_review_approved.json")
        result = guard.check_review(data)
        self.assertEqual(result["verdict"], "approved")

    def test_rejected_fails(self):
        """INVARIANT: rejected review must block pipeline."""
        data = load_fixture("valid_review_rejected.json")
        with self.assertRaises(SystemExit) as ctx:
            guard.check_review(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_with_fixes_fails(self):
        """INVARIANT: with_fixes review must block pipeline."""
        data = load_fixture("valid_review_with_fixes.json")
        with self.assertRaises(SystemExit) as ctx:
            guard.check_review(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_unknown_verdict_fails(self):
        data = {"verdict": "maybe", "summary": "Unclear result"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_review(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_verdict_fails(self):
        data = {"summary": "No verdict given"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_review(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_none_verdict_fails(self):
        data = {"verdict": None, "summary": "Null verdict"}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_review(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_saves_checkpoint_on_approved(self):
        data = load_fixture("valid_review_approved.json")
        guard.check_review(data)
        cp = guard.load_checkpoint("review")
        self.assertIsNotNone(cp)
        self.assertEqual(cp["verdict"], "approved")


class TestCheckVerify(unittest.TestCase):
    """Guard: INVARIANT — verify not passed must block commit."""

    def setUp(self):
        self._orig_dir = guard.WORKFLOW_DIR
        guard.WORKFLOW_DIR = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(guard.WORKFLOW_DIR, ignore_errors=True)
        guard.WORKFLOW_DIR = self._orig_dir

    def test_valid_verify_passes(self):
        data = load_fixture("valid_verify.json")
        result = guard.check_verify(data)
        self.assertTrue(result["verified"])

    def test_verified_false_fails(self):
        """INVARIANT: unverified must block pipeline."""
        data = {"verified": False, "evidence": "Tests failed: 2 errors", "tests_passed": False}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_verify(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_verified_missing_fails(self):
        data = {"evidence": "Some evidence here", "tests_passed": True}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_verify(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_verified_string_true_fails(self):
        """verified must be boolean true, not string 'true'."""
        data = {"verified": "true", "evidence": "Tests pass with evidence", "tests_passed": True}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_verify(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_short_evidence_fails(self):
        data = {"verified": True, "evidence": "ok", "tests_passed": True}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_verify(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_empty_evidence_fails(self):
        data = {"verified": True, "evidence": "", "tests_passed": True}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_verify(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_tests_failed_blocks(self):
        """INVARIANT: tests_passed=false must block even if verified=true."""
        data = {"verified": True, "evidence": "Tests ran but some failed badly", "tests_passed": False}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_verify(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_saves_checkpoint(self):
        data = load_fixture("valid_verify.json")
        guard.check_verify(data)
        cp = guard.load_checkpoint("verify")
        self.assertIsNotNone(cp)
        self.assertTrue(cp["verified"])


class TestCheckPreCommit(unittest.TestCase):
    """Guard: INVARIANT — aggregate triple gate must all pass before commit."""

    def setUp(self):
        self._orig_dir = guard.WORKFLOW_DIR
        guard.WORKFLOW_DIR = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(guard.WORKFLOW_DIR, ignore_errors=True)
        guard.WORKFLOW_DIR = self._orig_dir

    def _setup_checkpoints(self, review=True, verify=True, implement=True):
        """Write checkpoint files to simulate prior pipeline steps."""
        if review:
            guard.save_checkpoint("review", load_fixture("valid_review_approved.json"))
        if verify:
            guard.save_checkpoint("verify", load_fixture("valid_verify.json"))
        if implement:
            guard.save_checkpoint("implement", load_fixture("valid_implement.json"))

    def test_all_gates_pass(self):
        self._setup_checkpoints()
        data = load_fixture("valid_implement.json")
        result = guard.check_pre_commit(data)
        self.assertIn("files_changed", result)

    def test_missing_review_fails(self):
        """INVARIANT: no review checkpoint = review was skipped = block."""
        self._setup_checkpoints(review=False)
        data = load_fixture("valid_implement.json")
        with self.assertRaises(SystemExit) as ctx:
            guard.check_pre_commit(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_verify_fails(self):
        """INVARIANT: no verify checkpoint = verify was skipped = block."""
        self._setup_checkpoints(verify=False)
        data = load_fixture("valid_implement.json")
        with self.assertRaises(SystemExit) as ctx:
            guard.check_pre_commit(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_implement_fails(self):
        self._setup_checkpoints(implement=False)
        data = {}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_pre_commit(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_rejected_review_in_checkpoint_fails(self):
        """INVARIANT: even if checkpoint exists, verdict must be approved."""
        guard.save_checkpoint("review", {"verdict": "rejected", "summary": "bad"})
        guard.save_checkpoint("verify", load_fixture("valid_verify.json"))
        guard.save_checkpoint("implement", load_fixture("valid_implement.json"))
        data = load_fixture("valid_implement.json")
        with self.assertRaises(SystemExit) as ctx:
            guard.check_pre_commit(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_unverified_in_checkpoint_fails(self):
        """INVARIANT: even if checkpoint exists, verified must be true."""
        guard.save_checkpoint("review", load_fixture("valid_review_approved.json"))
        guard.save_checkpoint("verify", {"verified": False, "evidence": "Failed"})
        guard.save_checkpoint("implement", load_fixture("valid_implement.json"))
        data = load_fixture("valid_implement.json")
        with self.assertRaises(SystemExit) as ctx:
            guard.check_pre_commit(data)
        self.assertEqual(ctx.exception.code, 1)

    def test_all_missing_reports_multiple_failures(self):
        """All three checkpoints missing should report 3 failures."""
        data = {}
        with self.assertRaises(SystemExit) as ctx:
            guard.check_pre_commit(data)
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
