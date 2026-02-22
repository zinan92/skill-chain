"""Transition guards — deterministic checks between pipeline steps.

Each guard validates the semantic correctness of a step's output.
Schema guarantees format; guards guarantee meaning.

Usage:
  python3 guard.py --check <check_name>
  Reads JSON from stdin, validates, writes to stdout AND $SC_WORKFLOW_DIR/<check_name>.json.
  Exits 0 on pass, 1 on fail (halts pipeline).

Environment:
  SC_WORKFLOW_DIR — checkpoint directory for cross-step validation.
                    Defaults to /tmp/skill-chain-workflow.
                    For concurrent runs, set to a unique value per run
                    (e.g., SC_WORKFLOW_DIR=/tmp/sc-$$ lobster run ...).

Checks:
  triage     — valid type + weight + summary present
  route      — triage present; plan present if weight != Light
  implement  — files_changed non-empty, summary present
  review     — verdict is "approved" (supports legacy and dual-stage formats)
  verify     — verified == true AND evidence non-empty
  pre_commit — aggregate: reads all saved outputs, enforces triple gate
"""
import sys
import json
import os
import argparse

WORKFLOW_DIR = os.environ.get("SC_WORKFLOW_DIR", "/tmp/skill-chain-workflow")


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


def _is_dual_stage_format(data):
    """Detect whether data uses the dual-stage review format."""
    return "spec_review" in data or "quality_review" in data or "overall_verdict" in data


def _check_review_legacy(data):
    """Validate legacy single-stage review: verdict must be 'approved'."""
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

    return data


def _validate_sub_review(name, review):
    """Validate a sub-review (spec_review or quality_review) has valid structure."""
    if not isinstance(review, dict):
        fail(f"{name} must be an object, got {type(review).__name__}.")

    verdict = review.get("verdict")
    if verdict not in ("pass", "fail"):
        fail(f"{name}.verdict must be 'pass' or 'fail', got {verdict!r}.")

    issues = review.get("issues")
    if issues is not None and not isinstance(issues, list):
        fail(f"{name}.issues must be a list if present, got {type(issues).__name__}.")

    return verdict


def _check_review_dual_stage(data):
    """Validate dual-stage review: spec compliance + code quality."""
    spec_review = data.get("spec_review")
    quality_review = data.get("quality_review")
    overall_verdict = data.get("overall_verdict")

    # Validate overall_verdict
    if overall_verdict not in ("approved", "with_fixes", "rejected"):
        fail(
            f"overall_verdict must be 'approved', 'with_fixes', or 'rejected', "
            f"got {overall_verdict!r}.",
            data
        )

    # Validate spec_review (required)
    if not spec_review:
        fail("Dual-stage review missing 'spec_review'.", data)
    spec_verdict = _validate_sub_review("spec_review", spec_review)

    # Validate quality_review (optional — may be skipped if spec fails)
    quality_verdict = None
    if quality_review:
        quality_verdict = _validate_sub_review("quality_review", quality_review)

    # Consistency checks
    if spec_verdict == "fail" and overall_verdict == "approved":
        fail(
            "Contradiction: spec_review.verdict is 'fail' but overall_verdict is 'approved'. "
            "Spec compliance is required for approval.",
            data
        )

    if spec_verdict == "fail" and quality_verdict is not None:
        fail(
            "Stage 1 (spec) failed but Stage 2 (quality) was still run. "
            "Fix spec issues first — skip Stage 2 on spec failure.",
            data
        )

    if quality_verdict == "fail" and overall_verdict == "approved":
        fail(
            "Contradiction: quality_review.verdict is 'fail' but overall_verdict is 'approved'.",
            data
        )

    # Final gate: only 'approved' passes
    if overall_verdict == "rejected":
        spec_issues = spec_review.get("issues", []) if spec_review else []
        quality_issues = quality_review.get("issues", []) if quality_review else []
        all_issues = spec_issues + quality_issues
        critical = [i for i in all_issues if isinstance(i, dict) and i.get("severity") in ("critical", "high")]
        fail(
            f"Review verdict: rejected. {len(critical)} critical/high issues found.",
            {"overall_verdict": overall_verdict, "issues": critical}
        )

    if overall_verdict == "with_fixes":
        spec_issues = spec_review.get("issues", []) if spec_review else []
        quality_issues = quality_review.get("issues", []) if quality_review else []
        all_issues = spec_issues + quality_issues
        fail(
            f"Review verdict: with_fixes. Issues must be resolved before commit.",
            {"overall_verdict": overall_verdict, "issues": all_issues}
        )

    return data


def check_review(data):
    """Validate review verdict. Supports both legacy and dual-stage formats.

    Legacy format:
        {"verdict": "approved|with_fixes|rejected", "issues": [...]}

    Dual-stage format:
        {"spec_review": {"verdict": "pass|fail", "issues": [...]},
         "quality_review": {"verdict": "pass|fail", "issues": [...]},
         "overall_verdict": "approved|with_fixes|rejected"}
    """
    if _is_dual_stage_format(data):
        result = _check_review_dual_stage(data)
    else:
        result = _check_review_legacy(data)

    save_checkpoint("review", data)
    return result


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

    # Gate 1: Review verdict (supports both legacy and dual-stage formats)
    if not review:
        failures.append("No review checkpoint found — review step may have been skipped.")
    elif _is_dual_stage_format(review):
        if review.get("overall_verdict") != "approved":
            failures.append(
                f"Review overall_verdict is {review.get('overall_verdict')!r}, not 'approved'."
            )
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
