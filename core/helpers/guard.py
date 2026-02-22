"""Transition guards — deterministic checks between pipeline steps.

Each guard validates the semantic correctness of a step's output.
Schema guarantees format; guards guarantee meaning.

Usage:
  python3 guard.py --check <check_name>
  Reads JSON from stdin, validates, writes to stdout AND /tmp/workflow/<check_name>.json.
  Exits 0 on pass, 1 on fail (halts pipeline).

Checks:
  triage     — valid type + weight + summary present
  route      — triage present; plan present if weight != Light
  implement  — files_changed non-empty, summary present
  review     — verdict is "approved" (semantic, not just schema)
  verify     — verified == true AND evidence non-empty
  pre_commit — aggregate: reads all saved outputs, enforces triple gate
"""
import sys
import json
import os
import argparse

WORKFLOW_DIR = "/tmp/workflow"


def save_checkpoint(name, data):
    """Save validated output for cross-step checks."""
    os.makedirs(WORKFLOW_DIR, exist_ok=True)
    path = os.path.join(WORKFLOW_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f)


def load_checkpoint(name):
    """Load a saved checkpoint."""
    path = os.path.join(WORKFLOW_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def fail(reason, data=None):
    """Halt pipeline with structured error."""
    output = {"guard_failed": True, "reason": reason}
    if data:
        output["data"] = data
    print(json.dumps(output), file=sys.stderr)
    sys.exit(1)


def check_triage(data):
    """Validate triage output has required fields with valid values."""
    weight = data.get("weight")
    task_type = data.get("type")
    summary = data.get("summary")

    if not weight or weight not in ("Light", "Medium", "Heavy"):
        fail(f"Invalid weight: {weight!r}. Must be Light/Medium/Heavy.", data)

    if not task_type or not isinstance(task_type, str) or len(task_type) < 2:
        fail(f"Invalid type: {task_type!r}. Must be a non-empty string.", data)

    if not summary or not isinstance(summary, str) or len(summary) < 5:
        fail(f"Invalid summary: {summary!r}. Must be ≥5 chars.", data)

    save_checkpoint("triage", data)
    return data


def check_route(data):
    """Validate route output: triage present, plan present if not Light."""
    triage = data.get("triage")
    if not triage:
        fail("Route output missing 'triage' field.", data)

    weight = triage.get("weight", "Medium")
    plan = data.get("plan")

    if weight != "Light" and not plan:
        # Check if plan failed vs intentionally skipped
        error = data.get("error")
        if error:
            fail(f"Planning required for {weight} task but failed: {error}", data)
        else:
            fail(f"Planning required for {weight} task but plan is null.", data)

    save_checkpoint("route", data)
    return data


def check_implement(data):
    """Validate implementation output: files_changed non-empty."""
    files_changed = data.get("files_changed", [])
    files_created = data.get("files_created", [])
    all_files = files_changed + files_created

    if not all_files:
        fail("Implementation produced no files. files_changed and files_created are both empty.", data)

    summary = data.get("summary", "")
    if not summary:
        fail("Implementation missing summary.", data)

    # Check for error indicators
    if data.get("error"):
        fail(f"Implementation reported error: {data['error']}", data)

    save_checkpoint("implement", data)
    return data


def check_review(data):
    """Validate review verdict is 'approved'. Schema guarantees format; this checks meaning."""
    verdict = data.get("verdict")

    if verdict == "rejected":
        issues = data.get("issues", [])
        critical = [i for i in issues if i.get("severity") in ("critical", "high")]
        fail(
            f"Review verdict: rejected. {len(critical)} critical/high issues found.",
            {"verdict": verdict, "issues": critical, "summary": data.get("summary", "")}
        )

    if verdict == "with_fixes":
        issues = data.get("issues", [])
        fail(
            f"Review verdict: with_fixes. Issues must be resolved before commit.",
            {"verdict": verdict, "issues": issues, "summary": data.get("summary", "")}
        )

    if verdict != "approved":
        fail(f"Review verdict unknown: {verdict!r}. Expected 'approved'.", data)

    save_checkpoint("review", data)
    return data


def check_verify(data):
    """Validate verification: verified == true AND evidence present."""
    verified = data.get("verified")
    evidence = data.get("evidence", "")
    tests_passed = data.get("tests_passed")

    if verified is not True:
        fail(
            f"Verification failed. verified={verified!r}.",
            {"evidence": evidence, "tests_passed": tests_passed}
        )

    if not evidence or len(str(evidence)) < 10:
        fail("Verification missing evidence. No claims without proof.", data)

    if tests_passed is False:
        fail("Tests failed during verification.", data)

    save_checkpoint("verify", data)
    return data


def check_pre_commit(data):
    """Aggregate gate: ALL three conditions must be met before commit.

    1. review.verdict == "approved"
    2. verify.verified == true
    3. Lobster approval gate passed (implicit — this step only runs if approved)

    Reads from saved checkpoints, not from stdin.
    """
    # Load all checkpoints
    review = load_checkpoint("review")
    verify = load_checkpoint("verify")
    implement = load_checkpoint("implement")

    failures = []

    # Gate 1: Review verdict
    if not review:
        failures.append("No review checkpoint found — review step may have been skipped.")
    elif review.get("verdict") != "approved":
        failures.append(f"Review verdict is {review.get('verdict')!r}, not 'approved'.")

    # Gate 2: Verification
    if not verify:
        failures.append("No verify checkpoint found — verification step may have been skipped.")
    elif verify.get("verified") is not True:
        failures.append(f"Verification not passed: verified={verify.get('verified')!r}.")
    elif verify.get("tests_passed") is False:
        failures.append("Tests failed during verification.")

    # Gate 3: Implementation exists
    if not implement:
        failures.append("No implement checkpoint found.")
    elif not (implement.get("files_changed", []) + implement.get("files_created", [])):
        failures.append("No files to commit.")

    if failures:
        fail(
            f"Pre-commit gate: {len(failures)} condition(s) failed.",
            {"failures": failures}
        )

    # Pass through implement data (commit needs file list)
    save_checkpoint("pre_commit", {"passed": True, "gates": 3})
    return implement


CHECKS = {
    "triage": check_triage,
    "route": check_route,
    "implement": check_implement,
    "review": check_review,
    "verify": check_verify,
    "pre_commit": check_pre_commit,
}


def main():
    parser = argparse.ArgumentParser(description="Pipeline transition guard")
    parser.add_argument("--check", required=True, choices=CHECKS.keys(),
                        help="Which guard check to run")
    args = parser.parse_args()

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        fail(f"Guard received invalid JSON from stdin: {e}")
        return  # unreachable, fail() exits

    check_fn = CHECKS[args.check]
    result = check_fn(data)

    # Pass validated data to stdout for next step
    print(json.dumps(result))


if __name__ == "__main__":
    main()
