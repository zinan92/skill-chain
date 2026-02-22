"""Commit changes based on implementation report.

Reads implementation report JSON from stdin.
Uses files_changed and files_created to git add specific files.

Usage: python3 commit.py <repo_path>
"""
import sys
import json
import subprocess
import os


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "repo path required"}))
        sys.exit(1)

    repo = sys.argv[1]
    raw = sys.stdin.read()

    try:
        report = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Failed to parse report: {e}"}))
        sys.exit(1)

    files = []
    if isinstance(report, dict):
        files.extend(report.get("files_changed", []))
        files.extend(report.get("files_created", []))

    if not files:
        print(json.dumps({"committed": False, "reason": "No files to commit"}))
        return

    existing = [f for f in files if os.path.exists(os.path.join(repo, f))]
    if not existing:
        print(json.dumps({"committed": False, "reason": "None of the listed files exist"}))
        return

    add_result = subprocess.run(
        ["git", "add", "--"] + existing,
        cwd=repo,
        capture_output=True,
        text=True
    )
    if add_result.returncode != 0:
        print(json.dumps({"committed": False, "error": f"git add failed: {add_result.stderr}"}))
        sys.exit(1)

    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo,
        capture_output=True,
        text=True
    )
    staged = [f for f in diff_result.stdout.strip().split("\n") if f]
    if not staged:
        print(json.dumps({"committed": False, "reason": "No staged changes after git add"}))
        return

    task_type = report.get("type", "feat")
    summary = report.get("summary", report.get("task", "automated changes"))
    commit_msg = f"{task_type}: {summary}"

    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=repo,
        capture_output=True,
        text=True
    )
    if commit_result.returncode != 0:
        print(json.dumps({"committed": False, "error": f"git commit failed: {commit_result.stderr}"}))
        sys.exit(1)

    print(json.dumps({
        "committed": True,
        "files": staged,
        "message": commit_msg,
        "output": commit_result.stdout.strip()
    }))


if __name__ == "__main__":
    main()
