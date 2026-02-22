"""Unit tests for core/helpers/router.py — Light/Medium/Heavy routing logic.

Tests invariant: Light weight skips planning, Medium/Heavy invokes planning.
Only tests the routing decision logic, not the actual subprocess calls.
"""
import json
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core", "helpers"))

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


class TestRouterLightWeight(unittest.TestCase):
    """INVARIANT: Light weight tasks must skip planning."""

    def test_light_skips_plan(self):
        """Light weight should output plan=None without invoking subprocess."""
        triage = load_fixture("valid_triage_light.json")
        triage_json = json.dumps(triage)

        with patch("sys.stdin", StringIO(triage_json)), \
             patch("sys.argv", ["router.py", "/tmp/fake-repo"]), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout, \
             patch("subprocess.run") as mock_subprocess:

            import importlib
            import router
            importlib.reload(router)
            router.main()

            output = json.loads(mock_stdout.getvalue())
            self.assertIsNone(output["plan"])
            self.assertEqual(output["triage"]["weight"], "Light")
            self.assertIn("Light task", output["context"])
            # subprocess.run should NOT be called for Light tasks
            mock_subprocess.assert_not_called()

    def test_light_preserves_triage_data(self):
        """Light routing should pass through full triage data."""
        triage = load_fixture("valid_triage_light.json")
        triage_json = json.dumps(triage)

        with patch("sys.stdin", StringIO(triage_json)), \
             patch("sys.argv", ["router.py", "/tmp/fake-repo"]), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:

            import importlib
            import router
            importlib.reload(router)
            router.main()

            output = json.loads(mock_stdout.getvalue())
            self.assertEqual(output["triage"]["type"], "fix")
            self.assertEqual(output["triage"]["summary"], "Fix typo in README.md")


class TestRouterMediumWeight(unittest.TestCase):
    """INVARIANT: Medium weight tasks must invoke planning."""

    def test_medium_invokes_planning(self):
        """Medium weight should call subprocess.run for claude planning."""
        triage = load_fixture("valid_triage.json")
        triage_json = json.dumps(triage)

        plan_output = json.dumps({"plan": {"files_to_modify": []}})
        extract_result = MagicMock()
        extract_result.stdout = plan_output
        extract_result.returncode = 0

        claude_result = MagicMock()
        claude_result.stdout = json.dumps({"structured_output": {"plan": {"files_to_modify": []}}})
        claude_result.returncode = 0

        with patch("sys.stdin", StringIO(triage_json)), \
             patch("sys.argv", ["router.py", "/tmp/fake-repo"]), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout, \
             patch("subprocess.run", side_effect=[claude_result, extract_result]) as mock_subprocess:

            import importlib
            import router
            importlib.reload(router)
            router.main()

            # subprocess.run should be called (claude + extract)
            self.assertGreaterEqual(mock_subprocess.call_count, 1)
            # First call should be the claude command
            first_call_args = mock_subprocess.call_args_list[0]
            cmd = first_call_args[0][0]
            self.assertIn("claude", cmd)


class TestRouterHeavyWeight(unittest.TestCase):
    """INVARIANT: Heavy weight tasks must invoke planning."""

    def test_heavy_invokes_planning(self):
        """Heavy weight should call subprocess.run for claude planning."""
        triage = load_fixture("valid_triage_heavy.json")
        triage_json = json.dumps(triage)

        plan_output = json.dumps({"plan": {"files_to_modify": []}})
        extract_result = MagicMock()
        extract_result.stdout = plan_output
        extract_result.returncode = 0

        claude_result = MagicMock()
        claude_result.stdout = json.dumps({"structured_output": {"plan": {"files_to_modify": []}}})
        claude_result.returncode = 0

        with patch("sys.stdin", StringIO(triage_json)), \
             patch("sys.argv", ["router.py", "/tmp/fake-repo"]), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout, \
             patch("subprocess.run", side_effect=[claude_result, extract_result]) as mock_subprocess:

            import importlib
            import router
            importlib.reload(router)
            router.main()

            self.assertGreaterEqual(mock_subprocess.call_count, 1)


class TestRouterEdgeCases(unittest.TestCase):
    """Edge cases and error handling in routing."""

    def test_missing_repo_arg_exits(self):
        """Router should exit 1 when repo path is missing."""
        triage_json = json.dumps(load_fixture("valid_triage.json"))

        with patch("sys.stdin", StringIO(triage_json)), \
             patch("sys.argv", ["router.py"]), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:

            import importlib
            import router
            importlib.reload(router)

            with self.assertRaises(SystemExit) as ctx:
                router.main()
            self.assertEqual(ctx.exception.code, 1)

    def test_invalid_json_exits(self):
        """Router should exit 1 when stdin is not valid JSON."""
        with patch("sys.stdin", StringIO("not json")), \
             patch("sys.argv", ["router.py", "/tmp/fake-repo"]), \
             patch("sys.stdout", new_callable=StringIO):

            import importlib
            import router
            importlib.reload(router)

            with self.assertRaises(SystemExit) as ctx:
                router.main()
            self.assertEqual(ctx.exception.code, 1)

    def test_missing_weight_defaults_to_medium(self):
        """When weight is missing, router should default to Medium (invoke planning)."""
        triage = {"type": "feat", "summary": "A task without explicit weight"}
        triage_json = json.dumps(triage)

        claude_result = MagicMock()
        claude_result.stdout = json.dumps({"structured_output": {"plan": {"files_to_modify": []}}})
        claude_result.returncode = 0

        extract_result = MagicMock()
        extract_result.stdout = json.dumps({"plan": {"files_to_modify": []}})
        extract_result.returncode = 0

        with patch("sys.stdin", StringIO(triage_json)), \
             patch("sys.argv", ["router.py", "/tmp/fake-repo"]), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout, \
             patch("subprocess.run", side_effect=[claude_result, extract_result]) as mock_subprocess:

            import importlib
            import router
            importlib.reload(router)
            router.main()

            # Should invoke planning since default is Medium
            self.assertGreaterEqual(mock_subprocess.call_count, 1)


if __name__ == "__main__":
    unittest.main()
