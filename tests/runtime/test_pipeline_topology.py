"""Static analysis tests for dev-pipeline.lobster topology.

Parses the pipeline definition and verifies structural invariants
that protect the review-before-commit and verify-before-commit guarantees.
"""
import os
import re
import unittest

import yaml

PIPELINE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "core", "dev-pipeline.lobster"
)


def load_pipeline():
    """Load and parse the pipeline YAML."""
    with open(PIPELINE_PATH) as f:
        return yaml.safe_load(f)


def get_steps(pipeline):
    """Return list of step dicts from pipeline."""
    return pipeline.get("steps", [])


def get_step_ids(steps):
    """Return ordered list of step IDs."""
    return [s["id"] for s in steps]


def get_step_by_id(steps, step_id):
    """Find a step by its ID."""
    for s in steps:
        if s["id"] == step_id:
            return s
    return None


class TestPipelineStructure(unittest.TestCase):
    """Basic pipeline structure checks."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_pipeline()
        cls.steps = get_steps(cls.pipeline)
        cls.step_ids = get_step_ids(cls.steps)

    def test_pipeline_loads(self):
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline["name"], "dev-pipeline")

    def test_has_required_steps(self):
        required = {"init", "triage", "route", "implement", "review", "verify", "pre_commit", "commit"}
        actual = set(self.step_ids)
        missing = required - actual
        self.assertEqual(missing, set(), f"Missing steps: {missing}")

    def test_step_count(self):
        self.assertGreaterEqual(len(self.steps), 8)


class TestReviewBeforeCommit(unittest.TestCase):
    """INVARIANT: pipeline has no path that bypasses review to reach commit."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_pipeline()
        cls.steps = get_steps(cls.pipeline)
        cls.step_ids = get_step_ids(cls.steps)

    def test_review_precedes_commit(self):
        """Review step must appear before commit step in pipeline order."""
        review_idx = self.step_ids.index("review")
        commit_idx = self.step_ids.index("commit")
        self.assertLess(review_idx, commit_idx,
                        "review must come before commit in pipeline order")

    def test_review_precedes_pre_commit(self):
        """Review step must appear before pre_commit step."""
        review_idx = self.step_ids.index("review")
        pre_commit_idx = self.step_ids.index("pre_commit")
        self.assertLess(review_idx, pre_commit_idx,
                        "review must come before pre_commit in pipeline order")

    def test_implement_precedes_review(self):
        """Implement step must appear before review step."""
        impl_idx = self.step_ids.index("implement")
        review_idx = self.step_ids.index("review")
        self.assertLess(impl_idx, review_idx,
                        "implement must come before review in pipeline order")

    def test_commit_has_review_condition(self):
        """Commit step must have a condition gating on review approval."""
        commit_step = get_step_by_id(self.steps, "commit")
        condition = commit_step.get("condition", "")
        self.assertIn("review", condition,
                      "commit step must have condition referencing review")

    def test_pre_commit_has_review_condition(self):
        """Pre-commit step must have a condition gating on review approval."""
        pre_commit_step = get_step_by_id(self.steps, "pre_commit")
        condition = pre_commit_step.get("condition", "")
        self.assertIn("review", condition,
                      "pre_commit step must have condition referencing review")


