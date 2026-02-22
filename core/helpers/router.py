"""Route between Light (skip planning) and Medium/Heavy (run planning via /writing-plans skill).

Reads triage JSON from stdin.
If weight is Light: passes triage output directly to stdout.
If weight is Medium/Heavy: runs claude -p with /writing-plans skill, outputs combined context.

Usage: python3 router.py <repo_path>
"""
import sys
import json
import subprocess
import os

EXTRACT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extract_structured.py")

PLAN_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "plan": {
            "type": "object",
            "properties": {
                "files_to_modify": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "action": {"type": "string", "enum": ["create", "modify", "delete"]},
                            "description": {"type": "string"}
                        },
                        "required": ["path", "action", "description"]
                    }
                },
                "risks": {"type": "array", "items": {"type": "string"}},
                "test_strategy": {"type": "string"}
            },
            "required": ["files_to_modify"]
        }
    },
    "required": ["plan"]
})


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "repo path required as argument"}))
        sys.exit(1)

    repo = sys.argv[1]
    triage_raw = sys.stdin.read()

    try:
        triage = json.loads(triage_raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Failed to parse triage input: {e}"}))
        sys.exit(1)

    weight = triage.get("weight", "Medium")
    task = triage.get("summary", "unknown task")

    if weight == "Light":
        output = {
            "triage": triage,
            "plan": None,
            "context": f"Light task, no plan needed: {task}"
        }
        print(json.dumps(output))
        return

    # Medium/Heavy: run claude for planning
    env = {k: v for k, v in os.environ.items()}
    env.pop("CLAUDECODE", None)

    prompt = (
        "Use the /writing-plans skill. "
        "Read the triage report from stdin and create an implementation plan. "
        "Read the repo to understand existing patterns before planning."
    )

    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", PLAN_SCHEMA,
        "--max-turns", "20",
        "--permission-mode", "bypassPermissions",
        "--add-dir", repo
    ]

    try:
        result = subprocess.run(
            cmd,
            input=triage_raw,
            capture_output=True,
            text=True,
            cwd=repo,
            env=env,
            timeout=300
        )

        if result.returncode != 0:
            print(json.dumps({
                "triage": triage,
                "plan": None,
                "error": f"Planning failed: {result.stderr[:500]}",
                "context": f"Planning failed for {weight} task: {task}"
            }))
            sys.exit(1)

        extract_result = subprocess.run(
            ["python3", EXTRACT_SCRIPT],
            input=result.stdout,
            capture_output=True,
            text=True
        )

        try:
            plan_data = json.loads(extract_result.stdout)
        except json.JSONDecodeError:
            plan_data = {"raw": extract_result.stdout[:1000]}

        output = {
            "triage": triage,
            "plan": plan_data,
            "context": f"{weight} task with plan: {task}"
        }
        print(json.dumps(output))

    except subprocess.TimeoutExpired:
        print(json.dumps({
            "triage": triage,
            "plan": None,
            "error": "Planning timed out after 300s",
            "context": f"Planning timed out for {weight} task: {task}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