class TestVerifyBeforeCommit(unittest.TestCase):
    """INVARIANT: verify not passed must not enter pre_commit/commit."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_pipeline()
        cls.steps = get_steps(cls.pipeline)
        cls.step_ids = get_step_ids(cls.steps)

    def test_verify_precedes_pre_commit(self):
        """Verify step must appear before pre_commit step."""
        verify_idx = self.step_ids.index("verify")
        pre_commit_idx = self.step_ids.index("pre_commit")
        self.assertLess(verify_idx, pre_commit_idx,
                        "verify must come before pre_commit in pipeline order")

    def test_verify_precedes_commit(self):
        """Verify step must appear before commit step."""
        verify_idx = self.step_ids.index("verify")
        commit_idx = self.step_ids.index("commit")
        self.assertLess(verify_idx, commit_idx,
                        "verify must come before commit in pipeline order")

    def test_verify_has_review_condition(self):
        """Verify step runs only after review approval."""
        verify_step = get_step_by_id(self.steps, "verify")
        condition = verify_step.get("condition", "")
        self.assertIn("review", condition,
                      "verify must have condition gating on review approval")

    def test_pre_commit_reads_verify_checkpoint(self):
        """Pre-commit guard must reference verify checkpoint in its command."""
        pre_commit_step = get_step_by_id(self.steps, "pre_commit")
        command = pre_commit_step.get("command", "")
        self.assertIn("pre_commit", command,
                      "pre_commit guard must run --check pre_commit which reads verify checkpoint")


class TestApprovalGate(unittest.TestCase):
    """INVARIANT: approval: required must be present at review step."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_pipeline()
        cls.steps = get_steps(cls.pipeline)

    def test_review_has_approval_required(self):
        """Review step must have approval: required."""
        review_step = get_step_by_id(self.steps, "review")
        self.assertEqual(review_step.get("approval"), "required",
                         "review step must have 'approval: required' to pause for human approval")

    def test_no_other_step_has_approval(self):
        """Only review should have approval gate (not commit or others)."""
        for step in self.steps:
            if step["id"] != "review":
                self.assertNotIn("approval", step,
                                 f"Step '{step['id']}' should not have an approval gate; "
                                 f"only 'review' should require approval")


class TestGuardIntegration(unittest.TestCase):
    """Verify that guard.py is called at the right pipeline steps."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_pipeline()
        cls.steps = get_steps(cls.pipeline)

    def test_triage_step_runs_guard(self):
        step = get_step_by_id(self.steps, "triage")
        self.assertIn("guard.py", step.get("command", "").replace("${GUARD}", "guard.py"))

    def test_route_step_runs_guard(self):
        step = get_step_by_id(self.steps, "route")
        self.assertIn("guard.py", step.get("command", "").replace("${GUARD}", "guard.py"))

    def test_implement_step_runs_guard(self):
        step = get_step_by_id(self.steps, "implement")
        self.assertIn("guard.py", step.get("command", "").replace("${GUARD}", "guard.py"))

    def test_review_step_runs_guard(self):
        step = get_step_by_id(self.steps, "review")
        self.assertIn("guard.py", step.get("command", "").replace("${GUARD}", "guard.py"))

    def test_verify_step_runs_guard(self):
        step = get_step_by_id(self.steps, "verify")
        self.assertIn("guard.py", step.get("command", "").replace("${GUARD}", "guard.py"))

    def test_pre_commit_step_runs_guard(self):
        step = get_step_by_id(self.steps, "pre_commit")
        self.assertIn("guard.py", step.get("command", "").replace("${GUARD}", "guard.py"))

    def test_guard_env_var_defined(self):
        """Pipeline must define GUARD env var pointing to guard.py."""
        env = self.pipeline.get("env", {})
        guard_path = env.get("GUARD", "")
        self.assertIn("guard.py", guard_path,
                      "Pipeline env must define GUARD pointing to guard.py")


class TestDataFlowIntegrity(unittest.TestCase):
    """Verify step data flow — each step reads from the correct predecessor."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_pipeline()
        cls.steps = get_steps(cls.pipeline)

    def test_triage_reads_from_init(self):
        step = get_step_by_id(self.steps, "triage")
        stdin = step.get("stdin", "")
        self.assertIn("init", stdin)

    def test_route_reads_from_triage(self):
        step = get_step_by_id(self.steps, "route")
        stdin = step.get("stdin", "")
        self.assertIn("triage", stdin)

    def test_implement_reads_from_route(self):
        step = get_step_by_id(self.steps, "implement")
        stdin = step.get("stdin", "")
        self.assertIn("route", stdin)

    def test_review_reads_from_implement(self):
        step = get_step_by_id(self.steps, "review")
        stdin = step.get("stdin", "")
        self.assertIn("implement", stdin)

    def test_pre_commit_reads_from_implement(self):
        step = get_step_by_id(self.steps, "pre_commit")
        stdin = step.get("stdin", "")
        self.assertIn("implement", stdin)

    def test_commit_reads_from_pre_commit(self):
        step = get_step_by_id(self.steps, "commit")
        stdin = step.get("stdin", "")
        self.assertIn("pre_commit", stdin)


if __name__ == "__main__":
    unittest.main()
